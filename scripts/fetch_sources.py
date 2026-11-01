#!/usr/bin/env python3
"""Download selected WCO DM 4.3.0 publication package files.

The public package view is backed by `GET /datamodel/infopage/4.3.0`,
which returns a flat tree with `relative` (directory, usually ending in /)
and `fileName`.  Static files are served below `/webpage/4.3.0/...`.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import ssl
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://datamodel.wcoomd.org/"
try:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:  # executed through exec() with no __file__
    ROOT = os.path.abspath(os.getcwd())
TREE = os.path.join(ROOT, "sources", "package-tree.json")
OUT = os.path.join(ROOT, "sources", "package")
MANIFEST = os.path.join(ROOT, "sources", "download-manifest.csv")

CTX = ssl._create_unverified_context()
HEADERS = {"User-Agent": "WCO-DM-ontology-builder/1.0 (research; contact: local)"}


def entries():
    data = json.load(open(TREE, encoding="utf-8"))["list"]
    stack = []
    for item in data:
        level = item.get("level", 0)
        stack = stack[:level]
        if item.get("isDir"):
            stack.append(item["fileName"])
            continue
        rel = item.get("relative") or ""
        name = item.get("fileName") or ""
        # The API stores a directory prefix in `relative`; normal files end in '/'.
        full = rel + name
        yield full.replace("\\", "/"), level


def wanted(path: str) -> tuple[bool, str]:
    p = path.lower()
    if p.endswith(".xlsx"):
        return True, "workbook"
    if p.endswith(".xsd"):
        # Skip the two multi-megabyte consolidated schemas here; they are
        # fetched separately by scripts/fetch_big_schemas.sh.
        if "overall information package (ois)/2.3 xml schema/ois/" in p:
            return False, "large consolidated OIS schema; not downloaded (covered by LIB/OIS workbooks)"
        if "3. declaration/1. bip/" in p:
            return False, "large consolidated Declaration BIP schema; not downloaded (covered by LIB/OIS workbooks)"
        return True, "schema"
    if p.endswith(".zip"):
        return False, "binary UML/HTML archive; not required for ontology build"
    return False, "not selected"


def local_name(path: str) -> str:
    # Drop the fixed prefix so the tree is readable locally.
    prefix = "webpage/4.3.0/download files - 2/"
    rel = path[len(prefix):] if path.startswith(prefix) else path
    return os.path.join(OUT, *[p for p in rel.split("/") if p not in ("", ".", "..")])


def fetch(url: str, dest: str, retries: int = 3) -> int:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    part = dest + ".part"
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=CTX, timeout=180) as r, open(part, "wb") as f:
                total = 0
                while True:
                    chunk = r.read(1024 * 256)
                    if not chunk:
                        break
                    f.write(chunk)
                    total += len(chunk)
            os.replace(part, dest)
            return total
        except Exception as exc:  # noqa: BLE001
            print(f"  retry {attempt}/{retries}: {exc}", flush=True)
            time.sleep(2 * attempt)
    if os.path.exists(part):
        os.remove(part)
    raise RuntimeError(f"failed: {url}")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    rows = []
    todo = []
    for path, level in entries():
        ok, reason = wanted(path)
        rows.append({"path": path, "selected": "yes" if ok else "no", "reason": reason})
        if ok:
            todo.append(path)
    print(f"selected {len(todo)} files", flush=True)
    results = []
    for i, path in enumerate(todo, 1):
        dest = local_name(path)
        url = BASE + urllib.parse.quote(path)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            size = os.path.getsize(dest)
            print(f"[{i}/{len(todo)}] cached {size:>9,}  {path}", flush=True)
        else:
            print(f"[{i}/{len(todo)}] fetch  {path}", flush=True)
            try:
                size = fetch(url, dest)
                print(f"           -> {size:>9,} bytes", flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"           !! {exc}", flush=True)
                results.append({"path": path, "url": url, "bytes": 0, "sha256": "", "status": f"error: {exc}"})
                continue
        results.append({"path": path, "url": url, "bytes": size, "sha256": sha256(dest), "status": "ok"})
        time.sleep(0.15)

    # The build scripts read the two core workbooks from sources/xlsx.
    # Copy them there after downloading the package tree.
    core_copies = [
        (os.path.join(OUT, "1. Library", "1.1 WCO DM LIB V4.3.0.xlsx"), os.path.join(ROOT, "sources", "xlsx", "wco_lib_430.xlsx")),
        (os.path.join(OUT, "2. Overall Information Package (OIS)", "2.1 DataModel", "WCO DM OIS_V4.3.0.xlsx"), os.path.join(ROOT, "sources", "xlsx", "wco_ois_430.xlsx")),
    ]
    for src, dst in core_copies:
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            print(f"core workbook -> {dst}", flush=True)

    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "url", "bytes", "sha256", "status"])
        w.writeheader()
        w.writerows(results)
    with open(os.path.join(ROOT, "sources", "package-tree.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "selected", "reason"])
        w.writeheader()
        w.writerows(rows)
    print(f"manifest: {MANIFEST}", flush=True)


if __name__ == "__main__":
    main()
