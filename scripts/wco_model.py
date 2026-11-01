#!/usr/bin/env python3
"""Normalise the WCO DM 4.3.0 LIB and OIS workbooks into a model.

The LIB workbook provides the global element library (classes, attributes,
core data types, code list catalogue).  The OIS workbook provides the
containment hierarchy and the context in which each class / attribute is used.
"""
from __future__ import annotations

import csv
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _col_num(ref: str):
    m = re.match(r"([A-Z]+)(\d+)", ref or "")
    if not m:
        return None, None
    letters, row = m.groups()
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n, int(row)


def _shared_strings(z):
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    out = []
    for si in root.findall("m:si", NS):
        out.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
    return out


def _sheet_targets(z):
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    out = []
    for s in wb.find("m:sheets", NS):
        target = rmap.get(s.get("{%s}id" % NS["r"]), "")
        if not target.startswith("xl/"):
            target = "xl/" + target.lstrip("/")
        out.append((s.get("name"), target))
    return out


def read_xlsx(path: str):
    """Return {sheet_name: {row_number: {col_number: value}}}."""
    z = zipfile.ZipFile(path)
    shared = _shared_strings(z)
    result = {}
    for name, target in _sheet_targets(z):
        root = ET.fromstring(z.read(target))
        rows = {}
        for row in root.iter("{%s}row" % NS["m"]):
            r = int(row.get("r"))
            for c in row.findall("m:c", NS):
                cn, rn = _col_num(c.get("r"))
                if cn is None:
                    continue
                t = c.get("t")
                v = c.find("m:v", NS)
                isel = c.find("m:is", NS)
                val = None
                if t == "s" and v is not None:
                    idx = int(v.text)
                    val = shared[idx] if idx < len(shared) else ""
                elif t == "inlineStr" and isel is not None:
                    val = "".join(x.text or "" for x in isel.iter("{%s}t" % NS["m"]))
                elif v is not None:
                    val = v.text
                if val not in (None, ""):
                    rows.setdefault(rn, {})[cn] = val
        result[name] = rows
    return result


def clean(value) -> str:
    if value is None:
        return ""
    return re.sub(r"[ \t]+", " ", str(value).replace("\r", "\n")).strip()


def humanize(name: str) -> str:
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|[0-9]+", name or "")
    if not words:
        return (name or "").lower()
    out = [w if w.isupper() else w.lower() for w in words]
    return " ".join(out)


def slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", name or "")
    s = s.strip("._-")
    return s or "item"


ZH_CLASSES = {
    "OIS": "总体信息结构",
    "MDIP": "元数据信息包",
    "ContentInformationStructure": "内容信息结构",
    "Declaration": "报关单",
    "Consignment": "货物运输批次",
    "GoodsShipment": "货物装运",
    "GoodsItem": "货物项",
    "Party": "当事人",
    "Address": "地址",
    "Contact": "联系方式",
    "Communication": "通信",
    "Document": "单据",
    "TransportMeans": "运输工具",
    "TransportEquipment": "运输设备",
    "Location": "地点",
    "GovernmentAgency": "政府机构",
    "AdditionalDocument": "附加单据",
    "AdditionalInformation": "附加信息",
    "AdditionalReference": "附加参考",
    "Authentication": "认证",
    "Authenticator": "认证人",
    "Authorization": "授权",
    "DeclarationOffice": "报关办公室",
    "Agent": "代理人",
    "Carrier": "承运人",
    "Consignee": "收货人",
    "Consignor": "发货人",
    "Declarant": "申报人",
    "Exporter": "出口商",
    "Importer": "进口商",
    "Manufacturer": "制造商",
    "NotifyParty": "通知方",
    "Seller": "卖方",
    "Buyer": "买方",
    "UCR": "唯一托运参考号",
    "Warehouse": "仓库",
    "Seal": "封志",
    "Package": "包装",
    "Invoice": "发票",
    "DutyTaxFee": "关税税费",
    "CommodityClassification": "商品归类",
    "TransportContractDocument": "运输合同单据",
    "TransportMovement": "运输移动",
    "CustomsValuation": "海关估价",
    "Origin": "原产地",
}

CORE_ZH = {
    "Code": "代码",
    "Identifier": "标识符",
    "Text": "文本",
    "Date Time": "日期时间",
    "Numeric": "数值",
    "Quantity": "数量",
    "Measure": "计量",
    "Amount": "金额",
    "Indicator": "指示符",
    "Binary Object": "二进制对象",
}

XSD = "http://www.w3.org/2001/XMLSchema#"


def parse_format(fmt: str):
    """Return (xsd datatype local name, facets dict)."""
    f = (fmt or "").strip()
    if not f or f.upper() == "NA":
        return "string", {}
    m = re.match(r"^(an|a|n)\.?\.?(\d+)(?:,(\d+))?$", f, re.I)
    if not m:
        return "string", {}
    kind, total, frac = m.group(1).lower(), int(m.group(2)), m.group(3)
    if kind == "n":
        facets = {"totalDigits": total}
        if frac is not None:
            facets["fractionDigits"] = int(frac)
        else:
            facets["fractionDigits"] = 0
        return "decimal", facets
    facets = {}
    if ".." in f or ".N" in f.upper():
        facets["maxLength"] = total
    else:
        facets["minLength"] = total
        facets["maxLength"] = total
    if kind == "a":
        facets["pattern"] = "[A-Za-z]{%d}" % total
    elif kind == "an" and "." not in f:
        facets["pattern"] = "[A-Za-z0-9]{%d}" % total
    return "string", facets


def datatype_for(core_type: str, fmt: str):
    core = (core_type or "").strip()
    if core == "Date Time":
        return "dateTime", {}
    if core == "Indicator":
        return "boolean", {}
    if core == "Binary Object":
        return "base64Binary", {}
    if core in ("Numeric", "Quantity", "Measure", "Amount"):
        return "decimal", parse_format(fmt)[1] if fmt else {}
    return parse_format(fmt)


def parse_code_values(raw: str):
    """Parse the free-text Code ID column into a list of codes.

    The workbook sometimes stores one code per line, sometimes a short
    whitespace-separated list.  Descriptions are only used when their count
    matches the number of codes.
    """
    if not raw:
        return []
    lines = [ln.strip() for ln in str(raw).splitlines() if ln.strip()]
    codes = []
    for ln in lines:
        parts = re.split(r"\s+", ln)
        if len(parts) > 1 and all(len(p) <= 8 for p in parts):
            codes.extend(parts)
        else:
            codes.append(ln)
    # de-duplicate, preserve order
    seen = set()
    out = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def parse_code_descriptions(raw: str):
    if not raw:
        return []
    return [ln.strip() for ln in str(raw).splitlines() if ln.strip()]


def load_lib(path: str):
    wb = read_xlsx(path)
    names = list(wb.keys())
    rows = wb[names[0]]  # DataSet 1.2, 1.3, 1.4
    classes = []
    attrs = []
    for r in sorted(rows):
        if r < 3:
            continue
        row = rows[r]
        typ = clean(row.get(29))
        if not typ:
            continue
        item = {
            "row": r,
            "path": clean(row.get(7)),
            "class_id": clean(row.get(8)),
            "class_name": clean(row.get(9)),
            "attr_id": clean(row.get(10)),
            "attr_name": clean(row.get(11)),
            "definition": clean(row.get(12)),
            "format": clean(row.get(13)),
            "code_list": clean(row.get(14)),
            "code_id": clean(row.get(15)),
            "code_desc": clean(row.get(16)),
            "core_type": clean(row.get(17)),
            "uid": clean(row.get(18)),
            "tded_name": clean(row.get(19)),
            "den": clean(row.get(20)),
            "named_type": clean(row.get(21)),
            "xml_tag": clean(row.get(22)),
            "json_tag": clean(row.get(23)),
            "super_id": clean(row.get(24)),
            "super_name": clean(row.get(25)),
            "super_element_id": clean(row.get(26)),
            "super_element_name": clean(row.get(27)),
            "seq": clean(row.get(28)),
            "type": typ,
            "usage": [clean(row.get(i)) for i in range(1, 7) if clean(row.get(i))],
        }
        if typ == "C":
            classes.append(item)
        elif typ == "E":
            attrs.append(item)
    code_rows = wb[names[2]]  # DataSet 1.6
    code_lists = []
    for r in sorted(code_rows):
        if r < 3:
            continue
        row = code_rows[r]
        name = clean(row.get(2))
        if not name:
            continue
        source = clean(row.get(3))
        codes = parse_code_values(row.get(4))
        descs = parse_code_descriptions(row.get(5))
        code_items = []
        for i, c in enumerate(codes):
            desc = descs[i] if len(descs) == len(codes) else ""
            code_items.append({"code": c, "description": desc})
        code_lists.append(
            {
                "name": name,
                "local": "CL_" + slug(name),
                "source": source,
                "codes": code_items,
                "note": clean(row.get(5)) if len(descs) != len(codes) else "",
            }
        )
    core_rows = wb[names[1]]  # DataSet 1.5
    core_types = []
    for r in sorted(core_rows):
        if r < 3:
            continue
        row = core_rows[r]
        if clean(row.get(2)):
            core_types.append(
                {
                    "id": clean(row.get(1)),
                    "name": clean(row.get(2)),
                    "attribute": clean(row.get(3)),
                    "code_list": clean(row.get(4)),
                    "note": clean(row.get(5)),
                }
            )
    return {"classes": classes, "attrs": attrs, "code_lists": code_lists, "core_types": core_types}


def load_ois(path: str):
    wb = read_xlsx(path)
    rows = wb[list(wb.keys())[0]]
    records = []
    for r in sorted(rows):
        if r < 4:
            continue
        row = rows[r]
        path = clean(row.get(1))
        if not path:
            continue
        records.append(
            {
                "row": r,
                "path": path,
                "id": clean(row.get(2)),
                "name": clean(row.get(3)),
                "definition": clean(row.get(4)),
                "remarks": clean(row.get(5)),
                "format": clean(row.get(6)),
                "code_list": clean(row.get(7)),
                "cis_upi": clean(row.get(8)),
                "dec_uci": clean(row.get(9)),
                "ig_uci": clean(row.get(10)),
                "lpco_uci": clean(row.get(11)),
                "mdip_uci": clean(row.get(12)),
                "res_uci": clean(row.get(13)),
                "attr_upi": clean(row.get(14)),
                "seq": clean(row.get(15)),
                "type": clean(row.get(16)),
            }
        )
    return records


def build_model(lib_path: str, ois_path: str, package_tree_path: str):
    lib = load_lib(lib_path)
    ois = load_ois(ois_path)

    # --- classes -----------------------------------------------------------
    lib_classes = {}
    for c in lib["classes"]:
        cid = c["class_id"] or "OIS"
        if cid not in lib_classes:
            lib_classes[cid] = dict(c, class_id=cid)
        else:
            # keep the first definition but merge usage / superclass info
            for k in ("usage",):
                lib_classes[cid][k] = sorted(set(lib_classes[cid][k]) | set(c[k]))

    class_paths = defaultdict(list)
    class_defs_ois = {}
    class_names_ois = {}
    path_to_class = {}
    for rec in ois:
        if rec["type"] != "C":
            continue
        cid = rec["id"] or "OIS"
        class_paths[cid].append(rec["path"])
        path_to_class[rec["path"]] = cid
        if rec["definition"] and cid not in class_defs_ois:
            class_defs_ois[cid] = rec["definition"]
        if rec["name"] and cid not in class_names_ois:
            class_names_ois[cid] = rec["name"]

    all_class_ids = sorted(set(lib_classes) | set(class_paths), key=lambda x: (x != "OIS", x))
    classes = {}
    for cid in all_class_ids:
        lc = lib_classes.get(cid, {})
        name = lc.get("class_name") or class_names_ois.get(cid) or cid
        definition = lc.get("definition") or class_defs_ois.get(cid, "")
        if cid == "OIS":
            name = "OIS"
            definition = (
                "Overall Information Structure (OIS): the root container of the WCO Data Model "
                "4.3.0 class hierarchy, comprising the MDIP metadata package and the Content "
                "Information Structure (CIS)."
            )
        classes[cid] = {
            "id": cid,
            "local": "C_" + slug(cid),
            "iri": "https://w3id.org/wco-dm/4.3.0#C_" + slug(cid),
            "name": name,
            "zh": ZH_CLASSES.get(name, ""),
            "definition": definition,
            "paths": class_paths.get(cid, []),
            "xml_tag": lc.get("xml_tag", ""),
            "json_tag": lc.get("json_tag", ""),
            "super_id": lc.get("super_id", ""),
            "super_name": lc.get("super_name", ""),
            "usage": lc.get("usage", []),
        }

    # --- containment edges -------------------------------------------------
    edges = {}
    for rec in ois:
        if rec["type"] != "C" or rec["path"] == "OIS":
            continue
        parent_path, role = rec["path"].rsplit("/", 1)
        parent = path_to_class.get(parent_path)
        child = rec["id"] or "OIS"
        if not parent:
            continue
        key = (parent, role)
        edges[key] = {
            "parent": parent,
            "role": role,
            "child": child,
            "paths": edges.get(key, {}).get("paths", []) + [rec["path"]],
            "inferred": False,
        }

    # Three SC1 RootDocument classes occur in the LIB but not in the OIS tree:
    # Declaration (42A), AIP (58C) and LPCO (74B).  Keep them and place them as
    # top-level document roots under OIS.  The placement is explicitly flagged.
    for cid, lc in lib_classes.items():
        if cid in path_to_class.values() or cid == "OIS":
            continue
        if lc.get("super_id") == "SC1":
            role = lc.get("class_name") or cid
            key = ("OIS", role)
            if key in edges:
                continue
            edges[key] = {
                "parent": "OIS",
                "role": role,
                "child": cid,
                "paths": ["OIS/" + role],
                "inferred": True,
            }
            class_paths[cid].append("OIS/" + role)

    # dedupe repeated paths per edge
    for e in edges.values():
        e["paths"] = sorted(set(e["paths"]))

    # The class objects were created before the inferred root edges; refresh
    # the path lists that they hold.
    for cid in classes:
        classes[cid]["paths"] = sorted(set(class_paths.get(cid, [])))
        classes[cid]["occurrences"] = len(classes[cid]["paths"])

    # --- attributes --------------------------------------------------------
    lib_attrs = {}
    for a in lib["attrs"]:
        aid = a["attr_id"]
        if not aid:
            continue
        if aid not in lib_attrs:
            lib_attrs[aid] = dict(a)
        else:
            # merge class usage metadata, keep first DEN/XML/JSON definition
            for k in ("super_element_id", "super_element_name", "code_list", "core_type"):
                if not lib_attrs[aid].get(k) and a.get(k):
                    lib_attrs[aid][k] = a[k]

    attr_usage = defaultdict(set)
    attr_ois_meta = {}
    for rec in ois:
        if rec["type"] != "E":
            continue
        parent_path = rec["path"].rsplit("/", 1)[0]
        cid = path_to_class.get(parent_path)
        if not cid:
            continue
        aid = rec["id"]
        if not aid:
            continue
        attr_usage[aid].add(cid)
        meta = attr_ois_meta.setdefault(
            aid,
            {
                "definition": rec["definition"],
                "format": rec["format"],
                "code_list": rec["code_list"],
                "name": rec["name"],
                "upis": set(),
            },
        )
        if rec["attr_upi"]:
            meta["upis"].add(rec["attr_upi"])

    # ensure data elements referenced by LIB but absent from OIS are kept,
    # and add the LIB class context to every data element (OIS is a usage
    # view and does not necessarily list every library element).
    for a in lib["attrs"]:
        aid = a["attr_id"]
        if not aid:
            continue
        if aid not in attr_ois_meta:
            attr_ois_meta[aid] = {
                "definition": a["definition"],
                "format": a["format"],
                "code_list": a["code_list"],
                "name": a["attr_name"],
                "upis": set(),
            }
        if a["class_id"]:
            attr_usage[aid].add(a["class_id"])

    # code-list source -> candidate names
    source_to_names = defaultdict(list)
    for cl in lib["code_lists"]:
        source_to_names[clean(cl["source"])].append(cl["name"])

    data_properties = {}
    for aid, meta in attr_ois_meta.items():
        la = lib_attrs.get(aid, {})
        name = la.get("attr_name") or meta["name"] or aid
        fmt = la.get("format") or meta["format"]
        code_list = la.get("code_list") or meta["code_list"]
        core = la.get("core_type", "")
        dtype, facets = datatype_for(core, fmt)
        candidates = source_to_names.get(clean(code_list), [])
        code_name = candidates[0] if len(candidates) == 1 else ""
        data_properties[aid] = {
            "id": aid,
            "local": "dp_" + slug(aid),
            "iri": "https://w3id.org/wco-dm/4.3.0#dp_" + slug(aid),
            "name": name,
            "definition": la.get("definition") or meta["definition"],
            "format": fmt,
            "core_type": core,
            "datatype": "xsd:" + dtype,
            "facets": facets,
            "code_list": code_list,
            "code_list_name": code_name,
            "code_list_local": ("CL_" + slug(code_name)) if code_name else "",
            "xml_tag": la.get("xml_tag", ""),
            "json_tag": la.get("json_tag", ""),
            "named_type": la.get("named_type", ""),
            "super_element": (
                (la.get("super_element_id", "") + " " + la.get("super_element_name", "")).strip()
            ),
            "seq": la.get("seq", ""),
            "classes": sorted(attr_usage.get(aid, set())),
            "upis": sorted(meta["upis"]),
            # All 8,212 data-element rows in the four package workbooks have
            # Min=0 and Max=1.  Object-property maxima vary by package and are
            # therefore not asserted globally.
            "min_occurs": 0,
            "max_occurs": 1,
        }

    # --- object properties -------------------------------------------------
    by_role = defaultdict(list)
    for (parent, role), e in edges.items():
        by_role[role].append(e)

    object_properties = {}
    for role, es in by_role.items():
        children = {e["child"] for e in es}
        parents = sorted({e["parent"] for e in es})
        child = sorted(children)[0] if children else ""
        object_properties[role] = {
            "role": role,
            "local": "has" + role[:1].upper() + role[1:],
            "iri": "https://w3id.org/wco-dm/4.3.0#has" + role[:1].upper() + role[1:],
            "label": "has " + humanize(role),
            "definition": (
                "Associates a containing WCO DM class with its %s component (%s)."
                % (humanize(role), classes.get(child, {}).get("name", child))
            ),
            "range": child,
            "parents": parents,
            "paths": sorted({p for e in es for p in e["paths"]}),
            "xml_tag": role,
            "json_tag": classes.get(child, {}).get("json_tag", "") or humanize(role),
            "inferred": any(e.get("inferred") for e in es),
            "min_occurs": 0,
        }

    # --- navigation / statistics -----------------------------------------
    children = defaultdict(list)
    parents = defaultdict(list)
    for op in object_properties.values():
        for p in op["parents"]:
            children[p].append(op["role"])
            parents[op["range"]].append(op["role"])

    # shortest path from OIS for display
    import collections as _c

    q = _c.deque([("OIS", ["OIS"])])
    shortest = {"OIS": ["OIS"]}
    while q:
        cur, path = q.popleft()
        for role in children.get(cur, []):
            nxt = object_properties[role]["range"]
            if nxt not in shortest:
                shortest[nxt] = path + [nxt]
                q.append((nxt, path + [nxt]))

    for cid, c in classes.items():
        p = shortest.get(cid, [cid])
        c["depth"] = len(p) - 1
        c["typical_path"] = " / ".join(classes[x]["name"] for x in p)
        c["branch"] = p[1] if len(p) > 1 else "OIS"
        if cid in ("42A", "58C", "74B"):
            c["branch"] = "ROOT"
        c["occurrences"] = len(c["paths"])
        c["parent_roles"] = sorted(set(parents.get(cid, [])))
        c["child_roles"] = sorted(set(children.get(cid, [])))

    # --- code lists --------------------------------------------------------
    used_by_source = defaultdict(list)
    for aid, dp in data_properties.items():
        if dp["code_list"]:
            used_by_source[clean(dp["code_list"])].append(aid)

    code_lists = []
    for cl in lib["code_lists"]:
        cl = dict(cl)
        cl["used_by"] = sorted(used_by_source.get(clean(cl["source"]), []))
        cl["iri"] = "https://w3id.org/wco-dm/4.3.0#" + cl["local"]
        code_lists.append(cl)

    # --- package tree / download manifest ---------------------------------
    tree = json.load(open(package_tree_path, encoding="utf-8"))["list"]
    pkg_files = []
    stack = []
    for item in tree:
        lvl = item.get("level", 0)
        stack = stack[:lvl]
        if item.get("isDir"):
            stack.append(item["fileName"])
        else:
            pkg_files.append(
                {
                    "path": (item.get("relative") or "") + item.get("fileName", ""),
                    "name": item.get("fileName", ""),
                    "dir": " / ".join(stack),
                }
            )

    summary = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "version": "4.3.0",
        "classes": len(classes),
        "object_properties": len(object_properties),
        "data_properties": len(data_properties),
        "containment_edges": len(edges),
        "attribute_usages": sum(len(v["classes"]) for v in data_properties.values()),
        "code_lists": len(code_lists),
        "code_values": sum(len(c["codes"]) for c in code_lists),
        "package_files": len(pkg_files),
        "core_types": lib["core_types"],
    }

    model = {
        "meta": {
            "version": "4.3.0",
            "generated": summary["generated"],
            "source_page": "https://datamodel.wcoomd.org/#/package",
            "source_tree_api": "https://datamodel.wcoomd.org/datamodel/infopage/4.3.0",
            "ontology_iri": "https://w3id.org/wco-dm/4.3.0",
            "namespace": "https://w3id.org/wco-dm/4.3.0#",
            "summary": summary,
        },
        "summary": summary,
        "classes": classes,
        "object_properties": object_properties,
        "data_properties": data_properties,
        "code_lists": code_lists,
        "package_files": pkg_files,
        "core_types": lib["core_types"],
    }
    return model, lib, ois


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def export_model(model, lib, ois, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "model.json"), "w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)

    classes = model["classes"]
    ops = model["object_properties"]
    dps = model["data_properties"]

    write_csv(
        os.path.join(outdir, "classes.csv"),
        [
            "id", "name", "zh", "definition", "depth", "branch", "typical_path",
            "super_id", "super_name", "occurrences", "parent_roles", "child_roles",
        ],
        [
            {
                "id": c["id"], "name": c["name"], "zh": c["zh"],
                "definition": c["definition"], "depth": c["depth"],
                "branch": c["branch"], "typical_path": c["typical_path"],
                "super_id": c["super_id"], "super_name": c["super_name"],
                "occurrences": c["occurrences"],
                "parent_roles": "; ".join(c["parent_roles"]),
                "child_roles": "; ".join(c["child_roles"]),
            }
            for c in sorted(classes.values(), key=lambda x: (x["depth"], x["name"]))
        ],
    )
    write_csv(
        os.path.join(outdir, "object-properties.csv"),
        ["role", "label", "range_id", "range_name", "parent_count", "parent_ids", "xml_tag", "json_tag", "min_occurs", "definition"],
        [
            {
                "role": o["role"], "label": o["label"], "range_id": o["range"],
                "range_name": classes.get(o["range"], {}).get("name", ""),
                "parent_count": len(o["parents"]), "parent_ids": "; ".join(o["parents"]),
                "xml_tag": o["xml_tag"], "json_tag": o["json_tag"],
                "min_occurs": o.get("min_occurs", 0),
                "definition": o["definition"],
            }
            for o in sorted(ops.values(), key=lambda x: x["role"].lower())
        ],
    )
    write_csv(
        os.path.join(outdir, "data-properties.csv"),
        [
            "id", "name", "definition", "format", "datatype", "core_type", "code_list",
            "code_list_name", "class_count", "classes", "xml_tag", "json_tag", "super_element",
            "min_occurs", "max_occurs",
        ],
        [
            {
                "id": d["id"], "name": d["name"], "definition": d["definition"],
                "format": d["format"], "datatype": d["datatype"], "core_type": d["core_type"],
                "code_list": d["code_list"], "code_list_name": d["code_list_name"],
                "class_count": len(d["classes"]), "classes": "; ".join(d["classes"]),
                "xml_tag": d["xml_tag"], "json_tag": d["json_tag"],
                "super_element": d["super_element"],
                "min_occurs": d.get("min_occurs", 0), "max_occurs": d.get("max_occurs", 1),
            }
            for d in sorted(dps.values(), key=lambda x: x["name"].lower())
        ],
    )
    write_csv(
        os.path.join(outdir, "code-lists.csv"),
        ["name", "source", "code_count", "codes", "used_by_count", "used_by"],
        [
            {
                "name": c["name"], "source": c["source"],
                "code_count": len(c["codes"]),
                "codes": "; ".join(x["code"] for x in c["codes"]),
                "used_by_count": len(c["used_by"]),
                "used_by": "; ".join(c["used_by"]),
            }
            for c in sorted(model["code_lists"], key=lambda x: x["name"].lower())
        ],
    )
    write_csv(
        os.path.join(outdir, "ois-paths.csv"),
        ["path", "type", "id", "name", "format", "code_list", "definition", "attr_upi", "seq"],
        [
            {
                "path": r["path"], "type": r["type"], "id": r["id"], "name": r["name"],
                "format": r["format"], "code_list": r["code_list"],
                "definition": r["definition"], "attr_upi": r["attr_upi"], "seq": r["seq"],
            }
            for r in ois
        ],
    )
