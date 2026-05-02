#!/usr/bin/env python3
"""
Monday open reset — cancel all open orders and flatten Alpaca positions at **09:30:05 America/New_York**.

Governance:
  - **Stop** ``stock-bot.service`` before production use so the trading loop does not race this script.
  - Invokes the same broker actions as ``scripts/liquidate_all.py`` (cancel_all_orders + close_all_positions).

Environment:
  - ``MONDAY_OPEN_RESET_SKIP_ET_CHECK=1`` — allow run outside the Monday 09:30 ET window (dangerous; tests/ops only).

Exit codes: 0 success / no-op outside window, 2 missing creds, 1 broker failure.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
ET = ZoneInfo("America/New_York")


def _in_monday_open_window(now_et: datetime) -> bool:
    if now_et.weekday() != 0:
        return False
    if now_et.hour != 9 or now_et.minute != 30:
        return False
    if now_et.second < 5:
        return False
    return True


def main() -> int:
    os.chdir(REPO)
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))

    skip = os.getenv("MONDAY_OPEN_RESET_SKIP_ET_CHECK", "").strip().lower() in ("1", "true", "yes", "on")
    now_et = datetime.now(tz=ET)
    if not skip and not _in_monday_open_window(now_et):
        print(
            f"[monday_open_reset] Skip: not in Monday 09:30:05+ ET window (now_et={now_et.isoformat()}).",
            flush=True,
        )
        return 0

    print(f"[monday_open_reset] ARMED window OK at {now_et.isoformat()} — invoking liquidate_all.py", flush=True)
    cmd = [sys.executable, str(REPO / "scripts" / "liquidate_all.py")]
    r = subprocess.run(cmd, cwd=str(REPO))
    return int(r.returncode if r.returncode is not None else 1)


if __name__ == "__main__":
    raise SystemExit(main())
