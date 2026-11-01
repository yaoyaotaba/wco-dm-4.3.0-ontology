#!/usr/bin/env python3
"""Build the compact JSON/JS payload used by the static visualisation."""
from __future__ import annotations

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def category(c):
    b = c.get("branch")
    s = c.get("super_name")
    if b == "3MD":
        return "metadata"
    if b == "ROOT" or s == "RootDocument":
        return "root"
    if s == "Party":
        return "party"
    if s == "Location":
        return "location"
    if s == "GovernmentAgency":
        return "agency"
    if s == "TransportMeans":
        return "transport"
    return "content"


def build():
    with open(os.path.join(ROOT, "data", "model.json"), encoding="utf-8") as f:
        m = json.load(f)

    classes = {}
    for c in m["classes"].values():
        classes[c["id"]] = {
            "id": c["id"],
            "name": c["name"],
            "zh": c.get("zh", ""),
            "def": c["definition"],
            "depth": c["depth"],
            "branch": c["branch"],
            "category": category(c),
            "path": c["typical_path"],
            "rawPath": c["paths"][0] if c["paths"] else "",
            "super": (c["super_id"] + " " + c["super_name"]).strip(),
            "occurrences": c["occurrences"],
            "parents": [],
            "children": [],
            "attrs": [],
            "inferred": c["id"] in ("42A", "58C", "74B"),
        }

    edges = []
    for role, o in m["object_properties"].items():
        for p in o["parents"]:
            edges.append(
                {
                    "source": p,
                    "target": o["range"],
                    "role": role,
                    "label": o["label"],
                    "inferred": bool(o.get("inferred")),
                }
            )
            classes[p]["children"].append({"id": o["range"], "role": role})
            classes[o["range"]]["parents"].append({"id": p, "role": role})

    for d in m["data_properties"].values():
        for cid in d["classes"]:
            if cid in classes:
                classes[cid]["attrs"].append(d["id"])

    # stable ordering
    for c in classes.values():
        c["children"].sort(key=lambda x: (x["role"].lower(), x["id"]))
        c["parents"].sort(key=lambda x: x["role"].lower())
        c["attrs"].sort(key=lambda x: x)

    edge_keys = set()
    unique_edges = []
    for e in edges:
        k = (e["source"], e["target"], e["role"])
        if k not in edge_keys:
            edge_keys.add(k)
            unique_edges.append(e)
    unique_edges.sort(key=lambda e: (e["source"], e["role"].lower(), e["target"]))

    attrs = []
    for d in m["data_properties"].values():
        attrs.append(
            {
                "id": d["id"],
                "name": d["name"],
                "def": d["definition"],
                "format": d["format"],
                "datatype": d["datatype"].replace("xsd:", ""),
                "core": d["core_type"],
                "codeList": d["code_list"],
                "codeListName": d["code_list_name"],
                "xml": d["xml_tag"],
                "json": d["json_tag"],
                "classes": d["classes"],
                "count": len(d["classes"]),
            }
        )
    attrs.sort(key=lambda x: (x["name"].lower(), x["id"]))

    ops = []
    for o in m["object_properties"].values():
        ops.append(
            {
                "role": o["role"],
                "label": o["label"],
                "def": o["definition"],
                "range": o["range"],
                "rangeName": classes.get(o["range"], {}).get("name", ""),
                "parents": o["parents"],
                "count": len(o["parents"]),
                "xml": o["xml_tag"],
                "json": o["json_tag"],
                "inferred": bool(o.get("inferred")),
            }
        )
    ops.sort(key=lambda x: x["role"].lower())

    used_by_names = {a["id"]: a["name"] for a in attrs}
    code_lists = []
    for cl in m["code_lists"]:
        code_lists.append(
            {
                "name": cl["name"],
                "source": cl["source"],
                "codes": cl["codes"],
                "usedBy": cl["used_by"],
                "usedByNames": [used_by_names.get(x, x) for x in cl["used_by"]],
                "note": cl["note"],
            }
        )
    code_lists.sort(key=lambda x: x["name"].lower())

    s = m["summary"]
    package_rows = []
    pkg_csv = os.path.join(ROOT, "data", "package-sheets.csv")
    if os.path.exists(pkg_csv):
        with open(pkg_csv, encoding="utf-8-sig") as f:
            package_rows = list(csv.DictReader(f))
    model_pkg = [r for r in package_rows if r["workbook"] != "Changes"]
    change_pkg = [r for r in package_rows if r["workbook"] == "Changes"]
    package_data_rows = sum(int(r["attributes"]) for r in model_pkg)
    card_csv = os.path.join(ROOT, "data", "package-cardinalities.csv")
    if os.path.exists(card_csv):
        with open(card_csv, encoding="utf-8-sig") as f:
            package_data_rows = sum(1 for r in csv.DictReader(f) if r.get("type") == "E")

    profiles = {"packages": [], "flags": []}
    prof_path = os.path.join(ROOT, "data", "profiles.json")
    if os.path.exists(prof_path):
        profiles = json.load(open(prof_path, encoding="utf-8"))

    payload = {
        "meta": {
            "version": "4.3.0",
            "generated": m["meta"]["generated"],
            "sourcePage": m["meta"]["source_page"],
            "sourceTree": m["meta"]["source_tree_api"],
            "ontologyIri": m["meta"]["ontology_iri"],
            "namespace": m["meta"]["namespace"],
            "triples": 26663,
            "shapesTriples": 18459,
            "stats": {
                "classes": s["classes"],
                "objectProperties": s["object_properties"],
                "dataProperties": s["data_properties"],
                "associations": len(unique_edges),
                "attributeUsages": s["attribute_usages"],
                "codeLists": s["code_lists"],
                "codeValues": s["code_values"],
                "sourceFiles": s["package_files"],
                "withAttributes": sum(1 for c in classes.values() if c["attrs"]),
                "withChildren": sum(1 for c in classes.values() if c["children"]),
                "excelWorkbooks": 7,
                "excelSheets": 11,
                "coreSheets": 4,
                "packageSheets": len(model_pkg),
                "changeLogSheets": len(change_pkg),
                "packageRows": sum(int(r["rows"]) for r in model_pkg),
                "packageDataRows": package_data_rows,
                "profilePackages": len(profiles.get("packages", [])),
                "profileClasses": sum(int(x["classes"]) for x in profiles.get("packages", [])),
                "profileElements": sum(int(x["elements"]) for x in profiles.get("packages", [])),
                "profileAssociations": sum(int(x["associations"]) for x in profiles.get("packages", [])),
                "profileFlags": len(profiles.get("flags", [])),
                "profileTriples": 25407,
                "profileShapesTriples": 14248,
            },
        },
        "classes": list(classes.values()),
        "edges": unique_edges,
        "attributes": attrs,
        "objectProperties": ops,
        "codeLists": code_lists,
        "profiles": profiles,
    }

    out_dir = os.path.join(ROOT, "site", "assets")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "data.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(out_dir, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.WCO_DATA = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print("classes", len(classes), "edges", len(unique_edges), "attrs", len(attrs), "ops", len(ops), "code lists", len(code_lists))
    print("data.js bytes", os.path.getsize(os.path.join(out_dir, "data.js")))


if __name__ == "__main__":
    build()
