#!/usr/bin/env python3
"""
SRE: Scan repo for where trade ledgers are written and which fields exist.
Read-only; outputs emission points and inferred schema for CSA contract alignment.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan ledger emission points")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    if not root.exists():
        print(f"Repo root missing: {root}", file=sys.stderr)
        return 2

    emission_points = []
    # Known writers of FULL_TRADE_LEDGER or executed[] structure
    candidates = [
        ("scripts/audit/reconstruct_full_trade_ledger.py", "reconstruct", ["ts", "ts_iso", "symbol", "direction", "strategy_variant_id", "decision", "exit_reason", "hold_time_minutes", "realized_pnl", "realized_pnl_pct", "sizing", "entry_ts", "exit_ts"]),
        ("scripts/counter_intel/merge_counter_intel_into_ledger.py", "merge_counter_intel", ["executed", "blocked", "counter_intel"]),
    ]
    for rel_path, role, fields in candidates:
        p = root / rel_path
        if p.exists():
            emission_points.append({
                "path": str(p.resolve()),
                "role": role,
                "inferred_fields": fields,
                "writes": "ledger JSON" if "reconstruct" in role else "ledger in place",
            })

    # Grep for other references to ledger output
    for py in root.rglob("*.py"):
        if "test" in str(py) or "__pycache__" in str(py):
            continue
        try:
            text = py.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "FULL_TRADE_LEDGER" in text or ("executed" in text and "ledger" in text and "write" in text):
            if not any(ep["path"] == str(py.resolve()) for ep in emission_points):
                emission_points.append({
                    "path": str(py.resolve()),
                    "role": "reference",
                    "inferred_fields": [],
                    "writes": "reference only",
                })
        if len(emission_points) > 30:
            break

    out = {
        "repo_root": str(root),
        "emission_point_count": len(emission_points),
        "emission_points": emission_points,
        "current_executed_fields": ["ts", "ts_iso", "symbol", "direction", "strategy_variant_id", "decision", "exit_reason", "hold_time_minutes", "realized_pnl", "realized_pnl_pct", "sizing", "entry_ts", "exit_ts"],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("SRE scan:", len(emission_points), "emission points")
    return 0


if __name__ == "__main__":
    sys.exit(main())
