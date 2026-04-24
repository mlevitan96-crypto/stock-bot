#!/usr/bin/env python3
"""Check direction readiness state and cron log on droplet."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

def main() -> int:
    from droplet_client import DropletClient
    proj = "/root/stock-bot"
    with DropletClient() as c:
        out, _, _ = c._execute(f"cat {proj}/state/direction_readiness.json 2>/dev/null")
        print("Current direction_readiness.json:", out or "(missing)")
        out2, _, _ = c._execute(f"tail -40 {proj}/logs/direction_readiness_cron.log 2>/dev/null")
        print("--- direction_readiness_cron.log (last 40 lines) ---")
        print(out2 or "(no log or empty)")
        out3, _, _ = c._execute("crontab -l 2>/dev/null")
        print("--- crontab ---")
        print(out3 or "(empty)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
