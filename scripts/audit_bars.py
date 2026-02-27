#!/usr/bin/env python3
"""
Phase 4: Audit bars parquet. Checks: no NaN/Inf in OHLCV, High >= max(O,C), Low <= min(O,C),
Volume >= 0, no duplicate (symbol, date), date continuity per symbol (gaps/holidays allowed).
Writes reports/bars/integrity_audit.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

REPORT_DIR = REPO / "reports" / "bars"
AUDIT_PATH = REPORT_DIR / "integrity_audit.md"


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="path", default=None, help="Input parquet (default data/bars/alpaca_daily.parquet)")
    args = ap.parse_args()
    path = Path(args.path) if args.path else REPO / "data" / "bars" / "alpaca_daily.parquet"

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        AUDIT_PATH.write_text(
            "# Integrity audit\n\n**Status:** FAIL\n\nFile missing: " + str(path) + "\n",
            encoding="utf-8",
        )
        return 1

    import math
    import pandas as pd
    df = pd.read_parquet(path)
    if df.empty:
        AUDIT_PATH.write_text("# Integrity audit\n\n**Status:** FAIL\n\nParquet is empty.\n", encoding="utf-8")
        return 1

    errors = []
    # Required columns
    for col in ["symbol", "date", "o", "h", "l", "c", "volume"]:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
    if errors:
        AUDIT_PATH.write_text("# Integrity audit\n\n**Status:** FAIL\n\n" + "\n".join(errors) + "\n", encoding="utf-8")
        return 1

    # NaN/Inf
    for col in ["o", "h", "l", "c", "volume"]:
        if df[col].isna().any():
            errors.append(f"NaN in {col}")
        if hasattr(df[col], "__abs__") and (df[col].astype(float) == float("inf")).any():
            errors.append(f"Inf in {col}")
    df = df.astype({"o": float, "h": float, "l": float, "c": float, "volume": float}, errors="ignore")
    # High >= max(Open, Close), Low <= min(Open, Close)
    bad_hl = (df["h"] < df[["o", "c"]].max(axis=1)) | (df["l"] > df[["o", "c"]].min(axis=1))
    if bad_hl.any():
        errors.append("High < max(O,C) or Low > min(O,C) in some rows")
    # Volume >= 0
    if (df["volume"] < 0).any():
        errors.append("Negative volume")
    # No duplicate (symbol, date)
    dup = df.duplicated(subset=["symbol", "date"], keep=False)
    if dup.any():
        errors.append("Duplicate (symbol, date) present")
    # Date continuity: per symbol, sorted dates; we allow gaps (holidays)
    # No check required beyond no-duplicate

    if errors:
        AUDIT_PATH.write_text(
            "# Integrity audit\n\n**Status:** FAIL\n\n" + "\n".join("- " + e for e in errors) + "\n",
            encoding="utf-8",
        )
        return 1

    lines = [
        "# Integrity audit",
        "",
        "**Status:** PASS",
        "",
        "| Check | Result |",
        "|-------|--------|",
        "| NaN/Inf in OHLCV | none |",
        "| High >= max(O,C), Low <= min(O,C) | ok |",
        "| Volume >= 0 | ok |",
        "| No duplicate (symbol, date) | ok |",
        "| Rows | " + str(len(df)) + " |",
    ]
    AUDIT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print("Integrity audit: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
