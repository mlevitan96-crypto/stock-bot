#!/usr/bin/env python3
"""
Shadow: Stamp shortlist with artifact provenance (e.g. synthetic_backfill).
Epistemic honesty: callers know data source. Shadow-only; read + write to reports/shadow.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Stamp shortlist provenance")
    ap.add_argument("--shortlist", required=True)
    ap.add_argument("--provenance", required=True, help="e.g. synthetic_backfill")
    ap.add_argument("--notes", default="")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.shortlist)
    if not path.exists():
        print(f"Shortlist missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    data["artifact_provenance"] = args.provenance
    data["provenance_notes"] = args.notes or ""

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print("Stamped provenance:", args.provenance)
    return 0


if __name__ == "__main__":
    sys.exit(main())
