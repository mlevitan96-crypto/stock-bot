#!/usr/bin/env python3
"""
DEPRECATED (2026-03-30): Removes legacy notify_alpaca_trade_milestones crontab lines only.

Install: ``bash scripts/install_alpaca_telegram_integrity_on_droplet.sh``
"""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        existing = result.stdout if result.returncode == 0 else ""
    except Exception:
        existing = ""

    lines = [
        l
        for l in existing.split("\n")
        if l.strip() and "notify_alpaca_trade_milestones" not in l
    ]
    new_crontab = "\n".join(lines) + ("\n" if lines else "")
    r2 = subprocess.run(["crontab", "-"], input=new_crontab, text=True, capture_output=True)
    if r2.returncode != 0:
        print(f"Error updating crontab: {r2.stderr}", file=sys.stderr)
        return 1
    print(
        "Removed notify_alpaca_trade_milestones from crontab (if present). "
        "Use systemd: scripts/install_alpaca_telegram_integrity_on_droplet.sh"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
