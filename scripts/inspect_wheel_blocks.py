#!/usr/bin/env python3
"""
Summarize blocked trades by reason AND by strategy; highlight wheel blocks.
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
    by_reason = defaultdict(int)
    by_strategy = defaultdict(lambda: defaultdict(int))
    wheel_blocks = []
    for rec in iter_jsonl(BLOCKED_PATH):
        reason = rec.get("reason") or rec.get("block_reason") or "unknown"
        strategy = rec.get("strategy") or rec.get("variant_id") or "unknown"
        by_reason[reason] += 1
        by_strategy[strategy][reason] += 1
        if (strategy or "").lower() == "wheel" or "wheel" in (strategy or "").lower():
            wheel_blocks.append(rec)
    print("=== Blocked by reason ===")
    for reason in sorted(by_reason.keys(), key=lambda r: -by_reason[r]):
        print(f"  {reason}: {by_reason[reason]}")
    print("\n=== Blocked by strategy (then reason) ===")
    for strategy in sorted(by_strategy.keys()):
        for reason, count in sorted(by_strategy[strategy].items(), key=lambda x: -x[1]):
            print(f"  {strategy} / {reason}: {count}")
    if wheel_blocks:
        print(f"\n=== Wheel blocked: {len(wheel_blocks)} trade(s) ===")
        for r in wheel_blocks[:20]:
            print(f"  {r.get('symbol')} {r.get('reason')} score={r.get('score')}")
        if len(wheel_blocks) > 20:
            print(f"  ... and {len(wheel_blocks) - 20} more")
    else:
        print("\nNo blocked trades with strategy=wheel.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
