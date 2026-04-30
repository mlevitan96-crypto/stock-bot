#!/usr/bin/env python3
"""
Forensic probe: V2 XGBoost probability vs synthetic rows (train cohort shape).

Answers: (1) What probability does a "God Tier" *independent p99/max* row get?
(2) What does median cohort / median winner row get? (3) NaN-heavy + high scoreflow only?

Run from repo root:
  python scripts/debug/v2_perfect_trade_probe.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from telemetry.vanguard_ml_runtime import predict_v2_probability  # noqa: E402


def _stat_series(df: pd.DataFrame, k: str) -> np.ndarray | None:
    if k not in df.columns:
        return None
    a = pd.to_numeric(df[k], errors="coerce").to_numpy(dtype=float)
    a = a[np.isfinite(a)]
    return a if a.size else None


def god_row(df: pd.DataFrame, fo: list[str], mode: str) -> dict[str, float]:
    row: dict[str, float] = {}
    for k in fo:
        if k in ("symbol_enc", "side_enc"):
            continue
        a = _stat_series(df, k)
        if a is None:
            row[k] = 0.0 if mode == "zeros" else 1.5
            continue
        if mode == "p99":
            v = float(np.percentile(a, 99))
        elif mode == "max":
            v = float(np.max(a))
        elif mode == "mean":
            v = float(np.mean(a))
        else:
            v = 0.0
        row[k] = v if math.isfinite(v) else 0.0
    return row


def median_row(df: pd.DataFrame, fo: list[str]) -> dict[str, float]:
    row: dict[str, float] = {}
    for k in fo:
        if k in ("symbol_enc", "side_enc"):
            continue
        a = _stat_series(df, k)
        if a is None:
            row[k] = float("nan")
        else:
            row[k] = float(np.median(a))
    return row


def main() -> int:
    meta_path = REPO / "models" / "vanguard_v2_profit_agent_features.json"
    thr_path = REPO / "models" / "vanguard_v2_profit_agent_threshold.json"
    cohort = REPO / "reports" / "Alpaca" / "alpaca_ml_cohort_unified.csv"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    fo = list(meta["feature_names"])
    sc = [str(x) for x in (meta.get("symbol_classes") or [])]
    sdc = [str(x) for x in (meta.get("side_classes") or [])]
    thr = float(json.loads(thr_path.read_text(encoding="utf-8"))["holdout_probability_threshold"])

    if not cohort.is_file():
        print("MISSING", cohort, file=sys.stderr)
        return 2

    df = pd.read_csv(cohort, nrows=12000, low_memory=False)

    print("V2 threshold (holdout top_frac gate):", round(thr, 6))
    print("feature_count", len(fo))
    print()

    print("--- Synthetic conjunction tests (same symbol=TSLA, side=buy) ---")
    for mode in ("p99", "max", "mean", "zeros"):
        row = god_row(df, fo, mode)
        p, err = predict_v2_probability(fo, "TSLA", "buy", sc, sdc, row)
        print(f"  {mode:6s}  P(win)={p}  err={err}")

    row = {k: 1.0 for k in fo if k not in ("symbol_enc", "side_enc")}
    p, err = predict_v2_probability(fo, "TSLA", "buy", sc, sdc, row)
    print(f"  {'all_1.0':6s}  P(win)={p}  err={err}")

    row = {k: float("nan") for k in fo}
    row["hour_of_day"] = 10.0
    row["entry_price"] = 100.0
    row["mlf_scoreflow_total_score"] = 5.0
    p, err = predict_v2_probability(fo, "TSLA", "buy", sc, sdc, row)
    print(f"  {'sparse':6s}  P(win)={p}  err={err}  (only hour, entry_price, mlf_scoreflow_total_score)")

    print()
    print("--- Cohort median rows ---")
    row_all = median_row(df, fo)
    p, err = predict_v2_probability(fo, "TSLA", "buy", sc, sdc, row_all)
    nan_n = sum(1 for k in fo if k not in ("symbol_enc", "side_enc") and (k not in row_all or not math.isfinite(float(row_all[k]))))
    print(f"  median ALL rows     P={p}  nan_features~{nan_n}  err={err}")

    win = df[pd.to_numeric(df["realized_pnl_usd"], errors="coerce") > 0]
    if len(win) > 30:
        row_w = median_row(win, fo)
        p, err = predict_v2_probability(fo, "TSLA", "buy", sc, sdc, row_w)
        nan_n = sum(
            1
            for k in fo
            if k not in ("symbol_enc", "side_enc") and (k not in row_w or not math.isfinite(float(row_w[k])))
        )
        print(f"  median WINNER rows  P={p}  nan_features~{nan_n}  err={err}")

    print()
    print("INTERPRETATION:")
    print("  - p99/max *per-feature* conjunction is OOD; trees assign ~10% — not proof of broken booster.")
    print("  - Median cohort / winner shapes reach ~0.41–0.48+; model can exceed threshold on in-distribution rows.")
    print("  - Live vetoes with high composite + low P usually imply NaN-heavy / skewed flat row vs training support.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
