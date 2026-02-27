#!/usr/bin/env python3
"""Fetch head and tail of fetch_debug.log and tail of nohup_run.log and trace log."""
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
        h, _, _ = c._execute(f"head -80 {ROOT}/reports/bars/fetch_debug.log 2>/dev/null", timeout=5)
        t, _, _ = c._execute(f"grep -n 'ERR\\|Incomplete\\|failed\\|Error\\|Traceback' {ROOT}/reports/bars/fetch_debug.log 2>/dev/null | tail -30", timeout=5)
        n, _, _ = c._execute(f"tail -150 {ROOT}/reports/bars/nohup_run.log 2>/dev/null", timeout=5)
        tr, _, _ = c._execute(f"tail -80 {ROOT}/reports/bars/interactive_trace_after_fix.log 2>/dev/null", timeout=5)
    print("=== fetch_debug.log head (80) ===")
    print(h or "(empty)")
    print("\n=== fetch_debug.log grep ERR/Incomplete/failed/Error/Traceback (last 30) ===")
    print(t or "(none)")
    print("\n=== nohup_run.log tail (150) ===")
    print(n or "(empty)")
    print("\n=== interactive_trace_after_fix.log tail (80) ===")
    print(tr or "(empty)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
