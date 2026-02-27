#!/usr/bin/env python3
"""Baseline composite backtest. Wrapper: calls run_30d_backtest_droplet.py with --out. Droplet only."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", default=None)
    ap.add_argument("--config", default=None)
    ap.add_argument("--lab-mode", action="store_true")
    ap.add_argument("--walkforward", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # Invoke run_30d_backtest_droplet with --out <baseline_dir>
    import subprocess
    rc = subprocess.call(
        [sys.executable, str(REPO / "scripts" / "run_30d_backtest_droplet.py"), "--out", str(out)],
        cwd=str(REPO),
    )
    return rc


if __name__ == "__main__":
    sys.exit(main())
