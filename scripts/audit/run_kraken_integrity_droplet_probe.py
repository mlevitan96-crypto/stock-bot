#!/usr/bin/env python3
"""Read-only probe for Kraken integrity audit. Prints to stdout (UTF-8)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from droplet_client import DropletClient  # noqa: E402


def main() -> None:
    c = DropletClient()
    cmds = [
        "find /root -maxdepth 5 -name unified_events.jsonl 2>/dev/null | head -20",
        "find /root -maxdepth 5 -type d -iname '*kraken*' 2>/dev/null | head -20",
        "ls /root/stock-bot/logs/*.jsonl 2>/dev/null | wc -l",
        (
            "for f in /root/stock-bot/logs/exit_attribution.jsonl "
            "/root/stock-bot/logs/attribution.jsonl "
            "/root/stock-bot/logs/master_trade_log.jsonl "
            "/root/stock-bot/logs/alpaca_unified_events.jsonl "
            "/root/stock-bot/logs/submit_entry.jsonl; do "
            'echo -n "$f "; test -f "$f" && wc -l "$f" || echo MISSING; done'
        ),
        "systemctl is-active stock-bot 2>/dev/null; echo ---; crontab -l 2>/dev/null | head -25",
        "df -h / /root 2>/dev/null; echo INODES; df -i / 2>/dev/null | tail -2",
        "test -f /root/stock-bot/deploy_supervisor.py && grep -c RETENTION_PROTECTED_BASENAMES /root/stock-bot/deploy_supervisor.py || echo no_supervisor",
        "stat -c '%y %s' /root/stock-bot/logs/exit_attribution.jsonl 2>/dev/null || echo no_exit_attr",
        "tail -1 /root/stock-bot/logs/exit_attribution.jsonl 2>/dev/null | head -c 500 || true",
    ]
    for cmd in cmds:
        out, err, rc = c._execute(cmd, timeout=120)
        print("===", cmd[:120], "rc=", rc)
        print(out or err or "(empty)")


if __name__ == "__main__":
    main()
