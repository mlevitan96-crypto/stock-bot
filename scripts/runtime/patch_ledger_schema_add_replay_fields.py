#!/usr/bin/env python3
"""
Runtime: Produce a plan to add true-replay fields to ledger emission (paper-only).
Read-only; no code changes. Plan is consumed by apply_ledger_schema_patch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Plan ledger schema patch (replay fields)")
    ap.add_argument("--mode", default="paper", choices=("paper", "shadow"))
    ap.add_argument("--contract", required=True)
    ap.add_argument("--sre-scan", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    contract_path = Path(args.contract)
    sre_path = Path(args.sre_scan)
    if not contract_path.exists():
        print(f"Contract missing: {contract_path}", file=sys.stderr)
        return 2
    if not sre_path.exists():
        print(f"SRE scan missing: {sre_path}", file=sys.stderr)
        return 2

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    sre = json.loads(sre_path.read_text(encoding="utf-8"))
    required = contract.get("required_artifacts", [])
    ts_req = contract.get("timestamp_requirements", [])

    # Plan: add these keys to each executed/blocked event
    fields_to_add = []
    for a in required:
        if a == "signal_vectors":
            fields_to_add.append({"key": "signal_vectors", "type": "array", "description": "Per-signal contribution vector for rescoring"})
        elif a == "normalized_scores":
            fields_to_add.append({"key": "normalized_scores", "type": "object", "description": "Normalized score components [-1,1]"})
        elif a == "decision_timestamps":
            for ts in ts_req:
                fields_to_add.append({"key": ts, "type": "integer", "description": "Unix timestamp"})
        elif a == "entry_exit_reasons":
            fields_to_add.append({"key": "exit_reason", "type": "string", "description": "Exit reason code"})
            fields_to_add.append({"key": "entry_reason", "type": "string", "description": "Entry reason code"})

    plan = {
        "mode": args.mode,
        "contract_path": str(contract_path.resolve()),
        "sre_scan_path": str(sre_path.resolve()),
        "emission_points": [ep["path"] for ep in sre.get("emission_points", [])],
        "fields_to_add": fields_to_add,
        "apply_to": ["executed", "blocked"],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(plan, indent=2, default=str), encoding="utf-8")
    print("Patch plan:", len(plan["fields_to_add"]), "fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
