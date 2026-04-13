#!/usr/bin/env python3
"""
Install weekday 08:30 America/New_York cron for scripts/run_premarket_intel.py.

Designed to run ON the droplet (or any host) as root when crontab targets /root/stock-bot.
Idempotent: skips if an entry containing run_premarket_intel.py already exists.

Usage:
  sudo python3 scripts/install_premarket_cron_on_droplet.py

Optional:
  STOCK_BOT_ROOT=/path/to/stock-bot python3 scripts/install_premarket_cron_on_droplet.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _marker() -> str:
    return "scripts/run_premarket_intel.py"


def main() -> int:
    root = Path(os.environ.get("STOCK_BOT_ROOT", "/root/stock-bot")).resolve()
    py = os.environ.get("PREMARKET_PYTHON", "")
    if not py:
        vpy = root / "venv" / "bin" / "python3"
        py = str(vpy) if vpy.exists() else sys.executable
    log = os.environ.get("PREMARKET_LOG", "/var/log/premarket_intel.log")
    block = (
        f"CRON_TZ=America/New_York\n"
        f"30 8 * * 1-5 cd {root} && {py} scripts/run_premarket_intel.py >> {log} 2>&1\n"
    )
    try:
        r = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            check=False,
        )
        existing = (r.stdout or "") if r.returncode == 0 else ""
    except FileNotFoundError:
        print("crontab not available on this system", file=sys.stderr)
        return 1
    if _marker() in existing:
        print("premarket_intel cron already present; no change.")
        return 0
    new_crontab = (existing.rstrip() + "\n\n# stock-bot: Tier-1 premarket UW intel\n" + block).lstrip()
    p = subprocess.run(["crontab", "-"], input=new_crontab, text=True, capture_output=True)
    if p.returncode != 0:
        print(p.stderr or "crontab install failed", file=sys.stderr)
        return p.returncode or 1
    print("Installed premarket_intel weekday 08:30 America/New_York cron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
