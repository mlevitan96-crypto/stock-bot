#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from telemetry.vanguard_ml_runtime import default_v2_threshold, evaluate_v2_live_gate  # noqa: E402


CRITICAL_COLUMNS = [
    "symbol",
    "side",
    "entry_ts",
    "exit_ts",
    "entry_price",
    "exit_price",
    "realized_pnl_usd",
    "mlf_ml_feature_source",
    "mlf_scoreflow_join_tier",
    "mlf_scoreflow_total_score",
]


def _to_float_or_nan(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if math.isfinite(out) else float("nan")


def _row_features(row: pd.Series) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, value in row.items():
        if key in {"symbol", "side", "entry_ts", "exit_ts", "trade_id", "trade_key", "variant_id", "composite_version"}:
            continue
        out[str(key)] = _to_float_or_nan(value)
    try:
        entry = pd.to_datetime(row.get("entry_ts"), utc=True, errors="coerce")
        if not pd.isna(entry):
            out["hour_of_day"] = float(entry.tz_convert("America/New_York").hour)
    except Exception:
        pass
    return out


def _missing_critical_count(df: pd.DataFrame) -> int:
    missing_cols = [c for c in CRITICAL_COLUMNS if c not in df.columns]
    if missing_cols:
        return int(len(df))
    critical = df[CRITICAL_COLUMNS].replace("", np.nan)
    return int(critical.isna().any(axis=1).sum())


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze one Alpaca closed-trade market day from the flat ML cohort.")
    ap.add_argument("--csv", type=Path, default=REPO_ROOT / "reports" / "Alpaca" / "alpaca_ml_cohort_flat.csv")
    ap.add_argument("--date", default="2026-04-24", help="Market date in America/New_York, YYYY-MM-DD.")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    target = date.fromisoformat(args.date)
    exit_dt = pd.to_datetime(df["exit_ts"], utc=True, errors="coerce").dt.tz_convert("America/New_York")
    today = df.loc[exit_dt.dt.date == target].copy()

    today["realized_pnl_usd"] = pd.to_numeric(today["realized_pnl_usd"], errors="coerce")
    today["entry_price"] = pd.to_numeric(today["entry_price"], errors="coerce")
    today["exit_price"] = pd.to_numeric(today["exit_price"], errors="coerce")

    v2_probas: list[float] = []
    v2_reasons: list[str] = []
    for _, row in today.iterrows():
        allowed, proba, reason = evaluate_v2_live_gate(
            symbol=str(row.get("symbol", "")),
            side=str(row.get("side", "")),
            row=_row_features(row),
        )
        del allowed
        v2_probas.append(float(proba) if proba is not None else float("nan"))
        v2_reasons.append(reason)
    today["v2_proba"] = v2_probas
    today["v2_reason"] = v2_reasons

    winners = today.loc[today["realized_pnl_usd"] > 0]
    losers = today.loc[today["realized_pnl_usd"] <= 0]
    highest_entry = today.loc[today["entry_price"].idxmax()] if len(today) and today["entry_price"].notna().any() else None

    result = {
        "market_date_et": args.date,
        "source_csv": str(args.csv),
        "total_closed_trades_today": int(len(today)),
        "data_integrity_missing_critical_or_exit_pnl_rows": _missing_critical_count(today),
        "ai_approved_v2_missing_rows": int(today["ai_approved_v2"].replace("", np.nan).isna().sum())
        if "ai_approved_v2" in today.columns
        else int(len(today)),
        "win_rate_pct": round(float((today["realized_pnl_usd"] > 0).mean() * 100.0), 2) if len(today) else None,
        "net_realized_pnl_usd": round(float(today["realized_pnl_usd"].sum()), 2) if len(today) else 0.0,
        "gross_winner_pnl_usd": round(float(winners["realized_pnl_usd"].sum()), 2) if len(winners) else 0.0,
        "gross_loser_pnl_usd": round(float(losers["realized_pnl_usd"].sum()), 2) if len(losers) else 0.0,
        "highest_entry_price": round(float(highest_entry["entry_price"]), 4) if highest_entry is not None else None,
        "highest_entry_symbol": str(highest_entry["symbol"]) if highest_entry is not None else None,
        "highest_entry_side": str(highest_entry["side"]) if highest_entry is not None else None,
        "bought_above_825_count": int((today["entry_price"] > 825).sum()) if len(today) else 0,
        "highest_entry_above_825": bool(float(highest_entry["entry_price"]) > 825.0) if highest_entry is not None else False,
        "v2_threshold": round(float(default_v2_threshold()), 6),
        "v2_proba_available_count": int(today["v2_proba"].notna().sum()) if len(today) else 0,
        "avg_v2_proba_winners": round(float(winners["v2_proba"].mean()), 6) if len(winners) and winners["v2_proba"].notna().any() else None,
        "avg_v2_proba_losers": round(float(losers["v2_proba"].mean()), 6) if len(losers) and losers["v2_proba"].notna().any() else None,
        "median_v2_proba_winners": round(float(winners["v2_proba"].median()), 6) if len(winners) and winners["v2_proba"].notna().any() else None,
        "median_v2_proba_losers": round(float(losers["v2_proba"].median()), 6) if len(losers) and losers["v2_proba"].notna().any() else None,
        "top_symbols_by_pnl": [
            {
                "symbol": str(r.symbol),
                "realized_pnl_usd": round(float(r.realized_pnl_usd), 2),
                "entry_price": round(float(r.entry_price), 4),
                "v2_proba": round(float(r.v2_proba), 6) if math.isfinite(float(r.v2_proba)) else None,
            }
            for r in today.sort_values("realized_pnl_usd", ascending=False).head(5).itertuples(index=False)
        ],
        "bottom_symbols_by_pnl": [
            {
                "symbol": str(r.symbol),
                "realized_pnl_usd": round(float(r.realized_pnl_usd), 2),
                "entry_price": round(float(r.entry_price), 4),
                "v2_proba": round(float(r.v2_proba), 6) if math.isfinite(float(r.v2_proba)) else None,
            }
            for r in today.sort_values("realized_pnl_usd", ascending=True).head(5).itertuples(index=False)
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
