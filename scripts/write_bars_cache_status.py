#!/usr/bin/env python3
"""
Phase 3: Ensure data/bars/alpaca_daily.parquet exists, non-empty, (symbol, date) indexed, deterministic.
Write reports/bars/cache_status.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

REPORT_DIR = REPO / "reports" / "bars"
REPORT_PATH = REPORT_DIR / "cache_status.md"
DEFAULT_PARQUET = REPO / "data" / "bars" / "alpaca_daily.parquet"


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=None, help="Parquet path (default data/bars/alpaca_daily.parquet)")
    args = ap.parse_args()
    path = Path(args.path) if args.path else DEFAULT_PARQUET

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        REPORT_PATH.write_text(
            "# Cache status\n\n**Status:** MISSING\n\nFile not found: " + str(path) + "\n",
            encoding="utf-8",
        )
        print("Cache status: MISSING")
        return 1
    import pandas as pd
    df = pd.read_parquet(path)
    if df.empty:
        REPORT_PATH.write_text("# Cache status\n\n**Status:** EMPTY\n\nParquet has no rows.\n", encoding="utf-8")
        print("Cache status: EMPTY")
        return 1
    if "symbol" not in df.columns or "date" not in df.columns:
        REPORT_PATH.write_text("# Cache status\n\n**Status:** INVALID\n\nMissing symbol/date columns.\n", encoding="utf-8")
        return 1
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    n = len(df)
    symbols = df["symbol"].nunique()
    dates = df["date"].astype(str).unique()
    date_min, date_max = min(dates), max(dates)
    lines = [
        "# Cache status",
        "",
        "**Status:** READY",
        "",
        "| Item | Value |",
        "|------|-------|",
        f"| Path | {path} |",
        f"| Rows | {n} |",
        f"| Symbols | {symbols} |",
        f"| Date range | {date_min} to {date_max} |",
        f"| Index | (symbol, date), deterministic sort |",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print("Cache status: READY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
