#!/usr/bin/env python3
"""Add rolling PnL cron and run update script twice on droplet. Run after deploy."""
import sys
from pathlib import Path
if str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from droplet_client import DropletClient

def main():
    c = DropletClient()
    # Check if cron already present
    out, err, rc = c._execute_with_cd(
        "crontab -l 2>/dev/null | grep -q update_rolling_pnl_5d && echo already || echo missing"
    )
    if out and "already" in out:
        print("Cron for rolling_pnl_5d already present.")
    else:
        cron_line = "*/10 * * * * cd /root/stock-bot && /root/stock-bot/venv/bin/python scripts/performance/update_rolling_pnl_5d.py >> logs/rolling_pnl_5d.log 2>&1"
        r = c.execute_command(
            "(crontab -l 2>/dev/null; echo '" + cron_line + "') | crontab -"
        )
        print("Cron add:", "OK" if r.get("success") else r.get("stderr", r.get("stdout")))

    # Run script twice (idempotence)
    for i in range(2):
        r = c.execute_command(
            "/root/stock-bot/venv/bin/python scripts/performance/update_rolling_pnl_5d.py",
            timeout=30,
        )
        print("Run", i + 1, ":", "OK" if r.get("success") else r.get("stderr") or r.get("stdout"))

    # Verify
    r = c.execute_command(
        "wc -l reports/state/rolling_pnl_5d.jsonl 2>/dev/null; echo '---'; crontab -l | grep update_rolling_pnl_5d"
    )
    print("Verify:", r.get("stdout", "") or r.get("stderr"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
