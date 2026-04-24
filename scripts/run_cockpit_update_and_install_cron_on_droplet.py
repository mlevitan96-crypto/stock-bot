#!/usr/bin/env python3
"""Run update_profitability_cockpit.py on the droplet and install hourly cockpit refresh cron (14-21 UTC weekdays)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def detect_stockbot_root(client) -> str:
    """Detect stock-bot root on droplet: prefer stock-bot-current, fallback stock-bot."""
    cmd = (
        "ROOT=/root/stock-bot; "
        "[ -d /root/stock-bot-current/scripts ] && [ -d /root/stock-bot-current/config ] "
        "&& [ -f /root/stock-bot-current/scripts/update_profitability_cockpit.py ] "
        "&& ROOT=/root/stock-bot-current; echo $ROOT"
    )
    out, _, _ = client._execute(cmd, timeout=5)
    return (out or "").strip() or "/root/stock-bot"


def main() -> int:
    from droplet_client import DropletClient

    c = DropletClient()
    root = detect_stockbot_root(c)
    print("=== Droplet: Profitability Cockpit update and cron install ===")
    print(f"Repo root: {root}\n")

    # 1. Run cockpit update (full output)
    print("--- 1. Running update_profitability_cockpit.py ---")
    cmd1 = f"cd {root} && python3 scripts/update_profitability_cockpit.py 2>&1"
    out1, err1, rc1 = c._execute(cmd1, timeout=60)
    print(out1 or "(no stdout)")
    if err1:
        print("stderr:", err1)
    print(f"Exit code: {rc1}\n")

    # 2. Ensure logs dir exists for cron
    c._execute(f"mkdir -p {root}/logs", timeout=5)

    # 3. Add cockpit refresh cron (hourly 14-21 UTC weekdays), avoid duplicate
    cockpit_line = (
        f"0 14-21 * * 1-5 cd {root} && python3 scripts/update_profitability_cockpit.py >> {root}/logs/cockpit_refresh.log 2>&1"
    )
    cockpit_escaped = cockpit_line.replace("'", "'\"'\"'")
    install = (
        "(crontab -l 2>/dev/null | grep -v 'update_profitability_cockpit' | grep -v 'cockpit_refresh' || true; "
        f"printf '%s\\n' '{cockpit_escaped}') | crontab -"
    )
    print("--- 2. Installing cockpit refresh cron (0 14-21 * * 1-5) ---")
    out2, err2, rc2 = c._execute(install, timeout=10)
    if out2:
        print("stdout:", out2)
    if err2:
        print("stderr:", err2)
    print(f"Exit code: {rc2}\n")

    # 4. Show crontab
    print("--- 3. Current crontab ---")
    out3, err3, rc3 = c._execute("crontab -l 2>/dev/null || echo '(empty)'", timeout=5)
    print(out3 or err3 or "(none)")

    c.close()
    return 0 if rc1 == 0 else rc1


if __name__ == "__main__":
    sys.exit(main())
