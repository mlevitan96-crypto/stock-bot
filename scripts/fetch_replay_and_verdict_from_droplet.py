#!/usr/bin/env python3
"""Fetch replay_results.jsonl sample and verdict from droplet."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
ROOT = "/root/stock-bot"

def main() -> int:
    from droplet_client import DropletClient
    with DropletClient() as c:
        c._execute("true", timeout=5)
        verdict, _, _ = c._execute(f"cat {ROOT}/reports/bars/final_verdict.txt 2>/dev/null", timeout=5)
        replay, _, _ = c._execute(f"head -5 {ROOT}/reports/blocked_expectancy/replay_results.jsonl 2>/dev/null; wc -l {ROOT}/reports/blocked_expectancy/replay_results.jsonl 2>/dev/null", timeout=5)
        tail, _, _ = c._execute(f"tail -30 {ROOT}/reports/bars/nohup_run.log 2>/dev/null", timeout=5)
    print("=== final_verdict.txt ===")
    print(verdict or "(empty)")
    print("\n=== replay_results.jsonl (head 5 + wc) ===")
    print(replay or "(empty)")
    print("\n=== nohup_run.log tail (Phase 5) ===")
    print(tail or "(empty)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
