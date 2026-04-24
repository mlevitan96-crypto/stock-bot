#!/usr/bin/env python3
"""
Runtime: Apply ledger schema patch (paper-only). Adds logging field requirements only.
Does not modify trading behavior; documents applied plan for paper emission to conform to.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply ledger schema patch (paper logging only)")
    ap.add_argument("--mode", default="paper", choices=("paper",))
    ap.add_argument("--plan", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    plan_path = Path(args.plan)
    if not plan_path.exists():
        print(f"Plan missing: {plan_path}", file=sys.stderr)
        return 2

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    applied = {
        "applied": True,
        "mode": args.mode,
        "plan_path": str(plan_path.resolve()),
        "fields_added": [f["key"] for f in plan.get("fields_to_add", [])],
        "note": "Paper ledger emission shall include these fields when writing executed/blocked events. No behavior change; logging only.",
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(applied, indent=2, default=str), encoding="utf-8")
    print("Patch applied:", len(applied["fields_added"]), "fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
