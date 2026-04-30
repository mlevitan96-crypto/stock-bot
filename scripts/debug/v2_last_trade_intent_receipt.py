#!/usr/bin/env python3
"""Last trade_intent line summary (Dense DNA receipt). Optional path: argv[1] = run.jsonl."""
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
    last = None
    for line in p.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("event_type") == "trade_intent":
            last = r
    if not last:
        print("NO_TRADE_INTENT")
        return 1
    mr = last.get("v2_ml_row") or {}
    nkeys = len(mr) if isinstance(mr, dict) else 0
    nulls = sum(1 for _k, v in mr.items() if v is None) if isinstance(mr, dict) else -1
    print("ts", last.get("ts"))
    print("symbol", last.get("symbol"), "side", last.get("side"), "score", last.get("score"))
    print("decision_outcome", last.get("decision_outcome"))
    print("blocked_reason", str(last.get("blocked_reason") or "")[:240])
    print("v2_row_nan_fraction", last.get("v2_row_nan_fraction"), "v2_row_nan_count", last.get("v2_row_nan_count"))
    print("v2_live_gate_proba", last.get("v2_live_gate_proba"), "v2_live_gate_threshold", last.get("v2_live_gate_threshold"))
    print("v2_ml_row_keys", nkeys, "v2_ml_row_null_fields", nulls)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
