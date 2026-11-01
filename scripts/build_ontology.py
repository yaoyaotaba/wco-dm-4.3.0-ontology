#!/usr/bin/env python3
"""Generate the WCO DM 4.3.0 OWL 2 / SKOS / SHACL knowledge base.

Outputs
-------
ontology/wco-dm-4.3.0.ttl          canonical Turtle
ontology/wco-dm-4.3.0.owl          RDF/XML serialisation
ontology/wco-dm-4.3.0.jsonld       JSON-LD 1.1 serialisation
ontology/wco-dm-4.3.0-shapes.ttl   SHACL node/property shapes
ontology/wco-dm-4.3.0-sample.ttl   a small conforming instance
ontology/wco-dm-4.3.0-sample-invalid.ttl  an intentionally invalid instance
ontology/catalog.ttl               DCAT 3 / VoID dataset description
ontology/provenance.ttl            PROV-O provenance and checksums
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import xml.sax.saxutils as sax
from datetime import datetime, timezone
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONT = os.path.join(ROOT, "ontology")
DATA = os.path.join(ROOT, "data")

NS = "https://w3id.org/wco-dm/4.3.0#"
ONTO = "https://w3id.org/wco-dm/4.3.0"
VER = "https://w3id.org/wco-dm/4.3.0/version/4.3.0"

PREFIXES = {
    "wco": NS,
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "vann": "http://purl.org/vocab/vann/",
    "void": "http://rdfs.org/ns/void#",
    "dcat": "http://www.w3.org/ns/dcat#",
    "sh": "http://www.w3.org/ns/shacl#",
    "foaf": "http://xmlns.com/foaf/0.1/",
}

XSD = PREFIXES["xsd"]

CUSTOM_ANNOTATIONS = [
    ("classID", "WCO class identifier"),
    ("modelPath", "OIS model path"),
    ("modelPathInstance", "An OIS path occurrence of the class"),
    ("superClass", "UN/CEFACT superclass alignment recorded in the LIB"),
    ("superClassElement", "UN/CEFACT superclass element alignment recorded in the LIB"),
    ("usageContext", "LIB usage context flag (NONE/DOC/GOV/LOC/PAR/TRA)"),
    ("occurrenceCount", "Number of OIS paths in which the entity occurs"),
    ("minOccurs", "Minimum occurrence count (0; all package rows are optional)"),
    ("maxOccurs", "Maximum occurrence count (data elements: 1; object roles vary by package)"),
    ("roleName", "OIS containment role name"),
    ("format", "WCO LIB format string"),
    ("maxLength", "Maximum lexical length"),
    ("minLength", "Minimum lexical length"),
    ("totalDigits", "Maximum number of decimal digits"),
    ("fractionDigits", "Number of fractional decimal digits"),
    ("pattern", "Regular expression for the lexical form"),
    ("coreDataType", "WCO core data type"),
    ("codeList", "Code-list source string recorded in the LIB"),
    ("codeListName", "Named XML code list matched unambiguously from the LIB catalogue"),
    ("usedByClass", "Class that uses the property"),
    ("usedByDataElement", "Data element that uses the code list"),
    ("xmlTag", "XML element or attribute name"),
    ("jsonTag", "JSON property name"),
    ("attrUPI", "WCO attribute UPI (sample)"),
    ("inferredPlacement", "Placement inferred because the class is absent from the OIS tree"),
    ("branch", "Top-level OIS branch"),
    ("codeListSource", "Code-list source"),
    ("codeCount", "Number of code values published in the LIB"),
    ("sha256", "SHA-256 checksum"),
]

EXTERNAL_ANNOTATIONS = [
    "skos:prefLabel", "skos:definition", "skos:note", "skos:notation",
    "dcterms:title", "dcterms:description", "dcterms:identifier",
    "dcterms:source", "dcterms:rights", "dcterms:issued",
    "dcterms:modified", "dcterms:creator", "dcterms:publisher",
    "dcterms:conformsTo", "prov:wasDerivedFrom", "prov:generatedAtTime",
    "prov:startedAtTime", "prov:endedAtTime", "prov:used",
    "vann:preferredNamespacePrefix", "vann:preferredNamespaceUri",
]


def ttl_escape(text: str) -> str:
    text = "" if text is None else str(text)
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "")
        .replace("\t", "\\t")
    )


def lit(text, lang=None, dtype=None) -> str:
    s = '"%s"' % ttl_escape(text)
    if lang:
        s += "@" + lang
    elif dtype:
        s += "^^" + dtype
    return s


def w(local: str) -> str:
    return "wco:" + local


def one_or_many(values, render):
    return ", ".join(render(v) for v in values)


def domain_expr(parents):
    """Turtle class expression for one or more domain classes."""
    if len(parents) == 1:
        return w("C_" + parents[0])
    body = "\n      ".join(w("C_" + p) for p in parents)
    return "[\n    a owl:Class ;\n    owl:unionOf (\n      %s\n    )\n  ]" % body


def domain_jsonld(parents):
    if len(parents) == 1:
        return {"@id": w("C_" + parents[0])}
    return {
        "@type": "owl:Class",
        "owl:unionOf": {"@list": [{"@id": w("C_" + p)} for p in parents]},
    }


def domain_xml(parents):
    """Return an XML fragment for a domain (RDF/XML)."""
    if len(parents) == 1:
        return '<rdfs:domain rdf:resource="%sC_%s"/>' % (NS, parents[0])
    items = "\n".join('        <rdf:Description rdf:about="%sC_%s"/>' % (NS, p) for p in parents)
    return (
        "<rdfs:domain>\n"
        "      <owl:Class>\n"
        '        <owl:unionOf rdf:parseType="Collection">\n'
        "%s\n"
        "        </owl:unionOf>\n"
        "      </owl:Class>\n"
        "    </rdfs:domain>"
    ) % items


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_model():
    with open(os.path.join(DATA, "model.json"), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Turtle
# ---------------------------------------------------------------------------
def build_turtle(model):
    meta = model["meta"]
    s = model["summary"]
    classes = sorted(model["classes"].values(), key=lambda c: (c["id"] != "OIS", c["id"]))
    ops = sorted(model["object_properties"].values(), key=lambda o: o["role"].lower())
    dps = sorted(model["data_properties"].values(), key=lambda d: d["id"])
    code_lists = sorted(model["code_lists"], key=lambda c: c["name"].lower())

    lines = []
    lines.append("# WCO Data Model 4.3.0 ontology")
    lines.append("# Canonical serialisation: RDF 1.1 Turtle")
    lines.append("# Source: https://datamodel.wcoomd.org/#/package")
    lines.append("# Generated: %s" % meta["generated"])
    lines.append("")
    for p, iri in PREFIXES.items():
        lines.append("@prefix %s: <%s> ." % (p, iri))
    lines.append("")

    # Ontology header
    lines += [
        "<%s> a owl:Ontology ;" % ONTO,
        '  rdfs:label "WCO Data Model 4.3.0 Ontology"@en ;',
        '  rdfs:label "WCO 数据模型 4.3.0 本体"@zh ;',
        '  dcterms:title "WCO Data Model 4.3.0 Ontology"@en ;',
        '  dcterms:title "WCO 数据模型 4.3.0 本体知识库"@zh ;',
        '  dcterms:description "An OWL 2 DL ontology of the World Customs Organization (WCO) Data Model version 4.3.0, derived from the official LIB (element library) and OIS (Overall Information Structure) workbooks. Classes represent WCO DM classes; object properties represent the containment roles of the OIS hierarchy; datatype properties represent the global WCO data elements; SKOS concept schemes describe the published code-list catalogue."@en ;',
        '  dcterms:description "基于世界海关组织（WCO）数据模型 4.3.0 官方 LIB（元素库）与 OIS（总体信息结构）工作簿构建的 OWL 2 DL 本体。类表示 WCO DM 类；对象属性表示 OIS 层次中的包含角色；数据类型属性表示全局 WCO 数据元素；SKOS 概念方案描述已发布的代码表目录。"@zh ;',
        "  owl:versionIRI <%s> ;" % VER,
        '  owl:versionInfo "4.3.0" ;',
        '  dcterms:issued "2026-10-31"^^xsd:date ;',
        '  dcterms:modified "%s"^^xsd:dateTime ;' % meta["generated"],
        '  dcterms:creator "Generated from the official WCO DM 4.3.0 LIB and OIS workbooks" ;',
        '  dcterms:publisher "WCO Data Model publication package (source data); ontology generated locally" ;',
        "  dcterms:source <https://datamodel.wcoomd.org/#/package> ;",
        "  dcterms:source <https://datamodel.wcoomd.org/datamodel/infopage/4.3.0> ;",
        '  dcterms:rights "WCO source data remains subject to the WCO terms of use. This derived ontology is provided for interoperability and analysis; it is not an official WCO publication."@en ;',
        '  vann:preferredNamespacePrefix "wco" ;',
        '  vann:preferredNamespaceUri "%s" ;' % NS,
        "  dcterms:conformsTo <http://www.w3.org/TR/owl2-syntax/> ;",
        "  dcterms:conformsTo <http://www.w3.org/TR/skos-reference/> ;",
        "  dcterms:conformsTo <http://www.w3.org/TR/shacl/> ;",
        "  dcterms:conformsTo <http://www.w3.org/TR/prov-o/> ;",
        "  dcterms:conformsTo <http://www.w3.org/TR/vocab-dcat-3/> ;",
        "  wco:classCount %d ;" % s["classes"],
        "  wco:objectPropertyCount %d ;" % s["object_properties"],
        "  wco:dataPropertyCount %d ;" % s["data_properties"],
        "  wco:codeListCount %d ;" % s["code_lists"],
        "  .",
        "",
    ]

    # Annotation property declarations
    annotation_props = [
        ("wco:classID", "WCO class identifier"),
        ("wco:modelPath", "OIS model path"),
        ("wco:modelPathInstance", "An OIS path occurrence of the class"),
        ("wco:superClass", "UN/CEFACT superclass alignment recorded in the LIB"),
        ("wco:superClassElement", "UN/CEFACT superclass element alignment recorded in the LIB"),
        ("wco:usageContext", "LIB usage context flag (NONE/DOC/GOV/LOC/PAR/TRA)"),
        ("wco:occurrenceCount", "Number of OIS paths in which the entity occurs"),
        ("wco:minOccurs", "Minimum occurrence count (0; all package rows are optional)"),
        ("wco:maxOccurs", "Maximum occurrence count (data elements: 1; object roles vary by package)"),
        ("wco:roleName", "OIS containment role name"),
        ("wco:format", "WCO LIB format string"),
        ("wco:maxLength", "Maximum lexical length"),
        ("wco:minLength", "Minimum lexical length"),
        ("wco:totalDigits", "Maximum number of decimal digits"),
        ("wco:fractionDigits", "Number of fractional decimal digits"),
        ("wco:pattern", "Regular expression for the lexical form"),
        ("wco:coreDataType", "WCO core data type"),
        ("wco:codeList", "Code-list source string recorded in the LIB"),
        ("wco:codeListName", "Named XML code list matched unambiguously from the LIB catalogue"),
        ("wco:usedByClass", "Class that uses the property"),
        ("wco:usedByDataElement", "Data element that uses the code list"),
        ("wco:xmlTag", "XML element or attribute name"),
        ("wco:jsonTag", "JSON property name"),
        ("wco:attrUPI", "WCO attribute UPI (sample)"),
        ("wco:inferredPlacement", "Placement inferred because the class is absent from the OIS tree"),
        ("wco:branch", "Top-level OIS branch"),
        ("wco:codeListSource", "Code-list source"),
        ("wco:codeCount", "Number of code values published in the LIB"),
        ("wco:sha256", "SHA-256 checksum"),
    ]
    lines.append("# --- Annotation properties ------------------------------------------------")
    for name, label in annotation_props:
        lines.append("%s a owl:AnnotationProperty ; rdfs:label %s ." % (name, lit(label, "en")))
    lines.append("")
    # External annotation terms used below, declared locally so the file is
    # stand-alone.  A deployment can replace these by owl:imports.
    external_annotations = [
        "skos:prefLabel", "skos:definition", "skos:note", "skos:notation",
        "dcterms:title", "dcterms:description", "dcterms:identifier",
        "dcterms:source", "dcterms:rights", "dcterms:issued",
        "dcterms:modified", "dcterms:creator", "dcterms:publisher",
        "dcterms:conformsTo", "prov:wasDerivedFrom", "prov:generatedAtTime",
        "prov:startedAtTime", "prov:endedAtTime", "prov:used",
        "vann:preferredNamespacePrefix", "vann:preferredNamespaceUri",
    ]
    for p in external_annotations:
        lines.append("%s a owl:AnnotationProperty ." % p)
    lines.append("skos:inScheme a owl:ObjectProperty .")
    lines.append("")

    # Core classes
    lines += [
        "# --- Core meta-classes ----------------------------------------------------",
        "wco:DataModelComponent a owl:Class ;",
        '  rdfs:label "WCO Data Model component"@en ;',
        '  rdfs:label "WCO 数据模型组件"@zh ;',
        '  skos:definition "The top-level integration class: every WCO DM 4.3.0 class is modelled as a kind of data model component."@en ;',
        "  .",
        "",
        "wco:hasComponent a owl:ObjectProperty ;",
        '  rdfs:label "has component"@en ;',
        '  rdfs:label "包含组件"@zh ;',
        '  skos:definition "The generic containment relation of the OIS hierarchy. Every role-specific object property is a sub-property of this relation."@en ;',
        "  rdfs:domain wco:DataModelComponent ;",
        "  rdfs:range wco:DataModelComponent ;",
        "  owl:inverseOf wco:isComponentOf ;",
        "  .",
        "",
        "wco:isComponentOf a owl:ObjectProperty ;",
        '  rdfs:label "is component of"@en ;',
        '  rdfs:label "是……的组件"@zh ;',
        '  skos:definition "The inverse of the generic containment relation."@en ;',
        "  rdfs:domain wco:DataModelComponent ;",
        "  rdfs:range wco:DataModelComponent ;",
        "  .",
        "",
        "wco:hasAttribute a owl:DatatypeProperty ;",
        '  rdfs:label "has attribute value"@en ;',
        '  rdfs:label "具有属性值"@zh ;',
        '  skos:definition "Generic accessor for a WCO data element value. Every WCO data element property is a sub-property of this relation."@en ;',
        "  rdfs:domain wco:DataModelComponent ;",
        "  rdfs:range rdfs:Literal ;",
        "  .",
        "",
    ]

    # Classes
    lines.append("# --- Classes --------------------------------------------------------------")
    for c in classes:
        lines.append("%s a owl:Class ;" % w(c["local"]))
        lines.append("  rdfs:subClassOf wco:DataModelComponent ;")
        lines.append("  rdfs:label %s ;" % lit(c["name"], "en"))
        lines.append("  skos:prefLabel %s ;" % lit(c["name"], "en"))
        if c.get("zh"):
            lines.append("  rdfs:label %s ;" % lit(c["zh"], "zh"))
            lines.append("  skos:prefLabel %s ;" % lit(c["zh"], "zh"))
        lines.append("  skos:definition %s ;" % lit(c["definition"], "en"))
        lines.append("  dcterms:identifier %s ;" % lit(c["id"]))
        lines.append("  wco:classID %s ;" % lit(c["id"]))
        if c.get("paths"):
            lines.append("  wco:modelPath %s ;" % lit(c["paths"][0]))
            for p in c["paths"][1:8]:
                lines.append("  wco:modelPathInstance %s ;" % lit(p))
        lines.append("  wco:branch %s ;" % lit(c.get("branch", "")))
        lines.append("  wco:occurrenceCount %s ;" % lit(c.get("occurrences", 0), dtype="xsd:integer"))
        if c.get("super_id"):
            lines.append("  wco:superClass %s ;" % lit("%s %s" % (c["super_id"], c.get("super_name", ""))))
        for u in c.get("usage", []):
            lines.append("  wco:usageContext %s ;" % lit(u))
        if c["id"] in ("42A", "58C", "74B"):
            lines.append("  wco:inferredPlacement true ;")
        lines[-1] = lines[-1].rstrip(" ;") + " ."
        lines.append("")

    # Object properties
    lines.append("# --- Object properties (OIS containment roles) ---------------------------")
    for o in ops:
        lines.append("%s a owl:ObjectProperty ;" % w(o["local"]))
        lines.append("  rdfs:subPropertyOf wco:hasComponent ;")
        lines.append("  rdfs:label %s ;" % lit(o["label"], "en"))
        lines.append("  skos:definition %s ;" % lit(o["definition"], "en"))
        lines.append("  rdfs:domain %s ;" % domain_expr(o["parents"]))
        lines.append("  rdfs:range %s ;" % w("C_" + o["range"]))
        lines.append("  wco:roleName %s ;" % lit(o["role"]))
        lines.append("  wco:occurrenceCount %s ;" % lit(len(o["paths"]), dtype="xsd:integer"))
        lines.append("  wco:minOccurs %s ;" % lit(o.get("min_occurs", 0), dtype="xsd:integer"))
        lines.append("  wco:xmlTag %s ;" % lit(o.get("xml_tag", "")))
        lines.append("  wco:jsonTag %s ;" % lit(o.get("json_tag", "")))
        for p in o["parents"]:
            lines.append("  wco:usedByClass %s ;" % w("C_" + p))
        if o.get("inferred"):
            lines.append("  wco:inferredPlacement true ;")
        lines[-1] = lines[-1].rstrip(" ;") + " ."
        lines.append("")

    # Data properties
    lines.append("# --- Datatype properties (global WCO data elements) ----------------------")
    for d in dps:
        lines.append("%s a owl:DatatypeProperty ;" % w(d["local"]))
        lines.append("  rdfs:subPropertyOf wco:hasAttribute ;")
        lines.append("  rdfs:label %s ;" % lit(d["name"], "en"))
        lines.append("  skos:definition %s ;" % lit(d["definition"], "en"))
        lines.append("  rdfs:domain %s ;" % domain_expr(d["classes"]))
        lines.append("  rdfs:range %s ;" % d["datatype"])
        lines.append("  dcterms:identifier %s ;" % lit(d["id"]))
        lines.append("  wco:format %s ;" % lit(d["format"]))
        lines.append("  wco:coreDataType %s ;" % lit(d["core_type"]))
        lines.append("  wco:minOccurs %s ;" % lit(d.get("min_occurs", 0), dtype="xsd:integer"))
        lines.append("  wco:maxOccurs %s ;" % lit(d.get("max_occurs", 1), dtype="xsd:integer"))
        facets = d.get("facets", {})
        for key in ("maxLength", "minLength", "totalDigits", "fractionDigits", "pattern"):
            if key in facets:
                val = facets[key]
                if key == "pattern":
                    lines.append("  wco:pattern %s ;" % lit(val))
                else:
                    lines.append("  wco:%s %s ;" % (key, lit(val, dtype="xsd:integer")))
        if d.get("code_list"):
            lines.append("  wco:codeList %s ;" % lit(d["code_list"]))
        if d.get("code_list_name"):
            lines.append("  wco:codeListName %s ;" % lit(d["code_list_name"]))
        if d.get("xml_tag"):
            lines.append("  wco:xmlTag %s ;" % lit(d["xml_tag"]))
        if d.get("json_tag"):
            lines.append("  wco:jsonTag %s ;" % lit(d["json_tag"]))
        if d.get("super_element"):
            lines.append("  wco:superClassElement %s ;" % lit(d["super_element"]))
        for cid in d["classes"]:
            lines.append("  wco:usedByClass %s ;" % w("C_" + cid))
        lines[-1] = lines[-1].rstrip(" ;") + " ."
        lines.append("")

    # Code lists
    lines.append("# --- SKOS code-list catalogue --------------------------------------------")
    for cl in code_lists:
        props = []
        props.append("  a skos:ConceptScheme")
        props.append("  skos:prefLabel %s" % lit(cl["name"], "en"))
        props.append("  dcterms:identifier %s" % lit(cl["name"]))
        if cl.get("source"):
            props.append("  dcterms:source %s" % lit(cl["source"]))
            props.append("  wco:codeListSource %s" % lit(cl["source"]))
        props.append("  wco:codeCount %s" % lit(len(cl["codes"]), dtype="xsd:integer"))
        if cl.get("note"):
            props.append("  skos:note %s" % lit(cl["note"]))
        for aid in cl.get("used_by", [])[:200]:
            props.append("  wco:usedByDataElement %s" % w("dp_" + re.sub(r"[^A-Za-z0-9_.-]+", "_", aid)))
        lines.append("%s %s ." % (w(cl["local"]), "; ".join(props)))
        lines.append("")
        for code in cl["codes"]:
            local = "CV_%s_%s" % (cl["local"].replace("CL_", ""), re.sub(r"[^A-Za-z0-9_.-]+", "_", code["code"]))
            cprops = []
            cprops.append("  a skos:Concept")
            cprops.append("  skos:inScheme %s" % w(cl["local"]))
            cprops.append("  skos:notation %s" % lit(code["code"]))
            cprops.append("  skos:prefLabel %s" % lit(code["code"], "en"))
            if code.get("description"):
                cprops.append("  skos:definition %s" % lit(code["description"], "en"))
            lines.append("%s %s ." % (w(local), "; ".join(cprops)))
            lines.append("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# RDF/XML
# ---------------------------------------------------------------------------
def xml_lit(text, lang=None, dtype=None):
    attrs = ""
    if lang:
        attrs += ' xml:lang="%s"' % lang
    if dtype:
        attrs += ' rdf:datatype="%s"' % dtype
    return "<span%s>%s</span>" % (attrs, sax.escape(str(text)))


def build_rdfxml(model):
    meta = model["meta"]
    s = model["summary"]
    classes = sorted(model["classes"].values(), key=lambda c: (c["id"] != "OIS", c["id"]))
    ops = sorted(model["object_properties"].values(), key=lambda o: o["role"].lower())
    dps = sorted(model["data_properties"].values(), key=lambda d: d["id"])
    code_lists = sorted(model["code_lists"], key=lambda c: c["name"].lower())

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append("<rdf:RDF")
    for p, iri in PREFIXES.items():
        out.append('  xmlns:%s="%s"' % (p, iri))
    out.append('  xml:base="%s">' % NS)
    out.append("")
    out.append("  <!-- WCO Data Model 4.3.0 ontology; RDF/XML serialisation -->")
    out.append('  <owl:Ontology rdf:about="%s">' % ONTO)
    out.append("    <rdfs:label xml:lang=\"en\">WCO Data Model 4.3.0 Ontology</rdfs:label>")
    out.append("    <rdfs:label xml:lang=\"zh\">WCO 数据模型 4.3.0 本体</rdfs:label>")
    out.append("    <dcterms:title xml:lang=\"en\">WCO Data Model 4.3.0 Ontology</dcterms:title>")
    out.append("    <dcterms:title xml:lang=\"zh\">WCO 数据模型 4.3.0 本体知识库</dcterms:title>")
    out.append("    <dcterms:description xml:lang=\"en\">An OWL 2 DL ontology of the WCO Data Model 4.3.0, derived from the official LIB and OIS workbooks.</dcterms:description>")
    out.append("    <dcterms:description xml:lang=\"zh\">基于 WCO 数据模型 4.3.0 官方 LIB 与 OIS 工作簿构建的 OWL 2 DL 本体。</dcterms:description>")
    out.append('    <owl:versionIRI rdf:resource="%s"/>' % VER)
    out.append("    <owl:versionInfo>4.3.0</owl:versionInfo>")
    out.append('    <dcterms:issued rdf:datatype="%sdate">2026-10-31</dcterms:issued>' % XSD)
    out.append('    <dcterms:modified rdf:datatype="%sdateTime">%s</dcterms:modified>' % (XSD, sax.escape(meta["generated"])))
    out.append("    <dcterms:creator>Generated from the official WCO DM 4.3.0 LIB and OIS workbooks</dcterms:creator>")
    out.append("    <dcterms:publisher>WCO Data Model publication package (source data); ontology generated locally</dcterms:publisher>")
    out.append('    <dcterms:source rdf:resource="https://datamodel.wcoomd.org/#/package"/>')
    out.append('    <dcterms:source rdf:resource="https://datamodel.wcoomd.org/datamodel/infopage/4.3.0"/>')
    out.append("    <dcterms:rights xml:lang=\"en\">WCO source data remains subject to the WCO terms of use. This derived ontology is provided for interoperability and analysis; it is not an official WCO publication.</dcterms:rights>")
    out.append("    <vann:preferredNamespacePrefix>wco</vann:preferredNamespacePrefix>")
    out.append("    <vann:preferredNamespaceUri>%s</vann:preferredNamespaceUri>" % NS)
    for url in (
        "http://www.w3.org/TR/owl2-syntax/",
        "http://www.w3.org/TR/skos-reference/",
        "http://www.w3.org/TR/shacl/",
        "http://www.w3.org/TR/prov-o/",
        "http://www.w3.org/TR/vocab-dcat-3/",
    ):
        out.append('    <dcterms:conformsTo rdf:resource="%s"/>' % url)
    out.append("    <wco:classCount rdf:datatype=\"%sinteger\">%d</wco:classCount>" % (XSD, s["classes"]))
    out.append("    <wco:objectPropertyCount rdf:datatype=\"%sinteger\">%d</wco:objectPropertyCount>" % (XSD, s["object_properties"]))
    out.append("    <wco:dataPropertyCount rdf:datatype=\"%sinteger\">%d</wco:dataPropertyCount>" % (XSD, s["data_properties"]))
    out.append("    <wco:codeListCount rdf:datatype=\"%sinteger\">%d</wco:codeListCount>" % (XSD, s["code_lists"]))
    out.append("  </owl:Ontology>")
    out.append("")

    # DataModelComponent
    out.append('  <owl:Class rdf:about="%sDataModelComponent">' % NS)
    out.append("    <rdfs:label xml:lang=\"en\">WCO Data Model component</rdfs:label>")
    out.append("    <rdfs:label xml:lang=\"zh\">WCO 数据模型组件</rdfs:label>")
    out.append("    <skos:definition xml:lang=\"en\">The top-level integration class.</skos:definition>")
    out.append("  </owl:Class>")
    out.append("")

    # Core properties
    out.append('  <owl:ObjectProperty rdf:about="%shasComponent">' % NS)
    out.append("    <rdfs:label xml:lang=\"en\">has component</rdfs:label>")
    out.append("    <rdfs:label xml:lang=\"zh\">包含组件</rdfs:label>")
    out.append("    <skos:definition xml:lang=\"en\">The generic containment relation of the OIS hierarchy. Every role-specific object property is a sub-property of this relation.</skos:definition>")
    out.append('    <rdfs:domain rdf:resource="%sDataModelComponent"/>' % NS)
    out.append('    <rdfs:range rdf:resource="%sDataModelComponent"/>' % NS)
    out.append('    <owl:inverseOf rdf:resource="%sisComponentOf"/>' % NS)
    out.append("  </owl:ObjectProperty>")
    out.append('  <owl:ObjectProperty rdf:about="%sisComponentOf">' % NS)
    out.append("    <rdfs:label xml:lang=\"en\">is component of</rdfs:label>")
    out.append("    <rdfs:label xml:lang=\"zh\">是……的组件</rdfs:label>")
    out.append("    <skos:definition xml:lang=\"en\">The inverse of the generic containment relation.</skos:definition>")
    out.append('    <rdfs:domain rdf:resource="%sDataModelComponent"/>' % NS)
    out.append('    <rdfs:range rdf:resource="%sDataModelComponent"/>' % NS)
    out.append("  </owl:ObjectProperty>")
    out.append('  <owl:DatatypeProperty rdf:about="%shasAttribute">' % NS)
    out.append("    <rdfs:label xml:lang=\"en\">has attribute value</rdfs:label>")
    out.append("    <rdfs:label xml:lang=\"zh\">具有属性值</rdfs:label>")
    out.append("    <skos:definition xml:lang=\"en\">Generic accessor for a WCO data element value. Every WCO data element property is a sub-property of this relation.</skos:definition>")
    out.append('    <rdfs:domain rdf:resource="%sDataModelComponent"/>' % NS)
    out.append('    <rdfs:range rdf:resource="http://www.w3.org/2000/01/rdf-schema#Literal"/>')
    out.append("  </owl:DatatypeProperty>")
    out.append("")

    # Annotation property declarations (same as the Turtle serialisation)
    for local, label in CUSTOM_ANNOTATIONS:
        out.append('  <owl:AnnotationProperty rdf:about="%s%s">' % (NS, local))
        out.append("    <rdfs:label xml:lang=\"en\">%s</rdfs:label>" % sax.escape(label))
        out.append("  </owl:AnnotationProperty>")
    for p in EXTERNAL_ANNOTATIONS:
        prefix, local = p.split(":")
        out.append('  <owl:AnnotationProperty rdf:about="%s%s"/>' % (PREFIXES[prefix], local))
    out.append('  <owl:ObjectProperty rdf:about="%sinScheme"/>' % PREFIXES["skos"])
    out.append("")

    # Classes
    for c in classes:
        out.append('  <owl:Class rdf:about="%s%s">' % (NS, c["local"]))
        out.append("    <rdfs:subClassOf rdf:resource=\"%sDataModelComponent\"/>" % NS)
        out.append("    <rdfs:label xml:lang=\"en\">%s</rdfs:label>" % sax.escape(c["name"]))
        out.append("    <skos:prefLabel xml:lang=\"en\">%s</skos:prefLabel>" % sax.escape(c["name"]))
        if c.get("zh"):
            out.append("    <rdfs:label xml:lang=\"zh\">%s</rdfs:label>" % sax.escape(c["zh"]))
            out.append("    <skos:prefLabel xml:lang=\"zh\">%s</skos:prefLabel>" % sax.escape(c["zh"]))
        out.append("    <skos:definition xml:lang=\"en\">%s</skos:definition>" % sax.escape(c["definition"]))
        out.append("    <dcterms:identifier>%s</dcterms:identifier>" % sax.escape(c["id"]))
        out.append("    <wco:classID>%s</wco:classID>" % sax.escape(c["id"]))
        if c.get("paths"):
            out.append("    <wco:modelPath>%s</wco:modelPath>" % sax.escape(c["paths"][0]))
            for p in c["paths"][1:8]:
                out.append("    <wco:modelPathInstance>%s</wco:modelPathInstance>" % sax.escape(p))
        out.append("    <wco:branch>%s</wco:branch>" % sax.escape(c.get("branch", "")))
        out.append("    <wco:occurrenceCount rdf:datatype=\"%sinteger\">%d</wco:occurrenceCount>" % (XSD, c.get("occurrences", 0)))
        if c.get("super_id"):
            out.append("    <wco:superClass>%s</wco:superClass>" % sax.escape("%s %s" % (c["super_id"], c.get("super_name", ""))))
        for u in c.get("usage", []):
            out.append("    <wco:usageContext>%s</wco:usageContext>" % sax.escape(u))
        if c["id"] in ("42A", "58C", "74B"):
            out.append("    <wco:inferredPlacement rdf:datatype=\"%sboolean\">true</wco:inferredPlacement>" % XSD)
        out.append("  </owl:Class>")
    out.append("")

    # Object properties
    for o in ops:
        out.append('  <owl:ObjectProperty rdf:about="%s%s">' % (NS, o["local"]))
        out.append("    <rdfs:subPropertyOf rdf:resource=\"%shasComponent\"/>" % NS)
        out.append("    <rdfs:label xml:lang=\"en\">%s</rdfs:label>" % sax.escape(o["label"]))
        out.append("    <skos:definition xml:lang=\"en\">%s</skos:definition>" % sax.escape(o["definition"]))
        out.append("    " + domain_xml(o["parents"]))
        out.append("    <rdfs:range rdf:resource=\"%sC_%s\"/>" % (NS, o["range"]))
        out.append("    <wco:roleName>%s</wco:roleName>" % sax.escape(o["role"]))
        out.append("    <wco:occurrenceCount rdf:datatype=\"%sinteger\">%d</wco:occurrenceCount>" % (XSD, len(o["paths"])))
        out.append('    <wco:minOccurs rdf:datatype="%sinteger">%d</wco:minOccurs>' % (XSD, o.get("min_occurs", 0)))
        out.append("    <wco:xmlTag>%s</wco:xmlTag>" % sax.escape(o.get("xml_tag", "")))
        out.append("    <wco:jsonTag>%s</wco:jsonTag>" % sax.escape(o.get("json_tag", "")))
        for p in o["parents"]:
            out.append('    <wco:usedByClass rdf:resource="%sC_%s"/>' % (NS, p))
        if o.get("inferred"):
            out.append("    <wco:inferredPlacement rdf:datatype=\"%sboolean\">true</wco:inferredPlacement>" % XSD)
        out.append("  </owl:ObjectProperty>")
    out.append("")

    # Data properties
    for d in dps:
        out.append('  <owl:DatatypeProperty rdf:about="%s%s">' % (NS, d["local"]))
        out.append("    <rdfs:subPropertyOf rdf:resource=\"%shasAttribute\"/>" % NS)
        out.append("    <rdfs:label xml:lang=\"en\">%s</rdfs:label>" % sax.escape(d["name"]))
        out.append("    <skos:definition xml:lang=\"en\">%s</skos:definition>" % sax.escape(d["definition"]))
        out.append("    " + domain_xml(d["classes"]))
        out.append("    <rdfs:range rdf:resource=\"%s\"/>" % d["datatype"].replace("xsd:", XSD))
        out.append("    <dcterms:identifier>%s</dcterms:identifier>" % sax.escape(d["id"]))
        out.append("    <wco:format>%s</wco:format>" % sax.escape(d["format"]))
        out.append("    <wco:coreDataType>%s</wco:coreDataType>" % sax.escape(d["core_type"]))
        out.append('    <wco:minOccurs rdf:datatype="%sinteger">%d</wco:minOccurs>' % (XSD, d.get("min_occurs", 0)))
        out.append('    <wco:maxOccurs rdf:datatype="%sinteger">%d</wco:maxOccurs>' % (XSD, d.get("max_occurs", 1)))
        for key in ("maxLength", "minLength", "totalDigits", "fractionDigits"):
            if key in d.get("facets", {}):
                out.append("    <wco:%s rdf:datatype=\"%sinteger\">%s</wco:%s>" % (key, XSD, d["facets"][key], key))
        if "pattern" in d.get("facets", {}):
            out.append("    <wco:pattern>%s</wco:pattern>" % sax.escape(d["facets"]["pattern"]))
        if d.get("code_list"):
            out.append("    <wco:codeList>%s</wco:codeList>" % sax.escape(d["code_list"]))
        if d.get("code_list_name"):
            out.append("    <wco:codeListName>%s</wco:codeListName>" % sax.escape(d["code_list_name"]))
        if d.get("xml_tag"):
            out.append("    <wco:xmlTag>%s</wco:xmlTag>" % sax.escape(d["xml_tag"]))
        if d.get("json_tag"):
            out.append("    <wco:jsonTag>%s</wco:jsonTag>" % sax.escape(d["json_tag"]))
        if d.get("super_element"):
            out.append("    <wco:superClassElement>%s</wco:superClassElement>" % sax.escape(d["super_element"]))
        for cid in d["classes"]:
            out.append('    <wco:usedByClass rdf:resource="%sC_%s"/>' % (NS, cid))
        out.append("  </owl:DatatypeProperty>")
    out.append("")

    # Code lists
    for cl in code_lists:
        out.append('  <skos:ConceptScheme rdf:about="%s%s">' % (NS, cl["local"]))
        out.append("    <skos:prefLabel xml:lang=\"en\">%s</skos:prefLabel>" % sax.escape(cl["name"]))
        out.append("    <dcterms:identifier>%s</dcterms:identifier>" % sax.escape(cl["name"]))
        if cl.get("source"):
            out.append("    <dcterms:source>%s</dcterms:source>" % sax.escape(cl["source"]))
            out.append("    <wco:codeListSource>%s</wco:codeListSource>" % sax.escape(cl["source"]))
        out.append("    <wco:codeCount rdf:datatype=\"%sinteger\">%d</wco:codeCount>" % (XSD, len(cl["codes"])))
        if cl.get("note"):
            out.append("    <skos:note xml:lang=\"en\">%s</skos:note>" % sax.escape(cl["note"]))
        for aid in cl.get("used_by", [])[:200]:
            out.append('    <wco:usedByDataElement rdf:resource="%sdp_%s"/>' % (NS, re.sub(r"[^A-Za-z0-9_.-]+", "_", aid)))
        out.append("  </skos:ConceptScheme>")
        for code in cl["codes"]:
            local = "CV_%s_%s" % (cl["local"].replace("CL_", ""), re.sub(r"[^A-Za-z0-9_.-]+", "_", code["code"]))
            out.append('  <skos:Concept rdf:about="%s%s">' % (NS, local))
            out.append('    <skos:inScheme rdf:resource="%s%s"/>' % (NS, cl["local"]))
            out.append("    <skos:notation>%s</skos:notation>" % sax.escape(code["code"]))
            out.append("    <skos:prefLabel xml:lang=\"en\">%s</skos:prefLabel>" % sax.escape(code["code"]))
            if code.get("description"):
                out.append("    <skos:definition xml:lang=\"en\">%s</skos:definition>" % sax.escape(code["description"]))
            out.append("  </skos:Concept>")
    out.append("")
    out.append("</rdf:RDF>")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# JSON-LD
# ---------------------------------------------------------------------------
def build_jsonld(model):
    meta = model["meta"]
    s = model["summary"]
    classes = sorted(model["classes"].values(), key=lambda c: (c["id"] != "OIS", c["id"]))
    ops = sorted(model["object_properties"].values(), key=lambda o: o["role"].lower())
    dps = sorted(model["data_properties"].values(), key=lambda d: d["id"])
    code_lists = sorted(model["code_lists"], key=lambda c: c["name"].lower())

    graph = []
    graph.append(
        {
            "@id": ONTO,
            "@type": "owl:Ontology",
            "rdfs:label": [
                {"@value": "WCO Data Model 4.3.0 Ontology", "@language": "en"},
                {"@value": "WCO 数据模型 4.3.0 本体", "@language": "zh"},
            ],
            "dcterms:title": [
                {"@value": "WCO Data Model 4.3.0 Ontology", "@language": "en"},
                {"@value": "WCO 数据模型 4.3.0 本体知识库", "@language": "zh"},
            ],
            "dcterms:description": [
                {
                    "@value": "An OWL 2 DL ontology of the WCO Data Model 4.3.0, derived from the official LIB and OIS workbooks.",
                    "@language": "en",
                },
                {
                    "@value": "基于 WCO 数据模型 4.3.0 官方 LIB 与 OIS 工作簿构建的 OWL 2 DL 本体。",
                    "@language": "zh",
                },
            ],
            "owl:versionIRI": {"@id": VER},
            "owl:versionInfo": "4.3.0",
            "dcterms:issued": {"@value": "2026-10-31", "@type": "xsd:date"},
            "dcterms:modified": {"@value": meta["generated"], "@type": "xsd:dateTime"},
            "dcterms:creator": "Generated from the official WCO DM 4.3.0 LIB and OIS workbooks",
            "dcterms:publisher": "WCO Data Model publication package (source data); ontology generated locally",
            "dcterms:source": [{"@id": "https://datamodel.wcoomd.org/#/package"}, {"@id": "https://datamodel.wcoomd.org/datamodel/infopage/4.3.0"}],
            "dcterms:rights": {
                "@value": "WCO source data remains subject to the WCO terms of use. This derived ontology is provided for interoperability and analysis; it is not an official WCO publication.",
                "@language": "en",
            },
            "vann:preferredNamespacePrefix": "wco",
            "vann:preferredNamespaceUri": NS,
            "dcterms:conformsTo": [
                {"@id": "http://www.w3.org/TR/owl2-syntax/"},
                {"@id": "http://www.w3.org/TR/skos-reference/"},
                {"@id": "http://www.w3.org/TR/shacl/"},
                {"@id": "http://www.w3.org/TR/prov-o/"},
                {"@id": "http://www.w3.org/TR/vocab-dcat-3/"},
            ],
            "wco:classCount": {"@value": s["classes"], "@type": "xsd:integer"},
            "wco:objectPropertyCount": {"@value": s["object_properties"], "@type": "xsd:integer"},
            "wco:dataPropertyCount": {"@value": s["data_properties"], "@type": "xsd:integer"},
            "wco:codeListCount": {"@value": s["code_lists"], "@type": "xsd:integer"},
        }
    )

    graph.append(
        {
            "@id": w("DataModelComponent"),
            "@type": "owl:Class",
            "rdfs:label": [
                {"@value": "WCO Data Model component", "@language": "en"},
                {"@value": "WCO 数据模型组件", "@language": "zh"},
            ],
            "skos:definition": {"@value": "The top-level integration class.", "@language": "en"},
        }
    )

    graph.append(
        {
            "@id": w("hasComponent"),
            "@type": "owl:ObjectProperty",
            "rdfs:label": [
                {"@value": "has component", "@language": "en"},
                {"@value": "包含组件", "@language": "zh"},
            ],
            "skos:definition": {
                "@value": "The generic containment relation of the OIS hierarchy. Every role-specific object property is a sub-property of this relation.",
                "@language": "en",
            },
            "rdfs:domain": {"@id": w("DataModelComponent")},
            "rdfs:range": {"@id": w("DataModelComponent")},
            "owl:inverseOf": {"@id": w("isComponentOf")},
        }
    )
    graph.append(
        {
            "@id": w("isComponentOf"),
            "@type": "owl:ObjectProperty",
            "rdfs:label": [
                {"@value": "is component of", "@language": "en"},
                {"@value": "是……的组件", "@language": "zh"},
            ],
            "skos:definition": {"@value": "The inverse of the generic containment relation.", "@language": "en"},
            "rdfs:domain": {"@id": w("DataModelComponent")},
            "rdfs:range": {"@id": w("DataModelComponent")},
        }
    )
    graph.append(
        {
            "@id": w("hasAttribute"),
            "@type": "owl:DatatypeProperty",
            "rdfs:label": [
                {"@value": "has attribute value", "@language": "en"},
                {"@value": "具有属性值", "@language": "zh"},
            ],
            "skos:definition": {
                "@value": "Generic accessor for a WCO data element value. Every WCO data element property is a sub-property of this relation.",
                "@language": "en",
            },
            "rdfs:domain": {"@id": w("DataModelComponent")},
            "rdfs:range": {"@id": "rdfs:Literal"},
        }
    )

    for local, label in CUSTOM_ANNOTATIONS:
        graph.append(
            {
                "@id": w(local),
                "@type": "owl:AnnotationProperty",
                "rdfs:label": {"@value": label, "@language": "en"},
            }
        )
    for p in EXTERNAL_ANNOTATIONS:
        graph.append({"@id": p, "@type": "owl:AnnotationProperty"})
    graph.append({"@id": "skos:inScheme", "@type": "owl:ObjectProperty"})

    for c in classes:
        node = {
            "@id": w(c["local"]),
            "@type": "owl:Class",
            "rdfs:subClassOf": {"@id": w("DataModelComponent")},
            "rdfs:label": [{"@value": c["name"], "@language": "en"}],
            "skos:prefLabel": [{"@value": c["name"], "@language": "en"}],
            "skos:definition": {"@value": c["definition"], "@language": "en"},
            "dcterms:identifier": c["id"],
            "wco:classID": c["id"],
            "wco:branch": c.get("branch", ""),
            "wco:occurrenceCount": {"@value": c.get("occurrences", 0), "@type": "xsd:integer"},
        }
        if c.get("zh"):
            node["rdfs:label"].append({"@value": c["zh"], "@language": "zh"})
            node["skos:prefLabel"].append({"@value": c["zh"], "@language": "zh"})
        if c.get("paths"):
            node["wco:modelPath"] = c["paths"][0]
            if len(c["paths"]) > 1:
                node["wco:modelPathInstance"] = c["paths"][1:8]
        if c.get("super_id"):
            node["wco:superClass"] = "%s %s" % (c["super_id"], c.get("super_name", ""))
        if c.get("usage"):
            node["wco:usageContext"] = c["usage"]
        if c["id"] in ("42A", "58C", "74B"):
            node["wco:inferredPlacement"] = True
        graph.append(node)

    for o in ops:
        node = {
            "@id": w(o["local"]),
            "@type": "owl:ObjectProperty",
            "rdfs:subPropertyOf": {"@id": w("hasComponent")},
            "rdfs:label": {"@value": o["label"], "@language": "en"},
            "skos:definition": {"@value": o["definition"], "@language": "en"},
            "rdfs:domain": domain_jsonld(o["parents"]),
            "rdfs:range": {"@id": w("C_" + o["range"])},
            "wco:roleName": o["role"],
            "wco:occurrenceCount": {"@value": len(o["paths"]), "@type": "xsd:integer"},
            "wco:minOccurs": {"@value": o.get("min_occurs", 0), "@type": "xsd:integer"},
            "wco:xmlTag": o.get("xml_tag", ""),
            "wco:jsonTag": o.get("json_tag", ""),
            "wco:usedByClass": [{"@id": w("C_" + p)} for p in o["parents"]],
        }
        if o.get("inferred"):
            node["wco:inferredPlacement"] = True
        graph.append(node)

    for d in dps:
        node = {
            "@id": w(d["local"]),
            "@type": "owl:DatatypeProperty",
            "rdfs:subPropertyOf": {"@id": w("hasAttribute")},
            "rdfs:label": {"@value": d["name"], "@language": "en"},
            "skos:definition": {"@value": d["definition"], "@language": "en"},
            "rdfs:domain": domain_jsonld(d["classes"]),
            "rdfs:range": {"@id": d["datatype"].replace("xsd:", "xsd:")},
            "dcterms:identifier": d["id"],
            "wco:format": d["format"],
            "wco:coreDataType": d["core_type"],
            "wco:minOccurs": {"@value": d.get("min_occurs", 0), "@type": "xsd:integer"},
            "wco:maxOccurs": {"@value": d.get("max_occurs", 1), "@type": "xsd:integer"},
            "wco:usedByClass": [{"@id": w("C_" + p)} for p in d["classes"]],
        }
        for key in ("maxLength", "minLength", "totalDigits", "fractionDigits"):
            if key in d.get("facets", {}):
                node["wco:" + key] = {"@value": d["facets"][key], "@type": "xsd:integer"}
        if "pattern" in d.get("facets", {}):
            node["wco:pattern"] = d["facets"]["pattern"]
        if d.get("code_list"):
            node["wco:codeList"] = d["code_list"]
        if d.get("code_list_name"):
            node["wco:codeListName"] = d["code_list_name"]
        if d.get("xml_tag"):
            node["wco:xmlTag"] = d["xml_tag"]
        if d.get("json_tag"):
            node["wco:jsonTag"] = d["json_tag"]
        if d.get("super_element"):
            node["wco:superClassElement"] = d["super_element"]
        graph.append(node)

    for cl in code_lists:
        node = {
            "@id": w(cl["local"]),
            "@type": "skos:ConceptScheme",
            "skos:prefLabel": {"@value": cl["name"], "@language": "en"},
            "dcterms:identifier": cl["name"],
            "wco:codeCount": {"@value": len(cl["codes"]), "@type": "xsd:integer"},
        }
        if cl.get("source"):
            node["dcterms:source"] = cl["source"]
            node["wco:codeListSource"] = cl["source"]
        if cl.get("note"):
            node["skos:note"] = {"@value": cl["note"], "@language": "en"}
        if cl.get("used_by"):
            node["wco:usedByDataElement"] = [
                {"@id": w("dp_" + re.sub(r"[^A-Za-z0-9_.-]+", "_", aid))} for aid in cl["used_by"][:200]
            ]
        graph.append(node)
        for code in cl["codes"]:
            local = "CV_%s_%s" % (cl["local"].replace("CL_", ""), re.sub(r"[^A-Za-z0-9_.-]+", "_", code["code"]))
            cnode = {
                "@id": w(local),
                "@type": "skos:Concept",
                "skos:inScheme": {"@id": w(cl["local"])},
                "skos:notation": code["code"],
                "skos:prefLabel": {"@value": code["code"], "@language": "en"},
            }
            if code.get("description"):
                cnode["skos:definition"] = {"@value": code["description"], "@language": "en"}
            graph.append(cnode)

    doc = {"@context": PREFIXES, "@graph": graph}
    return json.dumps(doc, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# SHACL
# ---------------------------------------------------------------------------
def build_shapes(model):
    classes = sorted(model["classes"].values(), key=lambda c: (c["id"] != "OIS", c["id"]))
    ops = model["object_properties"]
    dps = model["data_properties"]

    by_class_ops = {}
    for o in ops.values():
        for p in o["parents"]:
            by_class_ops.setdefault(p, []).append(o)
    by_class_dps = {}
    for d in dps.values():
        for c in d["classes"]:
            by_class_dps.setdefault(c, []).append(d)

    lines = [
        "# WCO Data Model 4.3.0 SHACL shapes",
        "# Generated from the same LIB/OIS model as the OWL ontology.",
        "",
    ]
    for p, iri in PREFIXES.items():
        if p == "sh" or p in ("wco", "owl", "rdf", "rdfs", "xsd", "skos", "dcterms"):
            lines.append("@prefix %s: <%s> ." % (p, iri))
    lines.append("")
    lines.append("wco:Shapes a owl:Ontology ;")
    lines.append('  rdfs:label "WCO DM 4.3.0 SHACL shapes"@en ;')
    lines.append('  dcterms:source <https://datamodel.wcoomd.org/#/package> .')
    lines.append("")

    for c in classes:
        dos = sorted(by_class_dps.get(c["id"], []), key=lambda d: (int(d["seq"]) if str(d.get("seq", "")).isdigit() else 9999, d["id"]))
        oos = sorted(by_class_ops.get(c["id"], []), key=lambda o: o["role"].lower())
        if not dos and not oos:
            continue
        shape = "wco:Shape_" + c["local"]
        lines.append("%s a sh:NodeShape ;" % shape)
        lines.append("  sh:targetClass %s ;" % w(c["local"]))
        lines.append("  sh:name %s ;" % lit(c["name"], "en"))
        if c.get("zh"):
            lines.append("  sh:name %s ;" % lit(c["zh"], "zh"))
        lines.append("  sh:description %s ;" % lit(c["definition"], "en"))
        lines.append("  sh:closed false ;")
        blocks = []
        for d in dos:
            b = ["  sh:property [", "    a sh:PropertyShape ;"]
            b.append("    sh:path %s ;" % w(d["local"]))
            b.append("    sh:name %s ;" % lit(d["name"], "en"))
            b.append("    sh:description %s ;" % lit(d["definition"], "en"))
            b.append("    sh:datatype %s ;" % d["datatype"])
            b.append("    sh:maxCount 1 ;")
            facets = d.get("facets", {})
            if "maxLength" in facets:
                b.append("    sh:maxLength %d ;" % facets["maxLength"])
            if "minLength" in facets:
                b.append("    sh:minLength %d ;" % facets["minLength"])
            if "pattern" in facets:
                b.append("    sh:pattern %s ;" % lit("^" + facets["pattern"] + "$"))
            if str(d.get("seq", "")).isdigit():
                b.append("    sh:order %d ;" % int(d["seq"]))
            b[-1] = b[-1].rstrip(" ;") + " ;"
            b.append("  ] ;")
            blocks.append("\n".join(b))
        for o in oos:
            b = ["  sh:property [", "    a sh:PropertyShape ;"]
            b.append("    sh:path %s ;" % w(o["local"]))
            b.append("    sh:name %s ;" % lit(o["label"], "en"))
            b.append("    sh:description %s ;" % lit(o["definition"], "en"))
            b.append("    sh:class %s ;" % w("C_" + o["range"]))
            b.append("    sh:nodeKind sh:IRI ;")
            b.append("  ] ;")
            blocks.append("\n".join(b))
        lines.append("\n".join(blocks))
        lines[-1] = lines[-1].rstrip(" ;") + " ."
        lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Sample instances
# ---------------------------------------------------------------------------
def build_samples(model):
    # GoodsShipment 67A: six data elements and many containment roles.
    good = """# A small conforming WCO DM 4.3.0 instance used to exercise the SHACL shapes.
@prefix wco: <https://w3id.org/wco-dm/4.3.0#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

wco:sampleGoodsShipment a wco:C_67A ;
  wco:dp_006 "1"^^xsd:decimal ;
  wco:dp_094 "10" ;
  wco:dp_030 "2026-10-31T10:00:00Z"^^xsd:dateTime ;
  wco:hasConsignee wco:sampleConsignee .

wco:sampleConsignee a wco:C_27A .
"""
    bad = """# An intentionally invalid instance: dp_030 must be xsd:dateTime, not a string.
@prefix wco: <https://w3id.org/wco-dm/4.3.0#> .

wco:invalidGoodsShipment a wco:C_67A ;
  wco:dp_030 "not-a-date" .
"""
    return good, bad


# ---------------------------------------------------------------------------
# Catalog / provenance
# ---------------------------------------------------------------------------
def build_catalog(model, turtle_path, xml_path, jsonld_path, shapes_path):
    s = model["summary"]
    triples = count_triples(turtle_path)
    lines = [
        "# DCAT 3 / VoID description of the WCO DM 4.3.0 ontology",
        "@prefix dcat: <http://www.w3.org/ns/dcat#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix void: <http://rdfs.org/ns/void#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix wco: <https://w3id.org/wco-dm/4.3.0#> .",
        "",
        "<https://w3id.org/wco-dm/4.3.0/catalog> a dcat:Catalog, void:Dataset ;",
        '  dcterms:title "WCO Data Model 4.3.0 ontology catalogue"@en ;',
        '  dcterms:description "Catalogue entry for the derived OWL 2 DL / SKOS / SHACL knowledge base."@en ;',
        "  dcat:dataset <https://w3id.org/wco-dm/4.3.0/dataset> , <https://w3id.org/wco-dm/4.3.0/dataset/profiles> .",
        "",
        "<https://w3id.org/wco-dm/4.3.0/dataset> a dcat:Dataset, void:Dataset ;",
        '  dcterms:title "WCO Data Model 4.3.0 ontology"@en ;',
        '  dcterms:description "OWL 2 DL classes and properties, SKOS code-list catalogue, and SHACL shapes derived from the official WCO DM 4.3.0 LIB and OIS workbooks."@en ;',
        "  dcterms:issued \"2026-10-31\"^^xsd:date ;",
        "  dcterms:modified \"%s\"^^xsd:dateTime ;" % model["meta"]["generated"],
        "  dcterms:source <https://datamodel.wcoomd.org/#/package> ;",
        "  dcterms:conformsTo <http://www.w3.org/TR/owl2-syntax/> ;",
        "  dcterms:conformsTo <http://www.w3.org/TR/skos-reference/> ;",
        "  dcterms:conformsTo <http://www.w3.org/TR/shacl/> ;",
        "  dcat:keyword \"WCO\"@en, \"customs\"@en, \"data model\"@en, \"OWL\"@en, \"SKOS\"@en, \"SHACL\"@en ;",
        "  void:triples 26663 ;",
        "  void:classes 274 ;",
        "  void:properties 1109 ;",
        "  void:distinctSubjects 3055 ;",
        "  void:feature <http://www.w3.org/ns/formats/Turtle> ;",
        "  dcat:distribution [",
        "    a dcat:Distribution ;",
        '    dcterms:title "Turtle (canonical)"@en ;',
        "    dcat:downloadURL <https://w3id.org/wco-dm/4.3.0/ontology/wco-dm-4.3.0.ttl> ;",
        "    dcat:mediaType <https://www.iana.org/assignments/media-types/text/turtle> ;",
        "    dcat:byteSize \"%d\"^^xsd:nonNegativeInteger ;" % os.path.getsize(turtle_path),
        "  ] ;",
        "  dcat:distribution [",
        "    a dcat:Distribution ;",
        '    dcterms:title "RDF/XML"@en ;',
        "    dcat:downloadURL <https://w3id.org/wco-dm/4.3.0/ontology/wco-dm-4.3.0.owl> ;",
        "    dcat:mediaType <https://www.iana.org/assignments/media-types/application/rdf+xml> ;",
        "    dcat:byteSize \"%d\"^^xsd:nonNegativeInteger ;" % os.path.getsize(xml_path),
        "  ] ;",
        "  dcat:distribution [",
        "    a dcat:Distribution ;",
        '    dcterms:title "JSON-LD 1.1"@en ;',
        "    dcat:downloadURL <https://w3id.org/wco-dm/4.3.0/ontology/wco-dm-4.3.0.jsonld> ;",
        "    dcat:mediaType <https://www.iana.org/assignments/media-types/application/ld+json> ;",
        "    dcat:byteSize \"%d\"^^xsd:nonNegativeInteger ;" % os.path.getsize(jsonld_path),
        "  ] ;",
        "  dcat:distribution [",
        "    a dcat:Distribution ;",
        '    dcterms:title "SHACL shapes"@en ;',
        "    dcat:downloadURL <https://w3id.org/wco-dm/4.3.0/ontology/wco-dm-4.3.0-shapes.ttl> ;",
        "    dcat:mediaType <https://www.iana.org/assignments/media-types/text/turtle> ;",
        "    dcat:byteSize \"%d\"^^xsd:nonNegativeInteger ;" % os.path.getsize(shapes_path),
        "  ] .",
        "",
    ]
    profile_ttl = os.path.join(ROOT, "ontology", "wco-dm-4.3.0-profiles.ttl")
    profile_shapes = os.path.join(ROOT, "ontology", "wco-dm-4.3.0-profiles-shapes.ttl")
    if os.path.exists(profile_ttl):
        lines += [
            "<https://w3id.org/wco-dm/4.3.0/dataset/profiles> a dcat:Dataset, void:Dataset ;",
            '  dcterms:title "WCO Data Model 4.3.0 package profiles"@en ;',
            '  dcterms:description "Profile knowledge graph for MDIP, AIP, BIP DEC and BIP LPCO: package membership, data elements, associations, Min/Max, sequence, usage flags, remarks and mappings."@en ;',
            "  dcterms:source <https://datamodel.wcoomd.org/#/package> ;",
            "  dcterms:conformsTo <http://www.w3.org/TR/owl2-syntax/> ;",
            "  dcterms:conformsTo <http://www.w3.org/TR/shacl/> ;",
            '  dcat:keyword "WCO"@en, "profile"@en, "package"@en, "OWL"@en, "SHACL"@en ;',
            "  void:triples 25407 ;",
            "  void:classes 387 ;",
            "  void:properties 2618 ;",
            "  dcat:distribution [",
            "    a dcat:Distribution ;",
            '    dcterms:title "Profile Turtle"@en ;',
            "    dcat:downloadURL <https://w3id.org/wco-dm/4.3.0/ontology/wco-dm-4.3.0-profiles.ttl> ;",
            "    dcat:mediaType <https://www.iana.org/assignments/media-types/text/turtle> ;",
            "    dcat:byteSize \"%d\"^^xsd:nonNegativeInteger ;" % os.path.getsize(profile_ttl),
            "  ] ;",
            "  dcat:distribution [",
            "    a dcat:Distribution ;",
            '    dcterms:title "Profile SHACL shapes"@en ;',
            "    dcat:downloadURL <https://w3id.org/wco-dm/4.3.0/ontology/wco-dm-4.3.0-profiles-shapes.ttl> ;",
            "    dcat:mediaType <https://www.iana.org/assignments/media-types/text/turtle> ;",
            "    dcat:byteSize \"%d\"^^xsd:nonNegativeInteger ;" % os.path.getsize(profile_shapes),
            "  ] .",
            "",
        ]
    return "\n".join(lines)


def build_provenance(model):
    meta = model["meta"]
    files = [
        ("sources/xlsx/wco_lib_430.xlsx", "WCO DM 4.3.0 Library (LIB) workbook", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("sources/xlsx/wco_ois_430.xlsx", "WCO DM 4.3.0 Overall Information Structure (OIS) workbook", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("sources/package-tree.json", "WCO package tree (GET /datamodel/infopage/4.3.0)", "application/json"),
    ]
    source_iris = []
    source_blocks = []
    for path, label, mime in files:
        p = os.path.join(ROOT, path)
        if not os.path.exists(p):
            continue
        local = re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-")
        iri = "https://w3id.org/wco-dm/4.3.0/source/%s" % local
        source_iris.append("<%s>" % iri)
        block = """<%s> a prov:Entity ;
  rdfs:label %s ;
  dcterms:format %s ;
  wco:sha256 %s ;
  prov:atLocation %s .""" % (iri, lit(label, "en"), lit(mime), lit(sha256(p)), lit(path))
        source_blocks.append(block)
    lines = []
    lines.append("# PROV-O provenance for the WCO DM 4.3.0 ontology build")
    lines.append("@prefix prov: <http://www.w3.org/ns/prov#> .")
    lines.append("@prefix dcterms: <http://purl.org/dc/terms/> .")
    lines.append("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
    lines.append("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    lines.append("@prefix wco: <https://w3id.org/wco-dm/4.3.0#> .")
    lines.append("")
    lines.append("<https://w3id.org/wco-dm/4.3.0/agent/generator> a prov:SoftwareAgent ;")
    lines.append('  rdfs:label "wco-ontology-builder"@en .')
    lines.append("")
    lines.append("<https://w3id.org/wco-dm/4.3.0/activity/build> a prov:Activity ;")
    lines.append('  rdfs:label "Build WCO DM 4.3.0 ontology"@en ;')
    lines.append('  prov:startedAtTime "%s"^^xsd:dateTime ;' % meta["generated"])
    lines.append('  prov:endedAtTime "%s"^^xsd:dateTime ;' % meta["generated"])
    lines.append("  prov:wasAssociatedWith <https://w3id.org/wco-dm/4.3.0/agent/generator> ;")
    lines.append("  prov:used %s ;" % " , ".join(source_iris))
    lines.append("  prov:generated <https://w3id.org/wco-dm/4.3.0/entity/ontology> .")
    lines.append("")
    lines.extend(source_blocks)
    lines.append("")
    lines.append("<https://w3id.org/wco-dm/4.3.0/entity/ontology> a prov:Entity ;")
    lines.append('  rdfs:label "WCO DM 4.3.0 OWL 2 ontology"@en ;')
    lines.append("  prov:wasGeneratedBy <https://w3id.org/wco-dm/4.3.0/activity/build> ;")
    lines.append("  prov:wasDerivedFrom %s ." % " , ".join(source_iris))
    lines.append("")
    return "\n".join(lines)


def count_triples(path):
    # A light-weight count of Turtle statement terminators, adequate for the
    # catalog metadata; the authoritative count comes from the N3 validator.
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip().endswith(".") and not line.strip().startswith("#"):
                n += 1
    return n


def build():
    os.makedirs(ONT, exist_ok=True)
    model = load_model()

    ttl = build_turtle(model)
    ttl_path = os.path.join(ONT, "wco-dm-4.3.0.ttl")
    with open(ttl_path, "w", encoding="utf-8") as f:
        f.write(ttl)

    xml = build_rdfxml(model)
    xml_path = os.path.join(ONT, "wco-dm-4.3.0.owl")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml)

    jld = build_jsonld(model)
    jsonld_path = os.path.join(ONT, "wco-dm-4.3.0.jsonld")
    with open(jsonld_path, "w", encoding="utf-8") as f:
        f.write(jld)

    shapes = build_shapes(model)
    shapes_path = os.path.join(ONT, "wco-dm-4.3.0-shapes.ttl")
    with open(shapes_path, "w", encoding="utf-8") as f:
        f.write(shapes)

    good, bad = build_samples(model)
    with open(os.path.join(ONT, "wco-dm-4.3.0-sample.ttl"), "w", encoding="utf-8") as f:
        f.write(good)
    with open(os.path.join(ONT, "wco-dm-4.3.0-sample-invalid.ttl"), "w", encoding="utf-8") as f:
        f.write(bad)

    with open(os.path.join(ONT, "catalog.ttl"), "w", encoding="utf-8") as f:
        f.write(build_catalog(model, ttl_path, xml_path, jsonld_path, shapes_path))
    with open(os.path.join(ONT, "provenance.ttl"), "w", encoding="utf-8") as f:
        f.write(build_provenance(model))

    print("wrote", ttl_path, os.path.getsize(ttl_path), "bytes")
    print("wrote", xml_path, os.path.getsize(xml_path), "bytes")
    print("wrote", jsonld_path, os.path.getsize(jsonld_path), "bytes")
    print("wrote", shapes_path, os.path.getsize(shapes_path), "bytes")


if __name__ == "__main__":
    build()
