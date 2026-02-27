#!/usr/bin/env python3
"""
Supervise detached Alpaca bars run on droplet: poll until final_verdict.txt exists
and has non-zero size, then print verdict only. No restarts, no mutation, observe only.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

ROOT = "/root/stock-bot"
VERDICT_PATH = f"{ROOT}/reports/bars/final_verdict.txt"
POLL_INTERVAL = 45
MAX_WAIT_SEC = 3600  # 1 hour


def safe_print(text: str, file=None) -> None:
    if not text:
        return
    safe = text.replace("\u2192", "->").replace("\u2014", "-").encode("ascii", errors="replace").decode("ascii")
    (file or sys.stdout).write(safe)
    if not safe.endswith("\n"):
        (file or sys.stdout).write("\n")
    (file or sys.stdout).flush()


def main() -> int:
    from droplet_client import DropletClient

    deadline = time.monotonic() + MAX_WAIT_SEC
    while time.monotonic() < deadline:
        with DropletClient() as c:
            c._execute("true", timeout=5)
            out, _, rc = c._execute(f"test -s '{VERDICT_PATH}' && echo COMPLETE || echo PENDING", timeout=10)
        status = (out or "").strip()
        if status == "COMPLETE":
            break
        safe_print(f"Waiting for completion (verdict file not ready)... next check in {POLL_INTERVAL}s", file=sys.stderr)
        time.sleep(POLL_INTERVAL)

    with DropletClient() as c:
        c._execute("true", timeout=5)
        verdict, _, _ = c._execute(f"cat '{VERDICT_PATH}' 2>/dev/null; true", timeout=10)
        verdict = (verdict or "").strip()
        if not verdict:
            safe_print("(verdict file missing or empty after wait)", file=sys.stderr)
            return 1
        safe_print(verdict)
        if "BARS MISSING" in verdict:
            debug_out, _, _ = c._execute(f"tail -200 {ROOT}/reports/bars/fetch_debug.log 2>/dev/null; true", timeout=10)
            if (debug_out or "").strip():
                safe_print("", file=sys.stderr)
                safe_print("--- tail reports/bars/fetch_debug.log ---", file=sys.stderr)
                safe_print(debug_out.strip(), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
