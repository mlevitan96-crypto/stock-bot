#!/usr/bin/env python3
"""
Run ON THE DROPLET. Reads the last 10 blocked trades from state/blocked_trades.jsonl
and prints why they didn't reach minimum score (score vs min_required, reason, components).
Use to diagnose signal/score issues when trades aren't executing.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BLOCKED_PATH = REPO / "state" / "blocked_trades.jsonl"
MIN_EXEC_DEFAULT = 2.5


def main() -> int:
    if not BLOCKED_PATH.exists():
        print("state/blocked_trades.jsonl not found (no blocked trades recorded yet).")
        return 0

    lines = []
    with open(BLOCKED_PATH, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(line)

    last_n = 10
    records = []
    for line in lines[-last_n:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not records:
        print("No valid records in state/blocked_trades.jsonl")
        return 0

    min_exec = float(os.environ.get("MIN_EXEC_SCORE", str(MIN_EXEC_DEFAULT)))

    print("=" * 80)
    print("LAST 10 TRADES THAT DID NOT REACH EXECUTION (blocked_trades.jsonl)")
    print("=" * 80)
    print(f"Min exec score (env MIN_EXEC_SCORE or default): {min_exec}")
    print()

    for i, rec in enumerate(reversed(records), 1):
        symbol = rec.get("symbol", "?")
        reason = rec.get("reason") or rec.get("block_reason") or "unknown"
        score = rec.get("score") or rec.get("candidate_score")
        try:
            score_f = float(score) if score is not None else None
        except (TypeError, ValueError):
            score_f = None
        min_required = rec.get("min_required")
        if min_required is None:
            min_required = min_exec
        try:
            min_f = float(min_required)
        except (TypeError, ValueError):
            min_f = min_exec
        gap = (min_f - score_f) if score_f is not None else None
        ts = rec.get("timestamp") or rec.get("ts") or ""
        direction = rec.get("direction") or rec.get("side") or ""

        print(f"--- Blocked #{i}: {symbol} ({direction}) ---")
        print(f"  Reason:        {reason}")
        print(f"  Score:         {score_f if score_f is not None else score}")
        print(f"  Min required:  {min_f}")
        if gap is not None:
            print(f"  Gap (short):   {gap:.3f}")
        print(f"  Timestamp:     {ts}")

        # Components (from composite_meta or components)
        meta = rec.get("composite_meta") or rec.get("metadata") or {}
        comps = meta.get("components") if isinstance(meta, dict) else rec.get("components")
        if isinstance(comps, dict) and comps:
            print("  Score components (key signals):")
            for k in ("options_flow", "flow_conviction", "flow_conv", "dark_pool", "insider", "event_alignment", "freshness", "congress", "shorts_squeeze"):
                v = comps.get(k)
                if v is not None:
                    try:
                        print(f"    {k}: {float(v):.3f}" if isinstance(v, (int, float)) else f"    {k}: {v}")
                    except (TypeError, ValueError):
                        print(f"    {k}: {v}")
            # If no known keys, show first 8 entries
            shown = [k for k in comps if k in ("options_flow", "flow_conviction", "flow_conv", "dark_pool", "insider", "event_alignment", "freshness", "congress", "shorts_squeeze")]
            if not shown and comps:
                for k, v in list(comps.items())[:8]:
                    print(f"    {k}: {v}")

        # Expectancy gate detail if present
        if "expectancy_blocked" in str(reason):
            gate_reason = rec.get("gate_reason") or rec.get("expectancy_gate_reason") or ""
            if gate_reason:
                print(f"  Expectancy gate: {gate_reason}")

        print()

    print("=" * 80)
    print("If score is consistently below min_required, check: conviction/sentiment in cache,")
    print("adaptive weights (DISABLE_ADAPTIVE_WEIGHTS=1), and signal ingestion (see SIGNAL_INGESTION_AUDIT.md).")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
