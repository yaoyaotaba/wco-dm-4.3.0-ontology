#!/usr/bin/env python3
"""Audit every sheet of the downloaded WCO DM 4.3.0 workbooks.

The two core workbooks (LIB and OIS) are the semantic inputs of the ontology.
The four package workbooks contain the same class/attribute IDs but add
package-specific Min/Max occurrence constraints and package usage flags.
This script records what is covered, what is only archived, and exports the
package-level cardinalities for traceability.
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

PACKAGES = [
    ("MDIP", "sources/package/3. Information Packages/3.1 Data Model/3.1. WCO DM MDIP_V4.3.0.xlsx"),
    ("AIP", "sources/package/3. Information Packages/3.1 Data Model/3.2. WCO DM AIP_V4.3.0.xlsx"),
    ("BIP DEC", "sources/package/3. Information Packages/3.1 Data Model/3.3. WCO DM BIP DEC_V4.3.0.xlsx"),
    ("BIP LPCO", "sources/package/3. Information Packages/3.1 Data Model/3.4. WCO DM BIP LPCO_V4.3.0.xlsx"),
]
CHANGES = "sources/package/4. Changes/Section 4. WCO DM Overview of Changes_V4.3.0-final 260622.xlsx"


def header_map(rows):
    """Find the header row and map known column titles to column numbers."""
    known = ("Type", "WCO ID", "WCO Name", "WCO Definition", "WCO Format", "Min", "Max", "WCO Code List")
    best = None
    for r in sorted(rows):
        if r > 8:
            break
        found = {}
        for c, v in rows[r].items():
            v = clean(v)
            if v in known:
                found[v] = c
        if "Type" in found and "WCO ID" in found and len(found) >= 5:
            best = (r, found)
            break
    return best


def parse_package(label, path):
    wb = read_xlsx(path)
    sheet = list(wb.keys())[0]
    rows = wb[sheet]
    hdr = header_map(rows)
    if not hdr:
        raise RuntimeError("header not found: " + path)
    hr, h = hdr
    out = []
    for r in sorted(rows):
        if r <= hr:
            continue
        typ = clean(rows[r].get(h.get("Type", -1), ""))
        wco_id = clean(rows[r].get(h.get("WCO ID", -1), ""))
        if not wco_id:
            continue
        out.append(
            {
                "package": label,
                "sheet": sheet,
                "row": r,
                "path": clean(rows[r].get(1, "")),
                "type": typ,
                "wco_id": wco_id,
                "name": clean(rows[r].get(h.get("WCO Name", -1), "")),
                "definition": clean(rows[r].get(h.get("WCO Definition", -1), "")),
                "format": clean(rows[r].get(h.get("WCO Format", -1), "")),
                "min": clean(rows[r].get(h.get("Min", -1), "")),
                "max": clean(rows[r].get(h.get("Max", -1), "")),
                "code_list": clean(rows[r].get(h.get("WCO Code List", -1), "")),
            }
        )
    return sheet, out


def main():
    model = json.load(open(os.path.join(ROOT, "data", "model.json"), encoding="utf-8"))
    core_classes = set(model["classes"])
    core_attrs = set(model["data_properties"])
    core_class_def = {k: v["definition"] for k, v in model["classes"].items()}
    core_attr_def = {k: v["definition"] for k, v in model["data_properties"].items()}

    sheet_rows = []
    all_rows = []
    for label, rel in PACKAGES:
        sheet, rows = parse_package(label, os.path.join(ROOT, rel))
        all_rows.extend(rows)
        cls = {r["wco_id"] for r in rows if r["type"] == "C"}
        ats = {r["wco_id"] for r in rows if r["type"] == "E"}
        mins = Counter(r["min"] for r in rows)
        maxs = Counter(r["max"] for r in rows)
        def_mismatch = 0
        for r in rows:
            ref = core_class_def if r["type"] == "C" else core_attr_def
            if r["wco_id"] in ref and r["definition"] and ref[r["wco_id"]] and r["definition"] != ref[r["wco_id"]]:
                def_mismatch += 1
        sheet_rows.append(
            {
                "workbook": label,
                "sheet": sheet,
                "rows": len(rows),
                "classes": len(cls),
                "attributes": len(ats),
                "new_class_ids": len(cls - core_classes),
                "new_attr_ids": len(ats - core_attrs),
                "min_values": "; ".join(f"{k or '(blank)'}={v}" for k, v in mins.most_common()),
                "max_values": "; ".join(f"{k or '(blank)'}={v}" for k, v in maxs.most_common()),
                "definition_mismatches": def_mismatch,
                "status": "archived; IDs already in core; Min/Max now ingested",
            }
        )
        print(f"{label}: sheet={sheet!r} rows={len(rows)} C={len(cls)} E={len(ats)} newC={len(cls-core_classes)} newE={len(ats-core_attrs)} min={dict(mins)} max={dict(maxs)} def_mismatch={def_mismatch}")

    # Changes workbook sheets
    wb = read_xlsx(os.path.join(ROOT, CHANGES))
    for name, rows in wb.items():
        sheet_rows.append(
            {
                "workbook": "Changes",
                "sheet": name,
                "rows": max(rows) if rows else 0,
                "classes": 0,
                "attributes": 0,
                "new_class_ids": 0,
                "new_attr_ids": 0,
                "min_values": "",
                "max_values": "",
                "definition_mismatches": 0,
                "status": "change log; archived, not model content",
            }
        )

    with open(os.path.join(ROOT, "data", "package-sheets.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(sheet_rows[0].keys()))
        w.writeheader()
        w.writerows(sheet_rows)

    with open(os.path.join(ROOT, "data", "package-cardinalities.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)

    # Global cardinality consistency for data elements.
    e_rows = [r for r in all_rows if r["type"] == "E"]
    e_max = Counter(r["max"] for r in e_rows)
    e_min = Counter(r["min"] for r in e_rows)
    print("all package rows:", len(all_rows))
    print("data element max:", dict(e_max), "min:", dict(e_min))
    print("wrote data/package-sheets.csv and data/package-cardinalities.csv")


if __name__ == "__main__":
    main()
