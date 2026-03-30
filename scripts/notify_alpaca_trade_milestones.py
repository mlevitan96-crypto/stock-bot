#!/usr/bin/env python3
"""
DEPRECATED (2026-03-30): use ``scripts/run_alpaca_telegram_integrity_cycle.py`` via
``alpaca-telegram-integrity.timer``. Milestones are 250 unique closes since regular
session open (canonical ``trade_key``), not promotion-based 100/500 counts.

Cron lines invoking this file must be removed on the droplet.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Deprecated Alpaca milestone stub")
    ap.add_argument("--mock-count", type=int, help="Ignored")
    ap.parse_args()
    print(
        "notify_alpaca_trade_milestones.py: DEPRECATED — "
        "use systemd alpaca-telegram-integrity.timer + "
        "scripts/run_alpaca_telegram_integrity_cycle.py",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
