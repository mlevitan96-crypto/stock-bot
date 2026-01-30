#!/usr/bin/env python3
"""Install EOD cron job on droplet: weekdays 21:30 UTC. Verify with crontab -l."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

CRON_LINE = (
    "30 21 * * 1-5 cd /root/stock-bot && CLAWDBOT_SESSION_ID=\"stock_quant_eod_$(date -u +%Y-%m-%d)\" "
    "/usr/bin/python3 board/eod/run_stock_quant_officer_eod.py >> /root/stock-bot/cron_eod.log 2>&1"
)


def main() -> int:
    from droplet_client import DropletClient

    c = DropletClient()
    # (crontab -l | grep -v run_stock_quant_officer_eod; echo 'LINE') | crontab -
    install = (
        "(crontab -l 2>/dev/null | grep -v 'run_stock_quant_officer_eod' || true; "
        f"printf '%s\\n' '{CRON_LINE}') | crontab -"
    )
    print("=== Installing cron job ===")
    out, err, rc = c._execute(install, timeout=10)
    print("stdout:", out or "(none)")
    print("stderr:", err or "(none)")
    print("exit:", rc)
    if rc != 0:
        return rc
    print("\n=== crontab -l ===")
    out2, err2, rc2 = c._execute("crontab -l", timeout=5)
    print(out2 or err2)
    print("exit:", rc2)
    c.close()
    return rc2


if __name__ == "__main__":
    sys.exit(main())
