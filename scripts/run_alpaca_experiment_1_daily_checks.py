#!/usr/bin/env python3
"""
Run daily health checks for Alpaca Experiment #1: validate ledger, then break alert.
Analysis-only. Exits non-zero if break alert was sent (invalid or stale ledger).
No cron installation unless explicitly authorized.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATE = REPO / "scripts" / "validate_hypothesis_ledger_alpaca.py"
BREAK_NOTIFY = REPO / "scripts" / "notify_governance_experiment_alpaca_break.py"


def main() -> int:
    rv = subprocess.run([sys.executable, str(VALIDATE)], cwd=str(REPO), timeout=30)
    if rv.returncode != 0:
        # Ledger invalid; run break notify (sends Telegram), then exit non-zero
        subprocess.run([sys.executable, str(BREAK_NOTIFY)], cwd=str(REPO), timeout=60)
        return 1
    # Ledger valid; run break notify anyway (it only sends if invalid/stale)
    rv2 = subprocess.run([sys.executable, str(BREAK_NOTIFY)], cwd=str(REPO), timeout=60)
    # Break script exits 1 when it sent an alert, 0 when ledger OK, 2 on Telegram error
    if rv2.returncode == 1:
        return 1
    if rv2.returncode == 2:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
