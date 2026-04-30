#!/usr/bin/env python3
"""
Chen-style kill-chain: last 10 Alpaca trade_intent rows with v2_agent_veto.

For each, reports v2_row_nan_fraction and counts null keys inside persisted v2_ml_row (if present).

Run on droplet:
  cd /root/stock-bot && PYTHONPATH=. python3 scripts/debug/v2_killchain_last10.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main() -> int:
    p = REPO / "logs" / "run.jsonl"
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
    if not p.is_file():
        print("missing", p, file=sys.stderr)
        return 2
    vetoes = []
    for line in p.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("event_type") != "trade_intent":
            continue
        if (r.get("decision_outcome") or "").lower() != "blocked":
            continue
        if "v2_agent_veto" not in str(r.get("blocked_reason") or ""):
            continue
        vetoes.append(r)
    tail = vetoes[-10:]
    print("v2_agent_veto rows (up to 10):", len(tail))
    for r in tail:
        mr = r.get("v2_ml_row")
        nulls = sum(1 for _k, v in (mr or {}).items() if v is None) if isinstance(mr, dict) else -1
        print(
            r.get("ts"),
            r.get("symbol"),
            "nan_frac",
            r.get("v2_row_nan_fraction"),
            "v2_ml_row_null_fields",
            nulls,
            "proba",
            r.get("v2_live_gate_proba"),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
