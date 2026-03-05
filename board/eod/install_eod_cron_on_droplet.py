#!/usr/bin/env python3
"""Install EOD + sync cron jobs on droplet: EOD 21:30 UTC, sync 21:32 UTC weekdays. Path-agnostic (stock-bot-current, stock-bot)."""
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
    # EOD: 21:30 UTC weekdays (Memory Bank §5.5)
    eod_line = (
        f"30 21 * * 1-5 cd {root} && "
        f"/usr/bin/python3 board/eod/run_stock_quant_officer_eod.py >> {root}/logs/cron_eod.log 2>&1"
    )
    # Sync: 21:32 UTC weekdays — prefer run_droplet_audit_and_sync.sh, else droplet_sync_to_github.sh
    sync_script = "run_droplet_audit_and_sync.sh" if (REPO / "scripts" / "run_droplet_audit_and_sync.sh").exists() else "droplet_sync_to_github.sh"
    sync_line = (
        f"32 21 * * 1-5 cd {root} && bash scripts/{sync_script} >> {root}/logs/cron_sync.log 2>&1"
    )

    c._execute(f"mkdir -p {root}/logs", timeout=5)

    # Remove old stock-bot EOD/sync lines and install both EOD and sync
    eod_escaped = eod_line.replace("'", "'\"'\"'")
    sync_escaped = sync_line.replace("'", "'\"'\"'")
    install = (
        "(crontab -l 2>/dev/null | grep -v 'run_stock_quant_officer_eod' | grep -v 'droplet_sync_to_github' | grep -v 'run_droplet_audit_and_sync' || true; "
        f"printf '%s\\n' '{eod_escaped}' '{sync_escaped}') | crontab -"
    )
    print("=== Installing EOD (21:30) + sync (21:32) cron jobs ===")
    print(f"Sync script: {sync_script}")
    out, err, rc = c._execute(install, timeout=10)
    print("stdout:", out or "(none)")
    print("stderr:", err or "(none)")
    print("exit:", rc)
    if rc != 0:
        c.close()
        return rc
    print("\n=== crontab -l ===")
    out2, err2, rc2 = c._execute("crontab -l", timeout=5)
    print(out2 or err2)
    print("exit:", rc2)
    c.close()
    return rc2


if __name__ == "__main__":
    sys.exit(main())
