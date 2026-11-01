#!/usr/bin/env python3
"""Run the complete WCO DM 4.3.0 build from the checked-in sources."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.chdir(ROOT)

import wco_model  # noqa: E402
import build_ontology  # noqa: E402
import package_audit  # noqa: E402
import build_profiles  # noqa: E402
import build_site_data  # noqa: E402


def main() -> None:
    model, lib, ois = wco_model.build_model(
        os.path.join(ROOT, "sources", "xlsx", "wco_lib_430.xlsx"),
        os.path.join(ROOT, "sources", "xlsx", "wco_ois_430.xlsx"),
        os.path.join(ROOT, "sources", "package-tree.json"),
    )
    wco_model.export_model(model, lib, ois, os.path.join(ROOT, "data"))
    print("model:", model["summary"])
    package_audit.main()
    build_profiles.build()
    build_ontology.build()
    build_site_data.build()
    print("done")


if __name__ == "__main__":
    main()
