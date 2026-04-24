#!/usr/bin/env python3
"""
Vanguard Entry Filter V1 — XGBoost classifier on pre-decision features only.

Loads reports/Gemini/alpaca_ml_cohort_flat.csv, builds is_winner from realized_pnl_usd,
strips post-trade / exit-path columns, chronological 80/20 split, trains shallow XGBClassifier,
prints metrics + importances, saves booster to reports/Gemini/vanguard_entry_filter_v1.json.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Set

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

try:
    import xgboost as xgb
except ImportError as e:  # pragma: no cover
    print("pip install xgboost", e, file=sys.stderr)
    sys.exit(1)

try:
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    from sklearn.preprocessing import LabelEncoder
except ImportError as e:  # pragma: no cover
    print("pip install scikit-learn", e, file=sys.stderr)
    sys.exit(1)

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None


def _hour_of_day_et(entry_ts: pd.Series) -> pd.Series:
    dt = pd.to_datetime(entry_ts, utc=True, errors="coerce")
    if _ET is not None:
        dt = dt.dt.tz_convert(_ET)
    return dt.dt.hour.astype("float64")


def _is_leaky_column(name: str) -> bool:
    c = str(name).strip()
    cl = c.lower()
    if cl in {
        "realized_pnl_usd",
        "exit_price",
        "exit_ts",
        "exit_mfe_pct",
        "exit_mae_pct",
        "holding_time_minutes",
        "exit_intent",
    }:
        return True
    if cl.startswith("exit_"):
        return True
    if "_exit_" in cl:
        return True
    if re.search(r"\bexit_", cl) and "entry" not in cl:
        return True
    if "pnl" in cl and "entry" not in cl:
        return True
    if "mfe" in cl or "mae" in cl:
        return True
    if cl.endswith("_ts_epoch") or "snapshot_ts_epoch" in cl:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--csv",
        type=Path,
        default=REPO_ROOT / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv",
    )
    ap.add_argument(
        "--out-model",
        type=Path,
        default=REPO_ROOT / "models" / "vanguard_entry_filter_v1.json",
    )
    ap.add_argument(
        "--out-features",
        type=Path,
        default=REPO_ROOT / "models" / "vanguard_entry_filter_v1_features.json",
    )
    ap.add_argument("--train-frac", type=float, default=0.8)
    args = ap.parse_args()

    raw = pd.read_csv(args.csv)
    raw = raw.loc[raw["realized_pnl_usd"].notna()].copy()
    n = len(raw)
    if n < 50:
        print("Not enough rows after filtering.", file=sys.stderr)
        return 1

    if "entry_ts" not in raw.columns:
        print("Missing entry_ts for chronological split.", file=sys.stderr)
        return 1

    raw["is_winner"] = (pd.to_numeric(raw["realized_pnl_usd"], errors="coerce") > 0).astype(
        np.int32
    )

    order = pd.to_datetime(raw["entry_ts"], utc=True, errors="coerce").argsort(kind="mergesort")
    raw = raw.iloc[order].reset_index(drop=True)

    raw["hour_of_day"] = _hour_of_day_et(raw["entry_ts"])
    le_sym: Optional[LabelEncoder] = None
    le_side: Optional[LabelEncoder] = None
    if "symbol" in raw.columns:
        le_sym = LabelEncoder()
        raw["symbol_enc"] = le_sym.fit_transform(raw["symbol"].astype(str))
    if "side" in raw.columns:
        le_side = LabelEncoder()
        raw["side_enc"] = le_side.fit_transform(raw["side"].astype(str))

    drop_cols: Set[str] = set()
    for col in raw.columns:
        if _is_leaky_column(col):
            drop_cols.add(col)
    drop_cols.update(
        {
            "is_winner",
            "entry_ts",
            "trade_id",
            "trade_key",
            "variant_id",
            "composite_version",
            "symbol",
            "side",
        }
    )
    # Do not use encoded ids as leakage — keep symbol_enc / side_enc
    drop_cols.discard("symbol_enc")
    drop_cols.discard("side_enc")

    feature_cols = [c for c in raw.columns if c not in drop_cols]
    X = raw[feature_cols].copy()
    for c in list(X.columns):
        if X[c].dtype == "object":
            X = X.drop(columns=[c], errors="ignore")
    X = X.apply(pd.to_numeric, errors="coerce").astype("float64")
    feat_names = list(X.columns)
    y = raw["is_winner"].values

    split = int(len(raw) * float(args.train_frac))
    split = max(1, min(split, len(raw) - 1))
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y[:split], y[split:]

    clf = xgb.XGBClassifier(
        eval_metric="logloss",
        max_depth=3,
        learning_rate=0.05,
        n_estimators=150,
        subsample=0.9,
        colsample_bytree=0.85,
        random_state=42,
        n_jobs=0,
    )
    clf.fit(X_train.values, y_train)

    pred = clf.predict(X_test.values)

    acc = accuracy_score(y_test, pred)
    prec = precision_score(y_test, pred, zero_division=0)
    rec = recall_score(y_test, pred, zero_division=0)

    mask = pred == 1
    if mask.sum() > 0:
        approval_win_rate = float(y_test[mask].mean())
    else:
        approval_win_rate = float("nan")

    imp = clf.feature_importances_
    order_imp = np.argsort(-imp)
    top10 = [(feat_names[i], float(imp[i])) for i in order_imp[:10]]

    print("=== Vanguard Entry Filter V1 ===")
    print("rows (filled, realized_pnl_usd not null):", n)
    print("train:", len(X_train), "test:", len(X_test))
    print("pre_decision_features_n:", len(feat_names))
    print("(Flat cohort has no gut_confluence_score / shadow_fractal_vapor columns; using all safe numeric drivers.)")
    print("Test Accuracy:", round(acc, 4))
    print("Test Precision (pred positive = approve):", round(prec, 4))
    print("Test Recall:", round(rec, 4))
    print(
        "Theoretical win rate on test when model approves (y_true mean | pred==1):",
        round(approval_win_rate, 4) if np.isfinite(approval_win_rate) else "n/a",
    )
    print("Top 10 feature importances:")
    for name, v in top10:
        print(f"  {name}: {v:.5f}")

    args.out_model.parent.mkdir(parents=True, exist_ok=True)
    clf.get_booster().save_model(str(args.out_model))
    print("saved:", args.out_model.resolve())
    meta = {
        "feature_names": feat_names,
        "symbol_classes": le_sym.classes_.tolist() if le_sym is not None else [],
        "side_classes": le_side.classes_.tolist() if le_side is not None else [],
    }
    args.out_features.write_text(json.dumps(meta, indent=0), encoding="utf-8")
    print("saved features manifest:", args.out_features.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
