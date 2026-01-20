#!/usr/bin/env python3
"""
Premarket droplet runner (manual trigger).

Runs:
- build_daily_universe
- run_premarket_intel
- run_regression_checks (mock-safe)
Then syncs state/log tails locally under droplet_sync/YYYY-MM-DD/.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default today UTC)")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--no-pull", action="store_true")
    args = ap.parse_args()

    cmd = [sys.executable, "scripts/run_uw_intel_on_droplet.py"]
    if args.date:
        cmd += ["--date", args.date]
    if args.mock:
        cmd += ["--mock"]
    if args.no_pull:
        cmd += ["--no-pull"]
    # Note: run_uw_intel_on_droplet runs pre+post; this wrapper exists for operator convention.
    p = subprocess.run(cmd, capture_output=True, text=True)
    print(p.stdout.strip())
    if p.returncode != 0:
        print(p.stderr.strip())
    return int(p.returncode)


if __name__ == "__main__":
    raise SystemExit(main())

