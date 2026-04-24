#!/usr/bin/env python3
"""Install direction readiness check cron on droplet (every 5 min during market hours)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

REMOTE_ROOT = "/root/stock-bot"
# Every 5 min, 9–21 UTC (covers US market), Mon–Fri. Use venv python so cron has correct PATH.
CRON_LINE = "*/5 9-21 * * 1-5 cd /root/stock-bot && /root/stock-bot/venv/bin/python scripts/governance/check_direction_readiness_and_run.py >> logs/direction_readiness_cron.log 2>&1"


def main() -> int:
    from droplet_client import DropletClient
    with DropletClient() as client:
        # Remove any existing line for this script, add current line
        out, err, rc = client._execute(
            f"(crontab -l 2>/dev/null | grep -v check_direction_readiness_and_run; echo '{CRON_LINE}') | crontab -",
            timeout=10,
        )
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("Crontab install failed", file=sys.stderr)
            return rc
    print("Direction readiness cron installed (every 5 min, 9–21 UTC, Mon–Fri).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
