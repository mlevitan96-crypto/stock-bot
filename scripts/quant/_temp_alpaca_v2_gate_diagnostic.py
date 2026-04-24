#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from telemetry.vanguard_ml_runtime import default_v2_threshold, evaluate_v2_live_gate  # noqa: E402


def _to_float_or_nan(value: Any) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return out if math.isfinite(out) else float("nan")


def _row_features(row: pd.Series) -> dict[str, float]:
    out: dict[str, float] = {}
    skip = {"symbol", "side", "entry_ts", "exit_ts", "trade_id", "trade_key", "variant_id", "composite_version"}
    for key, value in row.items():
        if key in skip:
            continue
        out[str(key)] = _to_float_or_nan(value)
    try:
        entry = pd.to_datetime(row.get("entry_ts"), utc=True, errors="coerce")
        if not pd.isna(entry):
            out["hour_of_day"] = float(entry.tz_convert("America/New_York").hour)
    except Exception:
        pass
    return out


def _classify(row: pd.Series, threshold: float) -> str:
    side = str(row.get("side") or "").lower()
    proba = float(row.get("v2_proba"))
    entry_dt = pd.to_datetime(row.get("entry_ts"), utc=True, errors="coerce")
    exit_dt = pd.to_datetime(row.get("exit_ts"), utc=True, errors="coerce")
    same_instant = not pd.isna(entry_dt) and not pd.isna(exit_dt) and abs((exit_dt - entry_dt).total_seconds()) < 1.0
    pnl = _to_float_or_nan(row.get("realized_pnl_usd"))

    if proba >= threshold:
        return "above_threshold"
    if side == "short":
        return "short_bypassed_long_only_gate"
    if same_instant and abs(pnl) < 1e-9:
        return "flat_synthetic_same_instant_not_entry"
    if not pd.isna(entry_dt) and entry_dt.tz_convert("America/New_York").date().isoformat() != "2026-04-24":
        return "opened_before_target_day"
    return "below_threshold_long_requires_log_review"


def main() -> int:
    ap = argparse.ArgumentParser(description="Diagnose why post-hoc below-threshold V2 trades executed.")
    ap.add_argument("--csv", type=Path, default=REPO_ROOT / "reports" / "Alpaca" / "alpaca_ml_cohort_flat.csv")
    ap.add_argument("--date", default="2026-04-24")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    exit_dt = pd.to_datetime(df["exit_ts"], utc=True, errors="coerce").dt.tz_convert("America/New_York")
    today = df.loc[exit_dt.dt.date.astype(str) == args.date].copy()
    today["realized_pnl_usd"] = pd.to_numeric(today["realized_pnl_usd"], errors="coerce")
    today["entry_price"] = pd.to_numeric(today["entry_price"], errors="coerce")
    flat = today["realized_pnl_usd"].abs() < 1e-9
    today.loc[today["entry_price"].isna() & flat, "entry_price"] = pd.to_numeric(
        today.loc[today["entry_price"].isna() & flat, "exit_price"], errors="coerce"
    )

    probas: list[float] = []
    reasons: list[str] = []
    for _, row in today.iterrows():
        _, proba, reason = evaluate_v2_live_gate(symbol=str(row.get("symbol", "")), side=str(row.get("side", "")), row=_row_features(row))
        probas.append(float(proba) if proba is not None else float("nan"))
        reasons.append(str(reason))
    today["v2_proba"] = probas
    today["v2_reason"] = reasons

    threshold = float(default_v2_threshold())
    today["gate_diagnosis"] = today.apply(lambda r: _classify(r, threshold), axis=1)
    below = today.loc[today["v2_proba"] < threshold].copy()

    detail_cols = ["symbol", "side", "entry_ts", "exit_ts", "entry_price", "realized_pnl_usd", "v2_proba", "gate_diagnosis"]
    payload = {
        "market_date_et": args.date,
        "v2_threshold": round(threshold, 6),
        "total_closed_trades": int(len(today)),
        "below_threshold_count": int(len(below)),
        "above_or_equal_threshold_count": int((today["v2_proba"] >= threshold).sum()),
        "below_threshold_by_side": below.groupby("side").size().to_dict(),
        "diagnosis_counts": below["gate_diagnosis"].value_counts().to_dict(),
        "long_below_threshold_rows": below.loc[below["side"].astype(str).str.lower() == "long", detail_cols].to_dict(orient="records"),
        "short_below_threshold_count": int((below["side"].astype(str).str.lower() == "short").sum()),
        "remote_log_note": "Remote run.jsonl had no Apr 24 v2_live_gate_error/v2_agent_veto/v2_gate_pass events; post-hoc probabilities are recomputed from flat features, not persisted live gate decisions.",
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
