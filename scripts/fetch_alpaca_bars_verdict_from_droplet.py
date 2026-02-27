#!/usr/bin/env python3
"""
Fetch and print the Alpaca bars final verdict from the droplet (short SSH).
Authoritative source: reports/bars/final_verdict.txt.
Optional: --debug to also tail reports/bars/fetch_debug.log
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

ROOT = "/root/stock-bot"


def safe_print(text: str, file=None) -> None:
    if not text:
        return
    safe = text.replace("\u2192", "->").replace("\u2014", "-").encode("ascii", errors="replace").decode("ascii")
    (file or sys.stdout).write(safe)
    if not safe.endswith("\n"):
        (file or sys.stdout).write("\n")
    (file or sys.stdout).flush()


def main() -> int:
    ap = argparse.ArgumentParser(description="Cat final_verdict.txt from droplet; optional tail fetch_debug.log")
    ap.add_argument("--debug", action="store_true", help="Also tail -200 reports/bars/fetch_debug.log")
    args = ap.parse_args()
    from droplet_client import DropletClient

    with DropletClient() as c:
        c._execute("true", timeout=5)
        verdict, _, _ = c._execute(f"cat {ROOT}/reports/bars/final_verdict.txt 2>/dev/null; true", timeout=10)
        safe_print("========== FINAL VERDICT (authoritative) ==========")
        if (verdict or "").strip():
            safe_print(verdict.strip())
        else:
            safe_print("(file missing or empty — run may still be in progress)")
        safe_print("====================================================")
        if args.debug:
            debug_out, _, _ = c._execute(f"tail -200 {ROOT}/reports/bars/fetch_debug.log 2>/dev/null; true", timeout=10)
            if (debug_out or "").strip():
                safe_print("")
                safe_print("--- tail reports/bars/fetch_debug.log ---", file=sys.stderr)
                safe_print(debug_out.strip(), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
