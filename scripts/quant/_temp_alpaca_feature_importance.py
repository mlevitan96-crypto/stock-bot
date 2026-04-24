#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]


def _is_candidate_feature(col: str) -> bool:
    c = col.lower()
    if c in {"realized_pnl_usd", "exit_price", "exit_ts", "trade_id", "trade_key"}:
        return False
    if c.startswith("exit_") or "_exit_" in c or "snapshot_exit" in c:
        return False
    if "pnl" in c or "mfe" in c or "mae" in c:
        return False
    if c.startswith("ai_approved") or c.startswith("v2_proba"):
        return False
    if c.endswith("_ts_epoch") or "snapshot_ts_epoch" in c:
        return False
    return (
        c.startswith("mlf_scoreflow_components_")
        or c.startswith("mlf_entry_uw_")
        or c.startswith("mlf_direction_intel_embed_intel_snapshot_entry_")
        or c in {"entry_price", "qty", "uw_gamma_skew", "uw_tide_score", "hour_of_day", "side_short"}
    )


def _friendly_name(name: str) -> str:
    replacements = {
        "mlf_scoreflow_components_": "",
        "mlf_entry_uw_": "uw_",
        "mlf_direction_intel_embed_intel_snapshot_entry_": "entry_",
    }
    out = name
    for prefix, repl in replacements.items():
        if out.startswith(prefix):
            out = repl + out[len(prefix) :]
            break
    return out


def _load_v2_gain() -> dict[str, float]:
    model = REPO_ROOT / "models" / "vanguard_v2_profit_agent.json"
    features = REPO_ROOT / "models" / "vanguard_v2_profit_agent_features.json"
    if not model.is_file() or not features.is_file():
        return {}
    try:
        import xgboost as xgb

        meta = json.loads(features.read_text(encoding="utf-8"))
        names = list(meta.get("feature_names") or [])
        booster = xgb.Booster()
        booster.load_model(str(model))
        raw = booster.get_score(importance_type="gain")
        out: dict[str, float] = {}
        for key, value in raw.items():
            if re.fullmatch(r"f\d+", key):
                idx = int(key[1:])
                if 0 <= idx < len(names):
                    out[names[idx]] = float(value)
            else:
                out[key] = float(value)
        return out
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Feature/PnL correlation diagnostics for one Alpaca EOD cohort.")
    ap.add_argument("--csv", type=Path, default=REPO_ROOT / "reports" / "Alpaca" / "alpaca_ml_cohort_flat.csv")
    ap.add_argument("--date", default="2026-04-24")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    exit_dt = pd.to_datetime(df["exit_ts"], utc=True, errors="coerce").dt.tz_convert("America/New_York")
    today = df.loc[exit_dt.dt.date.astype(str) == args.date].copy()
    today["realized_pnl_usd"] = pd.to_numeric(today["realized_pnl_usd"], errors="coerce")
    today["entry_price"] = pd.to_numeric(today["entry_price"], errors="coerce")
    today["exit_price"] = pd.to_numeric(today["exit_price"], errors="coerce")
    flat = today["realized_pnl_usd"].abs() < 1e-9
    today.loc[today["entry_price"].isna() & flat, "entry_price"] = today.loc[today["entry_price"].isna() & flat, "exit_price"]

    entry_dt = pd.to_datetime(today["entry_ts"], utc=True, errors="coerce").dt.tz_convert("America/New_York")
    today["hour_of_day"] = entry_dt.dt.hour + entry_dt.dt.minute / 60.0
    today["side_short"] = today["side"].astype(str).str.lower().eq("short").astype(float)

    y = today["realized_pnl_usd"]
    rows: list[dict[str, Any]] = []
    for col in today.columns:
        if not _is_candidate_feature(str(col)):
            continue
        x = pd.to_numeric(today[col], errors="coerce")
        valid = x.notna() & y.notna()
        if int(valid.sum()) < 10:
            continue
        xv = x.loc[valid]
        yv = y.loc[valid]
        if float(xv.std(ddof=0)) == 0.0:
            continue
        pearson = float(xv.corr(yv, method="pearson"))
        spearman = float(xv.corr(yv, method="spearman"))
        if not np.isfinite(pearson) and not np.isfinite(spearman):
            continue
        rows.append(
            {
                "feature": str(col),
                "name": _friendly_name(str(col)),
                "n": int(valid.sum()),
                "pearson": round(pearson, 6) if np.isfinite(pearson) else None,
                "spearman": round(spearman, 6) if np.isfinite(spearman) else None,
                "abs_spearman": abs(spearman) if np.isfinite(spearman) else -1.0,
            }
        )

    rows.sort(key=lambda r: (r["abs_spearman"], abs(r["pearson"] or 0.0)), reverse=True)
    gain = _load_v2_gain()
    gain_rows = [
        {"feature": k, "name": _friendly_name(k), "gain": round(v, 6)}
        for k, v in sorted(gain.items(), key=lambda kv: kv[1], reverse=True)[:12]
    ]

    selected_names = ["alpha11", "rsi", "vwap", "hour_of_day", "mlf_entry_uw_flow_strength", "mlf_scoreflow_components_flow"]
    selected = {}
    for needle in selected_names:
        matches = [r for r in rows if needle.lower() in r["feature"].lower()]
        selected[needle] = matches[:5]

    payload = {
        "market_date_et": args.date,
        "rows": int(len(today)),
        "numeric_candidate_features": int(len(rows)),
        "top_correlations_by_abs_spearman": rows[:15],
        "top_v2_model_gain_features": gain_rows,
        "requested_feature_presence": {
            "alpha11_flow": any("alpha11" in c.lower() for c in today.columns),
            "rsi": any(re.search(r"(^|_)rsi($|_)", c.lower()) for c in today.columns),
            "vwap_distance": any("vwap" in c.lower() for c in today.columns),
            "time_of_day": True,
        },
        "requested_feature_correlations": selected,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
