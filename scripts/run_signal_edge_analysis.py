#!/usr/bin/env python3
"""
Run signal edge analysis on a backtest directory.
Produces SIGNAL_EDGE_ANALYSIS_REPORT.md in that directory.

Usage:
  python scripts/run_signal_edge_analysis.py --backtest-dir backtests/30d_after_signal_engine_block3d_YYYYMMDD_HHMMSS/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    p = argparse.ArgumentParser(description="Run signal edge analysis on backtest dir")
    p.add_argument("--backtest-dir", "-d", required=True, help="Path to backtest directory")
    args = p.parse_args()
    backtest_dir = Path(args.backtest_dir)
    if not backtest_dir.is_absolute():
        backtest_dir = REPO_ROOT / backtest_dir
    if not backtest_dir.is_dir():
        print(f"Error: not a directory: {backtest_dir}", file=sys.stderr)
        return 1

    try:
        from src.analysis.signal_edge_analysis import run_analysis, render_markdown_report
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    data = run_analysis(backtest_dir)
    report = render_markdown_report(data, backtest_dir)
    out_path = backtest_dir / "SIGNAL_EDGE_ANALYSIS_REPORT.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
