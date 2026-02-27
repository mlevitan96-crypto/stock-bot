#!/usr/bin/env python3
"""Run resume script with bash -x on droplet and fetch trace log. Observe only."""
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
        # Run with -x and capture; use bash -c so we get one shell with set -Eeuo pipefail and -x
        cmd = (
            f"cd {ROOT} && "
            "bash -x scripts/enable_alpaca_bars_resume.sh "
            "> reports/bars/interactive_trace.log 2>&1; echo TRACE_EXIT=$?"
        )
        c._execute(cmd, timeout=120)
        out, _, _ = c._execute(f"tail -300 {ROOT}/reports/bars/interactive_trace.log 2>/dev/null; true", timeout=10)
        grep_out, _, _ = c._execute(
            f"grep -n 'Resume Phase 3' {ROOT}/reports/bars/interactive_trace.log 2>/dev/null || true", timeout=5
        )
    print("--- grep 'Resume Phase 3' ---")
    print(grep_out or "(none)")
    print("")
    print("--- tail -300 interactive_trace.log ---")
    print(out or "(empty)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
