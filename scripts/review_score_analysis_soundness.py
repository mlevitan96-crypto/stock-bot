#!/usr/bin/env python3
"""
Reviewer: sanity-check score_vs_profitability and baseline consistency.
Ensures totals match, no impossible values, and band counts sum to total trades.
Exit 0 if sound; non-zero and prints issues if not.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True, help="e.g. reports/backtests/<RUN_ID>")
    args = ap.parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = REPO / run_dir
    errors = []

    # 1) score_bands.json: band counts sum to total_trades
    sb_path = run_dir / "score_analysis" / "score_bands.json"
    if sb_path.exists():
        sb = json.loads(sb_path.read_text(encoding="utf-8"))
        band_total = sum(b.get("trade_count") or 0 for b in sb.get("bands") or [])
        declared = sb.get("total_trades") or 0
        if band_total != declared:
            errors.append(f"score_bands: sum(band trade_count)={band_total} != total_trades={declared}")
        for b in sb.get("bands") or []:
            n = b.get("trade_count") or 0
            wr = b.get("win_rate_pct")
            if wr is not None and (wr < 0 or wr > 100):
                errors.append(f"score_bands: band {b.get('score_band')} has invalid win_rate_pct={wr}")
            if n > 0 and b.get("winning_trades", 0) + b.get("losing_trades", 0) > n:
                errors.append(f"score_bands: band {b.get('score_band')} wins+losses > trade_count")

    # 2) baseline metrics vs score_analysis total
    base_metrics = run_dir / "baseline" / "metrics.json"
    if base_metrics.exists() and sb_path.exists():
        m = json.loads(base_metrics.read_text(encoding="utf-8"))
        sb = json.loads(sb_path.read_text(encoding="utf-8"))
        if m.get("trades_count") != sb.get("total_trades"):
            errors.append(f"baseline metrics trades_count={m.get('trades_count')} != score_bands total_trades={sb.get('total_trades')}")

    if errors:
        for e in errors:
            print("REVIEW FAIL:", e, file=sys.stderr)
        return 1
    print("Review passed: score analysis and baseline consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
