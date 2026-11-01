#!/usr/bin/env python3
"""Build the WCO DM 4.3.0 package-profile knowledge graph.

The core ontology describes what a WCO DM class / property *is*.  A package
workbook additionally says how a concrete package (MDIP, AIP, BIP DEC,
BIP LPCO) *uses* the core model: which classes/elements are included, their
Min/Max, sequence, usage flags, remarks and external mappings.

Outputs
-------
ontology/wco-dm-4.3.0-profiles.ttl
ontology/wco-dm-4.3.0-profiles-shapes.ttl
ontology/wco-dm-4.3.0-profiles-sample.ttl
ontology/wco-dm-4.3.0-profiles-sample-invalid.ttl
data/profiles.json
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from wco_model import read_xlsx, clean  # noqa: E402

PROF = "https://w3id.org/wco-dm/4.3.0/profile#"
PROF_IRI = "https://w3id.org/wco-dm/4.3.0/profiles"
WCO = "https://w3id.org/wco-dm/4.3.0#"
XSD = "http://www.w3.org/2001/XMLSchema#"

PACKAGES = [
    ("MDIP", "sources/package/3. Information Packages/3.1 Data Model/3.1. WCO DM MDIP_V4.3.0.xlsx"),
    ("AIP", "sources/package/3. Information Packages/3.1 Data Model/3.2. WCO DM AIP_V4.3.0.xlsx"),
    ("BIP DEC", "sources/package/3. Information Packages/3.1 Data Model/3.3. WCO DM BIP DEC_V4.3.0.xlsx"),
    ("BIP LPCO", "sources/package/3. Information Packages/3.1 Data Model/3.4. WCO DM BIP LPCO_V4.3.0.xlsx"),
]

KNOWN = {
    "UML Model Path", "WCO ID", "WCO Name", "WCO Definition", "Remark",
    "WCO Format", "Min", "Max", "WCO Code List", "Seq. No.", "Type",
    "Class", "Attr.", "XML Tag", "JSON Tag",
}


def slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", s or "").strip("_")
    return s or "item"


def pkg_slug(name: str) -> str:
    return slug(name.upper().replace(" ", "_"))


def ttl_lit(s, dtype=None):
    s = str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    if dtype:
        return '"%s"^^%s' % (s, dtype)
    return '"%s"' % s


def header_map(rows):
    for r in sorted(rows):
        if r > 8:
            break
        h = {}
        for c, v in rows[r].items():
            h[re.sub(r"\s+", " ", clean(v)).strip()] = c
        if "Type" in h and "WCO ID" in h and "Min" in h and "Max" in h:
            return r, h
    raise RuntimeError("header not found")


def is_cell(h):
    return h.lower().startswith("cell address")


def is_unique(h):
    return ("unique" in h.lower() and ("pos" in h.lower() or "upi" in h.lower() or "uci" in h.lower())) or h.upper() == "UPI"


def is_imo(h):
    return h in ("IMO ID", "Term", "Compendium name", "Compendium definition")


def is_mydata(h):
    return h.lower().startswith("mydataset") or h.lower().startswith("my dataset")


def is_key(h):
    return h in ("Key",)


def is_flag_header(h):
    low = h.lower()
    blocked = (
        "uci", "upi", "cell", "business rule", "remark", "name", "definition",
        "status", "row no", "reference data", "pfcwg", "wco dmpt", "codes",
        "class", "attr.", "seq", "type", "xml tag", "json tag", "format",
        "imo id", "term", "compendium", "key", "comment",
    )
    return not any(b in low for b in blocked)


def read_package(label, rel):
    wb = read_xlsx(os.path.join(ROOT, rel))
    sheet = list(wb.keys())[0]
    rows = wb[sheet]
    hr, h = header_map(rows)

    def col(name):
        return h.get(name)

    def cell(row, name):
        c = col(name)
        return clean(row.get(c, "")) if c else ""

    # first pass: path -> class id
    path_class = {}
    for r in sorted(rows):
        if r <= hr:
            continue
        if cell(rows[r], "Type") == "C" and cell(rows[r], "WCO ID"):
            path_class[cell(rows[r], "UML Model Path")] = cell(rows[r], "WCO ID")

    flags = {}
    classes = {}
    props = {}
    assocs = {}
    flag_cols = [name for name in h if name not in KNOWN and name and is_flag_header(name)]

    def flag_values(row):
        out = {}
        for name in flag_cols:
            v = clean(row.get(h[name], ""))
            if v:
                out[name] = v
        return out

    for r in sorted(rows):
        if r <= hr:
            continue
        row = rows[r]
        typ = cell(row, "Type")
        wid = cell(row, "WCO ID")
        path = cell(row, "UML Model Path")
        if not wid or typ not in ("C", "E"):
            continue
        fv = flag_values(row)
        base = {
            "package": label,
            "path": path,
            "wco_id": wid,
            "name": cell(row, "WCO Name"),
            "definition": cell(row, "WCO Definition"),
            "remark": cell(row, "Remark"),
            "seq": cell(row, "Seq. No."),
            "min": cell(row, "Min"),
            "max": cell(row, "Max"),
            "flags": fv,
            "imo": {k: cell(row, k) for k in ("IMO ID", "Term", "Compendium name", "Compendium definition") if cell(row, k)},
            "cell": next((clean(row.get(h[k], "")) for k in h if is_cell(k) and clean(row.get(h[k], ""))), ""),
            "unique": next((clean(row.get(h[k], "")) for k in h if is_unique(k) and clean(row.get(h[k], ""))), ""),
            "mydata": {k: cell(row, k) for k in h if is_mydata(k) and cell(row, k)},
        }
        if typ == "C":
            key = wid
            rec = classes.setdefault(key, dict(base, paths=set(), flags=defaultdict(set), remarks=set()))
            rec["paths"].add(path)
            if base["remark"]:
                rec["remarks"].add(base["remark"])
            for k, v in fv.items():
                rec["flags"][k].add(v)
            for k, v in base["imo"].items():
                if v and not rec.get("imo", {}).get(k):
                    rec.setdefault("imo", {})[k] = v
            if not rec.get("min") and base["min"]:
                rec["min"] = base["min"]
            if not rec.get("max") and base["max"]:
                rec["max"] = base["max"]
        else:
            parent_path = path.rsplit("/", 1)[0] if "/" in path else ""
            parent = path_class.get(parent_path)
            if not parent:
                # Property directly under the package root
                parent = path_class.get(path.rsplit("/", 1)[0]) or ""
            if not parent:
                continue
            key = (parent, wid)
            rec = props.setdefault(key, dict(base, class_id=parent, flags=defaultdict(set)))
            for k, v in fv.items():
                rec["flags"][k].add(v)
            if not rec.get("min"):
                rec["min"] = base["min"]
            if not rec.get("max"):
                rec["max"] = base["max"]

        # association from a class row to its parent class
        if typ == "C" and path and "/" in path:
            parent_path, role = path.rsplit("/", 1)
            parent = path_class.get(parent_path)
            if parent:
                key = (parent, role)
                arec = assocs.setdefault(key, {
                    "package": label, "parent": parent, "role": role, "child": wid,
                    "path": path, "min": base["min"], "max": base["max"],
                    "flags": defaultdict(set), "remark": base["remark"],
                })
                for k, v in fv.items():
                    arec["flags"][k].add(v)

    return {
        "label": label,
        "rel": rel,
        "sheet": sheet,
        "rows": len(rows),
        "path_class": path_class,
        "classes": classes,
        "props": props,
        "assocs": assocs,
        "flag_cols": flag_cols,
    }


def build():
    model = json.load(open(os.path.join(ROOT, "data", "model.json"), encoding="utf-8"))
    core_classes = model["classes"]
    core_dps = model["data_properties"]
    core_ops = model["object_properties"]

    pkgs = [read_package(label, rel) for label, rel in PACKAGES]

    # Global flag catalogue
    flag_names = set()
    for p in pkgs:
        for rec in list(p["classes"].values()) + list(p["props"].values()) + list(p["assocs"].values()):
            flag_names.update(rec["flags"].keys())
    flag_local = {name: "F_" + slug(name) for name in sorted(flag_names)}

    # Locals
    for p in pkgs:
        p["slug"] = pkg_slug(p["label"])
        p["pkg_local"] = "PKG_" + p["slug"]
        p["class_local"] = {cid: "P_%s_C_%s" % (p["slug"], slug(cid)) for cid in p["classes"]}
        p["prop_local"] = {}
        for (cid, aid), rec in p["props"].items():
            p["prop_local"][(cid, aid)] = "P_%s_%s_%s" % (p["slug"], slug(cid), slug(aid))
        p["assoc_local"] = {}
        for (parent, role), rec in p["assocs"].items():
            p["assoc_local"][(parent, role)] = "P_%s_A_%s_%s" % (p["slug"], slug(parent), slug(role))

    lines = [
        "# WCO Data Model 4.3.0 package-profile knowledge graph",
        "# Profile layer: how MDIP / AIP / BIP DEC / BIP LPCO use the core model.",
        "",
        "@prefix prof: <%s> ." % PROF,
        "@prefix wco: <%s> ." % WCO,
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <%s> ." % XSD,
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "",
        "<%s> a owl:Ontology ;" % PROF_IRI,
        '  rdfs:label "WCO Data Model 4.3.0 Package Profiles"@en ;',
        '  rdfs:label "WCO 数据模型 4.3.0 包配置剖面本体"@zh ;',
        '  dcterms:description "A profile ontology describing how the MDIP, AIP, BIP DEC and BIP LPCO packages use and constrain the WCO DM 4.3.0 core model: class membership, data elements, associations, Min/Max, sequence, package usage flags, remarks and external mappings."@en ;',
        "  owl:imports <https://w3id.org/wco-dm/4.3.0> ;",
        "  owl:versionInfo \"1.0.0\" ;",
        "  dcterms:source <https://datamodel.wcoomd.org/#/package> ;",
        "  .",
        "",
        "# --- Profile vocabulary ----------------------------------------------------",
        "prof:PackageProfile a owl:Class ;",
        '  rdfs:label "package profile"@en .',
        "prof:ProfileProperty a owl:Class ;",
        '  rdfs:label "profile data element"@en .',
        "prof:ProfileAssociation a owl:Class ;",
        '  rdfs:label "profile association"@en .',
        "prof:Flag a owl:Class ;",
        '  rdfs:label "package usage flag"@en .',
        "",
        "prof:profile a owl:ObjectProperty ;",
        "  rdfs:domain [ a owl:Class ; owl:unionOf ( prof:ProfileProperty prof:ProfileAssociation ) ] ;",
        "  rdfs:range prof:PackageProfile .",
        "prof:inPackage a owl:AnnotationProperty .",
        "prof:sourceClass a owl:AnnotationProperty .",
        "prof:ofClass a owl:AnnotationProperty .",
        "prof:ofProperty a owl:AnnotationProperty .",
        "prof:parentClass a owl:AnnotationProperty .",
        "prof:childClass a owl:AnnotationProperty .",
        "prof:roleName a owl:AnnotationProperty .",
        "prof:minOccurs a owl:AnnotationProperty .",
        "prof:maxOccurs a owl:AnnotationProperty .",
        "prof:sequence a owl:AnnotationProperty .",
        "prof:path a owl:AnnotationProperty .",
        "prof:remark a owl:AnnotationProperty .",
        "prof:hasFlag a owl:AnnotationProperty .",
        "prof:flagName a owl:AnnotationProperty .",
        "prof:sourceColumn a owl:AnnotationProperty .",
        "prof:cellAddress a owl:AnnotationProperty .",
        "prof:uniquePositionID a owl:AnnotationProperty .",
        "prof:imoID a owl:AnnotationProperty .",
        "prof:imoTerm a owl:AnnotationProperty .",
        "prof:imoCompendiumName a owl:AnnotationProperty .",
        "prof:imoCompendiumDefinition a owl:AnnotationProperty .",
        "prof:myDataSetName a owl:AnnotationProperty .",
        "prof:myDataSetDefinition a owl:AnnotationProperty .",
        "prof:myDataSetKey a owl:AnnotationProperty .",
        "prof:packageCode a owl:AnnotationProperty .",
        "prof:sourceWorkbook a owl:AnnotationProperty .",
        "prof:sourceSheet a owl:AnnotationProperty .",
        "prof:profileClassCount a owl:AnnotationProperty .",
        "prof:profileElementCount a owl:AnnotationProperty .",
        "prof:profileAssociationCount a owl:AnnotationProperty .",
        "",
        "# --- Packages --------------------------------------------------------------",
    ]

    for p in pkgs:
        lines.append("%s a prof:PackageProfile ;" % ("prof:" + p["pkg_local"]))
        lines.append("  skos:prefLabel %s ;" % ttl_lit(p["label"]))
        lines.append("  prof:packageCode %s ;" % ttl_lit(p["label"].split()[-1] if p["label"] != "MDIP" else "MDIP"))
        lines.append("  prof:sourceWorkbook %s ;" % ttl_lit(os.path.basename(p["rel"])))
        lines.append("  prof:sourceSheet %s ;" % ttl_lit(p["sheet"]))
        lines.append("  prof:profileClassCount %s ;" % ttl_lit(len(p["classes"]), "xsd:integer"))
        lines.append("  prof:profileElementCount %s ;" % ttl_lit(len(p["props"]), "xsd:integer"))
        lines.append("  prof:profileAssociationCount %s ." % ttl_lit(len(p["assocs"]), "xsd:integer"))
        lines.append("")

    # Flags
    for name in sorted(flag_names):
        local = flag_local[name]
        lines.append("prof:%s a prof:Flag ;" % local)
        lines.append("  skos:prefLabel %s ;" % ttl_lit(name))
        lines.append("  prof:flagName %s ;" % ttl_lit(name))
        lines.append("  prof:sourceColumn %s ." % ttl_lit(name))
        lines.append("")

    # Classes
    lines.append("# --- Profile classes (OWL subclasses of core classes) ---------------------")
    for p in pkgs:
        for cid, rec in sorted(p["classes"].items()):
            if cid not in core_classes:
                continue
            local = p["class_local"][cid]
            lines.append("prof:%s a owl:Class ;" % local)
            lines.append("  rdfs:subClassOf wco:C_%s ;" % slug(cid))
            lines.append("  rdfs:label %s ;" % ttl_lit("%s · %s" % (p["label"], core_classes[cid]["name"])))
            lines.append("  prof:inPackage prof:%s ;" % p["pkg_local"])
            lines.append("  prof:sourceClass wco:C_%s ;" % slug(cid))
            lines.append("  prof:path %s ;" % ttl_lit(sorted(rec.get("paths", []))[0] if rec.get("paths") else rec["path"]))
            if rec.get("seq"):
                lines.append("  prof:sequence %s ;" % ttl_lit(rec["seq"], "xsd:integer") if rec["seq"].isdigit() else "  prof:sequence %s ;" % ttl_lit(rec["seq"]))
            for name in sorted(rec.get("flags", {})):
                lines.append("  prof:hasFlag prof:%s ;" % flag_local[name])
            if rec.get("remark") or rec.get("remarks"):
                lines.append("  prof:remark %s ;" % ttl_lit(rec.get("remark") or sorted(rec["remarks"])[0]))
            for key, prop in (("MyDataSet Name", "myDataSetName"), ("MyDataSet Definition", "myDataSetDefinition"), ("MyDataSet Key", "myDataSetKey")):
                if rec.get("mydata", {}).get(key):
                    lines.append("  prof:%s %s ;" % (prop, ttl_lit(rec["mydata"][key])))
            for k, key in (("imoID", "IMO ID"), ("imoTerm", "Term"), ("imoCompendiumName", "Compendium name"), ("imoCompendiumDefinition", "Compendium definition")):
                if rec.get("imo", {}).get(key):
                    lines.append("  prof:%s %s ;" % (k, ttl_lit(rec["imo"][key])))
            lines[-1] = lines[-1].rstrip(" ;") + " ."
            lines.append("")

    # Properties
    lines.append("# --- Profile data elements -------------------------------------------------")
    for p in pkgs:
        for (cid, aid), rec in sorted(p["props"].items()):
            if cid not in p["class_local"] or aid not in core_dps:
                continue
            local = p["prop_local"][(cid, aid)]
            lines.append("prof:%s a prof:ProfileProperty ;" % local)
            lines.append("  prof:profile prof:%s ;" % p["pkg_local"])
            lines.append("  prof:ofClass prof:%s ;" % p["class_local"][cid])
            lines.append("  prof:ofProperty wco:dp_%s ;" % slug(aid))
            lines.append("  prof:path %s ;" % ttl_lit(rec["path"]))
            if rec.get("min") != "":
                lines.append("  prof:minOccurs %s ;" % ttl_lit(rec["min"], "xsd:integer") if rec["min"].isdigit() else "  prof:minOccurs %s ;" % ttl_lit(rec["min"]))
            if rec.get("max") != "":
                lines.append("  prof:maxOccurs %s ;" % ttl_lit(rec["max"], "xsd:integer") if rec["max"].isdigit() else "  prof:maxOccurs %s ;" % ttl_lit(rec["max"]))
            if rec.get("seq"):
                lines.append("  prof:sequence %s ;" % ttl_lit(rec["seq"], "xsd:integer") if rec["seq"].isdigit() else "  prof:sequence %s ;" % ttl_lit(rec["seq"]))
            for name in sorted(rec.get("flags", {})):
                lines.append("  prof:hasFlag prof:%s ;" % flag_local[name])
            if rec.get("remark"):
                lines.append("  prof:remark %s ;" % ttl_lit(rec["remark"]))
            for key, prop in (("MyDataSet Name", "myDataSetName"), ("MyDataSet Definition", "myDataSetDefinition"), ("MyDataSet Key", "myDataSetKey")):
                if rec.get("mydata", {}).get(key):
                    lines.append("  prof:%s %s ;" % (prop, ttl_lit(rec["mydata"][key])))
            for k, key in (("imoID", "IMO ID"), ("imoTerm", "Term"), ("imoCompendiumName", "Compendium name"), ("imoCompendiumDefinition", "Compendium definition")):
                if rec.get("imo", {}).get(key):
                    lines.append("  prof:%s %s ;" % (k, ttl_lit(rec["imo"][key])))
            for k, key in (("cellAddress", "Cell Address"),):
                if rec.get("cell"):
                    lines.append("  prof:cellAddress %s ;" % ttl_lit(rec["cell"]))
            if rec.get("unique"):
                lines.append("  prof:uniquePositionID %s ;" % ttl_lit(rec["unique"]))
            lines[-1] = lines[-1].rstrip(" ;") + " ."
            lines.append("")

    # Associations
    lines.append("# --- Profile associations (containment roles) ------------------------------")
    for p in pkgs:
        for (parent, role), rec in sorted(p["assocs"].items()):
            if parent not in p["class_local"] or rec["child"] not in p["class_local"]:
                continue
            local = p["assoc_local"][(parent, role)]
            lines.append("prof:%s a prof:ProfileAssociation ;" % local)
            lines.append("  prof:profile prof:%s ;" % p["pkg_local"])
            lines.append("  prof:parentClass prof:%s ;" % p["class_local"][parent])
            lines.append("  prof:childClass prof:%s ;" % p["class_local"][rec["child"]])
            lines.append("  prof:roleName %s ;" % ttl_lit(role))
            op_local = "has" + role[:1].upper() + role[1:]
            if op_local in core_ops:
                lines.append("  prof:ofProperty wco:%s ;" % op_local)
            if rec.get("min") != "":
                lines.append("  prof:minOccurs %s ;" % ttl_lit(rec["min"], "xsd:integer") if rec["min"].isdigit() else "  prof:minOccurs %s ;" % ttl_lit(rec["min"]))
            if rec.get("max") != "":
                lines.append("  prof:maxOccurs %s ;" % ttl_lit(rec["max"], "xsd:integer") if rec["max"].isdigit() else "  prof:maxOccurs %s ;" % ttl_lit(rec["max"]))
            for name in sorted(rec.get("flags", {})):
                lines.append("  prof:hasFlag prof:%s ;" % flag_local[name])
            lines[-1] = lines[-1].rstrip(" ;") + " ."
            lines.append("")

    with open(os.path.join(ROOT, "ontology", "wco-dm-4.3.0-profiles.ttl"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # Shapes
    shapes = [
        "# WCO Data Model 4.3.0 profile SHACL shapes",
        "@prefix prof: <%s> ." % PROF,
        "@prefix wco: <%s> ." % WCO,
        "@prefix sh: <http://www.w3.org/ns/shacl#> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <%s> ." % XSD,
        "",
        "prof:ProfileShapes a owl:Ontology ;",
        '  rdfs:label "WCO DM 4.3.0 profile SHACL shapes"@en .',
        "",
    ]
    for p in pkgs:
        by_class_props = defaultdict(list)
        for (cid, aid), rec in p["props"].items():
            if cid in p["class_local"] and aid in core_dps:
                by_class_props[cid].append(rec)
        by_class_assocs = defaultdict(list)
        for (parent, role), rec in p["assocs"].items():
            if parent in p["class_local"] and rec["child"] in p["class_local"]:
                by_class_assocs[parent].append(rec)
        for cid in sorted(p["classes"]):
            if cid not in p["class_local"]:
                continue
            ps = [r for r in by_class_props.get(cid, []) if r.get("wco_id") in core_dps]
            ass = [r for r in by_class_assocs.get(cid, []) if r["role"] in core_ops]
            if not ps and not ass:
                continue
            shape_local = "Shape_%s" % p["class_local"][cid]
            start_len = len(shapes)
            shapes.append("prof:%s a sh:NodeShape ;" % shape_local)
            shapes.append("  sh:targetClass prof:%s ;" % p["class_local"][cid])
            shapes.append("  sh:name %s ;" % ttl_lit("%s · %s" % (p["label"], core_classes.get(cid, {}).get("name", cid))))
            blocks = []
            for rec in sorted(ps, key=lambda x: (int(x["seq"]) if x.get("seq", "").isdigit() else 9999, x["wco_id"])):
                aid = rec["wco_id"]
                dp = core_dps.get(aid)
                if not dp:
                    continue
                b = ["  sh:property [", "    a sh:PropertyShape ;"]
                b.append("    sh:path wco:dp_%s ;" % slug(aid))
                b.append("    sh:datatype %s ;" % dp["datatype"])
                if rec.get("max", "").isdigit():
                    b.append("    sh:maxCount %s ;" % rec["max"])
                if rec.get("min", "").isdigit() and int(rec["min"]) > 0:
                    b.append("    sh:minCount %s ;" % rec["min"])
                b.append("  ] ;")
                blocks.append("\n".join(b))
            for rec in sorted(ass, key=lambda x: x["role"].lower()):
                op_local = "has" + rec["role"][:1].upper() + rec["role"][1:]
                if rec["role"] not in core_ops:
                    continue
                b = ["  sh:property [", "    a sh:PropertyShape ;"]
                b.append("    sh:path wco:%s ;" % op_local)
                b.append("    sh:class prof:%s ;" % p["class_local"][rec["child"]])
                b.append("    sh:nodeKind sh:IRI ;")
                if rec.get("max", "").isdigit():
                    b.append("    sh:maxCount %s ;" % rec["max"])
                b.append("  ] ;")
                blocks.append("\n".join(b))
            if not blocks:
                continue
            shapes.append("\n".join(blocks))
            shapes[-1] = shapes[-1].rstrip(" ;") + " ."
            shapes.append("")

    with open(os.path.join(ROOT, "ontology", "wco-dm-4.3.0-profiles-shapes.ttl"), "w", encoding="utf-8") as f:
        f.write("\n".join(shapes) + "\n")

    # Simple sample using BIP DEC / Declaration
    sample = """# Conforming BIP DEC profile instance
@prefix prof: <https://w3id.org/wco-dm/4.3.0/profile#> .
@prefix wco: <https://w3id.org/wco-dm/4.3.0#> .
@prefix ex: <http://example.org/> .

ex:declaration a prof:P_BIP_DEC_C_42A ;
  wco:dp_D014 "DOC-001" .
"""
    sample_bad = """# Invalid BIP DEC profile instance: dp_D014 occurs twice (Max=1).
@prefix prof: <https://w3id.org/wco-dm/4.3.0/profile#> .
@prefix wco: <https://w3id.org/wco-dm/4.3.0#> .
@prefix ex: <http://example.org/> .

ex:declaration a prof:P_BIP_DEC_C_42A ;
  wco:dp_D014 "DOC-001" ;
  wco:dp_D014 "DOC-002" .
"""
    with open(os.path.join(ROOT, "ontology", "wco-dm-4.3.0-profiles-sample.ttl"), "w", encoding="utf-8") as f:
        f.write(sample)
    with open(os.path.join(ROOT, "ontology", "wco-dm-4.3.0-profiles-sample-invalid.ttl"), "w", encoding="utf-8") as f:
        f.write(sample_bad)

    # Export for the visualisation
    payload = {"packages": [], "flags": [{"name": n, "local": flag_local[n]} for n in sorted(flag_names)]}
    for p in pkgs:
        items = []
        for (cid, aid), rec in sorted(p["props"].items()):
            if cid not in p["class_local"] or aid not in core_dps:
                continue
            items.append({
                "class": cid,
                "className": core_classes.get(cid, {}).get("name", cid),
                "property": aid,
                "propertyName": core_dps.get(aid, {}).get("name", aid),
                "min": rec.get("min", ""),
                "max": rec.get("max", ""),
                "seq": rec.get("seq", ""),
                "flags": sorted(rec.get("flags", {}).keys()),
                "remark": rec.get("remark", ""),
                "path": rec.get("path", ""),
            })
        payload["packages"].append({
            "name": p["label"],
            "slug": p["slug"],
            "classes": len(p["classes"]),
            "elements": len(items),
            "associations": len(p["assocs"]),
            "items": items,
        })
    with open(os.path.join(ROOT, "data", "profiles.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print("profiles: packages=%d classes=%d elements=%d associations=%d flags=%d" % (
        len(pkgs), sum(len(p["classes"]) for p in pkgs), sum(len(p["props"]) for p in pkgs),
        sum(len(p["assocs"]) for p in pkgs), len(flag_names)))


if __name__ == "__main__":
    build()
