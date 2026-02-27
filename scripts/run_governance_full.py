#!/usr/bin/env python3
"""Governance check for backtest run. Calls backtest_governance_check.py. Droplet only."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backtest", required=True, help="Backtest summary dir or run dir (e.g. reports/backtests/<RUN_ID>)")
    ap.add_argument("--out", required=True, help="Governance output dir (e.g. reports/governance/<RUN_ID>)")
    args = ap.parse_args()
    backtest_dir = Path(args.backtest)
    if not backtest_dir.is_absolute():
        backtest_dir = REPO / backtest_dir
    # If --backtest points to summary subdir, use parent as run dir (provenance/config live in run dir)
    if backtest_dir.name == "summary":
        run_dir = backtest_dir.parent
    elif (backtest_dir / "summary.md").exists():
        run_dir = backtest_dir
    else:
        run_dir = backtest_dir
    import subprocess
    return subprocess.call(
        [
            sys.executable,
            str(REPO / "scripts" / "backtest_governance_check.py"),
            "--backtest-dir", str(run_dir),
            "--governance-out", args.out,
        ],
        cwd=str(REPO),
    )


if __name__ == "__main__":
    sys.exit(main())
