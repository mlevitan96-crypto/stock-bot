#!/usr/bin/env python3
"""Install Molt workflow cron on droplet (post-market 21:35 UTC weekdays)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

REMOTE_ROOT = "/root/stock-bot"
CRON_LINE = "35 21 * * 1-5 cd /root/stock-bot && REPO_DIR=/root/stock-bot bash scripts/run_molt_on_droplet.sh >> logs/molt_cron.log 2>&1"


def main() -> int:
    from droplet_client import DropletClient
    client = DropletClient()
    try:
        ssh = client._connect()
    except Exception as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1
    out, err, rc = client._execute(f"(crontab -l 2>/dev/null | grep -v run_molt_on_droplet; echo '{CRON_LINE}') | crontab -", timeout=10)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    print("Molt cron installed (21:35 UTC weekdays).")
    client.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
