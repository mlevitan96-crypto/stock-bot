#!/usr/bin/env python3
"""
Analyze SPI-related columns in a trades CSV (and optionally Gemini SPI CSV) for blank / non-numeric rates.

Usage:
  python3 scripts/stock_spi_diagnostics.py reports/stock_100_trades.csv
  python3 scripts/stock_spi_diagnostics.py reports/stock_100_trades.csv --spi reports/Gemini/signal_intelligence_spi.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Aligns with scripts/telemetry_milestone_watcher.py SPI_CORE_COLS
SPI_CORE_COLS = [
    "component_options_flow",
    "component_dark_pool",
    "component_greeks_gamma",
    "component_ftd_pressure",
    "component_iv_skew",
    "component_oi_change",
    "component_toxicity_penalty",
]


def _is_numeric_cell(val: str) -> bool:
    s = (val or "").strip()
    if s == "" or s.lower() in ("null", "none", "nan"):
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


def _analyze_csv(path: Path, label: str) -> None:
    if not path.is_file():
        print(f"{label}: file not found: {path}", file=sys.stderr)
        return
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        headers = list(r.fieldnames or [])
        spi_like: List[str] = []
        for h in headers:
            if not h:
                continue
            if h.startswith("component_") or h.startswith("shadow_"):
                spi_like.append(h)
            elif h in ("total_score", "freshness"):
                spi_like.append(h)
        if not spi_like:
            spi_like = [h for h in SPI_CORE_COLS if h in headers]
        rows: List[Dict[str, str]] = list(r)
    n = len(rows)
    print(f"\n=== {label}: {path} ({n} rows) ===")
    if n == 0:
        print("No data rows.")
        return
    for col in spi_like:
        blank = sum(1 for row in rows if not _is_numeric_cell((row.get(col) or "").strip()))
        pct = 100.0 * blank / n if n else 0.0
        print(f"  {col}: blank/non-numeric {blank}/{n} ({pct:.1f}%)")
    # Milestone-style check on standard 7 columns if present
    present = [c for c in SPI_CORE_COLS if c in headers]
    if present:
        bad_rows = 0
        for row in rows:
            if any(not _is_numeric_cell((row.get(c) or "").strip()) for c in present):
                bad_rows += 1
        print(
            f"  [gate] rows missing any of {len(present)} core SPI cols: "
            f"{bad_rows}/{n} ({100.0 * bad_rows / n:.1f}%)"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("trades_csv", type=Path, help="Exported closed trades CSV")
    ap.add_argument(
        "--spi",
        type=Path,
        default=None,
        help="Optional reports/Gemini/signal_intelligence_spi.csv for pipeline view",
    )
    args = ap.parse_args()
    _analyze_csv(args.trades_csv.resolve(), "Trades export")
    if args.spi:
        _analyze_csv(args.spi.resolve(), "Gemini SPI CSV (full file)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
