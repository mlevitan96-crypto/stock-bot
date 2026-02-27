#!/usr/bin/env python3
"""
Summarize state/blocked_trades.jsonl by reason, UW quality bucket, and strategy/variant_id.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BLOCKED_PATH = REPO_ROOT / "state" / "blocked_trades.jsonl"


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def main():
    by_reason = defaultdict(lambda: {"count": 0, "expected_value_usd": 0.0, "uw_scores": []})
    by_strategy = defaultdict(lambda: {"count": 0, "reasons": defaultdict(int)})
    for rec in iter_jsonl(BLOCKED_PATH):
        reason = rec.get("reason") or rec.get("block_reason") or "unknown"
        by_reason[reason]["count"] += 1
        ev = rec.get("expected_value_usd")
        if ev is not None:
            try:
                by_reason[reason]["expected_value_usd"] += float(ev)
            except (TypeError, ValueError):
                pass
        q = rec.get("uw_signal_quality_score")
        if q is not None:
            by_reason[reason]["uw_scores"].append(float(q))
        strategy = rec.get("strategy") or rec.get("variant_id") or "unknown"
        by_strategy[strategy]["count"] += 1
        by_strategy[strategy]["reasons"][reason] += 1
    print("=== By reason ===")
    for reason in sorted(by_reason.keys(), key=lambda r: -by_reason[r]["count"]):
        d = by_reason[reason]
        avg_uw = sum(d["uw_scores"]) / len(d["uw_scores"]) if d["uw_scores"] else None
        if avg_uw is not None:
            print(f"  {reason}: count={d['count']}, expected_value_usd={d['expected_value_usd']:.2f}, avg_uw_quality={avg_uw:.2f}")
        else:
            print(f"  {reason}: count={d['count']}, expected_value_usd={d['expected_value_usd']:.2f}")
    print("\n=== By strategy/variant_id ===")
    for strategy in sorted(by_strategy.keys(), key=lambda s: -by_strategy[s]["count"]):
        d = by_strategy[strategy]
        print(f"  {strategy}: count={d['count']}, reasons={dict(d['reasons'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
