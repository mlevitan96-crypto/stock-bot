#!/usr/bin/env python3
"""Install EOD cron job on droplet: weekdays 21:30 UTC. Path-agnostic (stock-bot-current, stock-bot)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def detect_stockbot_root(client) -> str:
    """Detect stock-bot root on droplet: prefer stock-bot-current, fallback stock-bot."""
    cmd = (
        "ROOT=/root/stock-bot; "
        "[ -d /root/stock-bot-current/scripts ] && [ -d /root/stock-bot-current/config ] "
        "&& [ -f /root/stock-bot-current/board/eod/run_stock_quant_officer_eod.py ] "
        "&& ROOT=/root/stock-bot-current; echo $ROOT"
    )
    out, _, _ = client._execute(cmd, timeout=5)
    return (out or "").strip() or "/root/stock-bot"


def main() -> int:
    from droplet_client import DropletClient

    c = DropletClient()
    root = detect_stockbot_root(c)
    cron_line = (
        f"30 21 * * 1-5 cd {root} && "
        "CLAWDBOT_SESSION_ID=\"stock_quant_eod_$(date -u +\\%Y-\\%m-\\%d)\" "
        f"/usr/bin/python3 board/eod/run_stock_quant_officer_eod.py >> {root}/logs/cron_eod.log 2>&1"
    )
    # Ensure logs dir exists
    c._execute(f"mkdir -p {root}/logs", timeout=5)

    # (crontab -l | grep -v run_stock_quant_officer_eod; echo 'LINE') | crontab -
    # Escape single quotes in cron_line for shell
    cron_escaped = cron_line.replace("'", "'\"'\"'")
    install = (
        "(crontab -l 2>/dev/null | grep -v 'run_stock_quant_officer_eod' || true; "
        f"printf '%s\\n' '{cron_escaped}') | crontab -"
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
