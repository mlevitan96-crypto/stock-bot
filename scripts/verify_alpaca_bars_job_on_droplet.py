#!/usr/bin/env python3
"""Verify detached Alpaca bars job state on droplet. Observe only; no restarts or mutation."""
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

        # CHECK 1 — PID liveness
        pid_out, _, _ = c._execute(
            f"cat {ROOT}/reports/bars/nohup_pid.txt 2>/dev/null; true", timeout=5
        )
        pid = (pid_out or "").strip()
        ps_out, _, _ = c._execute(
            f"ps -fp {pid} 2>/dev/null; true", timeout=5
        )
        alive_out, _, _ = c._execute(
            f"kill -0 {pid} 2>/dev/null && echo ALIVE || echo DEAD; true", timeout=5
        )
        pid_alive = "YES" if pid and (alive_out or "").strip() == "ALIVE" else "NO"

        # CHECK 2 — Fetch activity
        wc_out, _, _ = c._execute(
            f"wc -l {ROOT}/reports/bars/fetch_debug.log 2>/dev/null || echo 0", timeout=5
        )
        try:
            nlines = int((wc_out or "0").strip().split()[0])
        except Exception:
            nlines = 0
        ls_out, _, _ = c._execute(f"ls -lh {ROOT}/data/bars/ 2>/dev/null || true", timeout=5)
        phase3_started = "YES" if nlines > 5 or (ls_out and "parquet" in (ls_out or "")) else "NO"

        # CHECK 3 — nohup log tail
        tail_out, _, _ = c._execute(
            f"tail -200 {ROOT}/reports/bars/nohup_run.log 2>/dev/null || true", timeout=10
        )

    # Report
    print("--- CHECK 1: PID ---")
    print(f"PID from file: {pid or '(none)'}")
    print(ps_out or "(ps output empty)")
    print("")
    print("--- CHECK 2: Phase 3 ---")
    print(f"fetch_debug.log lines: {nlines}")
    print(ls_out or "(data/bars listing empty)")
    print("")
    print("--- CHECK 3: nohup_run.log (tail) ---")
    print((tail_out or "(empty)")[-4000:] if tail_out else "(empty)")
    print("")
    print("========================================================\nREPORT\n========================================================")
    print(f"PID alive: {pid_alive}")
    print(f"Phase 3 started: {phase3_started}")
    if pid_alive == "NO" or phase3_started == "NO":
        print("Likely cause if NO: early exit / script not invoked / permission or path issue")
    print("========================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
