#!/usr/bin/env python3
"""Fetch cursor one-shot summary and log tail from droplet."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient

def main():
    c = DropletClient()
    pd = c.project_dir or "/root/stock-bot"
    path = f"{pd}/reports/backtests/promotion_candidate_1_check/cursor_final_summary.txt"
    out, err, rc = c._execute(f"cat {path}", timeout=15)
    print("--- cursor_final_summary.txt ---")
    print(out or err)
    out2, _, _ = c._execute("tail -60 /tmp/cursor_full_automated_orchestrator_runall.log", timeout=10)
    print("--- log tail ---")
    print(out2 or "")

if __name__ == "__main__":
    main()
