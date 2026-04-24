#!/usr/bin/env python3
"""
Vanguard V2 profit agent — XGBoost on unified Alpaca cohort with top-quartile probability gate.

Loads ``reports/Alpaca/alpaca_ml_cohort_unified.csv``, trains ``is_winner = (realized_pnl_usd > 0)``,
reports holdout metrics for the slice where ``predict_proba`` is in the top 25% by score (no 0.5 threshold).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

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
    from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
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
    if "snapshot_exit" in cl:
        return True
    if re.search(r"\bexit_", cl) and "entry" not in cl:
        return True
    if "pnl" in cl and "entry" not in cl:
        return True
    if "mfe" in cl or "mae" in cl:
        return True
    if cl.endswith("_ts_epoch") or "snapshot_ts_epoch" in cl:
        return True
    if cl.startswith("ai_approved"):
        return True
    return False


def _prepare_feature_frame(raw: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray, pd.DataFrame, Dict[str, Any]]:
    raw = raw.loc[raw["realized_pnl_usd"].notna()].copy()
    raw["is_winner"] = (pd.to_numeric(raw["realized_pnl_usd"], errors="coerce") > 0).astype(np.int32)
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
    drop_cols.discard("symbol_enc")
    drop_cols.discard("side_enc")

    feature_cols = [c for c in raw.columns if c not in drop_cols]
    X = raw[feature_cols].copy()
    for c in list(X.columns):
        if X[c].dtype == "object":
            X = X.drop(columns=[c], errors="ignore")
    X = X.apply(pd.to_numeric, errors="coerce").astype("float64")
    meta = {
        "feature_names": list(X.columns),
        "symbol_classes": le_sym.classes_.tolist() if le_sym is not None else [],
        "side_classes": le_side.classes_.tolist() if le_side is not None else [],
    }
    return X, raw["is_winner"].values, raw, meta


def _top_slice_metrics(proba: np.ndarray, y_test: np.ndarray, test_realized: np.ndarray, top_frac: float) -> Dict[str, Any]:
    n_test = len(proba)
    k = max(1, int(math.ceil(float(top_frac) * n_test)))
    order = np.argsort(-proba)
    threshold = float(proba[order[k - 1]])
    approved_mask = proba >= threshold
    approved_pnl = test_realized[approved_mask]
    gross_profit = float(np.nansum(approved_pnl[approved_pnl > 0])) if len(approved_pnl) else 0.0
    gross_loss = float(abs(np.nansum(approved_pnl[approved_pnl < 0]))) if len(approved_pnl) else 0.0
    return {
        "holdout_probability_threshold": threshold,
        "holdout_approved_n": int(approved_mask.sum()),
        "holdout_total_n": int(n_test),
        "holdout_win_rate_among_approved": float(y_test[approved_mask].mean()) if approved_mask.any() else float("nan"),
        "holdout_net_realized_pnl_usd_among_approved": float(np.nansum(approved_pnl)) if len(approved_pnl) else float("nan"),
        "holdout_precision_approved": float(precision_score(y_test, approved_mask.astype(np.int32), zero_division=0)),
        "holdout_recall_approved": float(recall_score(y_test, approved_mask.astype(np.int32), zero_division=0)),
        "holdout_profit_factor_approved": gross_profit / gross_loss if gross_loss > 0 else float("inf"),
        "holdout_gross_profit_approved": gross_profit,
        "holdout_gross_loss_approved": gross_loss,
    }


def _train_challenger_for_side(
    raw_side: pd.DataFrame,
    side_name: str,
    *,
    out_dir: Path,
    train_frac: float,
    top_frac: float,
) -> Dict[str, Any]:
    X, y, raw, meta = _prepare_feature_frame(raw_side)
    split = int(len(raw) * float(train_frac))
    split = max(1, min(split, len(raw) - 1))
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y[:split], y[split:]
    test_realized = pd.to_numeric(raw.iloc[split:]["realized_pnl_usd"], errors="coerce").to_numpy()

    base = xgb.XGBClassifier(
        eval_metric="logloss",
        random_state=42,
        n_jobs=0,
    )
    grid = {
        "max_depth": [2, 3, 4],
        "learning_rate": [0.03, 0.06, 0.1],
        "n_estimators": [100, 200],
        "subsample": [0.8, 1.0],
        "colsample_bytree": [0.75, 0.95],
    }
    cv_splits = min(3, max(2, len(X_train) // 60))
    search = GridSearchCV(
        base,
        grid,
        scoring="precision",
        cv=TimeSeriesSplit(n_splits=cv_splits),
        n_jobs=1,
        error_score=0.0,
    )
    search.fit(X_train.values, y_train)
    clf = search.best_estimator_
    proba = clf.predict_proba(X_test.values)[:, 1]
    metrics = _top_slice_metrics(proba, y_test, test_realized, top_frac)
    metrics.update(
        {
            "side": side_name,
            "rows": int(len(raw)),
            "train": int(len(X_train)),
            "test": int(len(X_test)),
            "pre_decision_features_n": int(len(meta["feature_names"])),
            "best_params": search.best_params_,
            "best_cv_score": float(search.best_score_),
        }
    )

    model_path = out_dir / f"vanguard_challenger_{side_name}.json"
    features_path = out_dir / f"vanguard_challenger_{side_name}_features.json"
    threshold_path = out_dir / f"vanguard_challenger_{side_name}_threshold.json"
    clf.get_booster().save_model(str(model_path))
    meta["side"] = side_name
    features_path.write_text(json.dumps(meta, indent=0), encoding="utf-8")
    threshold_payload = dict(metrics)
    threshold_payload["model_path"] = str(model_path.as_posix())
    threshold_path.write_text(json.dumps(threshold_payload, indent=2), encoding="utf-8")
    return metrics


def train_challenger_split_brain(args: argparse.Namespace) -> int:
    raw = pd.read_csv(args.csv)
    raw = raw.loc[raw["realized_pnl_usd"].notna()].copy()
    if "entry_ts" not in raw.columns:
        print("Missing entry_ts for chronological split.", file=sys.stderr)
        return 1
    raw = raw.iloc[pd.to_datetime(raw["entry_ts"], utc=True, errors="coerce").argsort(kind="mergesort")].reset_index(drop=True)
    out_dir = Path(args.challenger_out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for side_name, aliases in (("long", {"long", "buy"}), ("short", {"short", "sell"})):
        side_df = raw.loc[raw["side"].astype(str).str.lower().isin(aliases)].copy()
        if len(side_df) < 50:
            print(f"Not enough {side_name} rows after filtering: {len(side_df)}", file=sys.stderr)
            return 1
        metrics = _train_challenger_for_side(
            side_df,
            side_name,
            out_dir=out_dir,
            train_frac=args.train_frac,
            top_frac=args.top_frac,
        )
        results.append(metrics)
        print(
            f"CHALLENGER {side_name}: rows={metrics['rows']} train={metrics['train']} test={metrics['test']} "
            f"threshold={metrics['holdout_probability_threshold']:.6f} "
            f"precision={metrics['holdout_precision_approved']:.4f} "
            f"recall={metrics['holdout_recall_approved']:.4f} "
            f"profit_factor={metrics['holdout_profit_factor_approved']:.4f} "
            f"net_pnl={metrics['holdout_net_realized_pnl_usd_among_approved']:.2f} "
            f"best_params={metrics['best_params']}"
        )
    (out_dir / "vanguard_challenger_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("saved challenger summary:", (out_dir / "vanguard_challenger_summary.json").resolve())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--csv",
        type=Path,
        default=REPO_ROOT / "reports" / "Alpaca" / "alpaca_ml_cohort_unified.csv",
    )
    ap.add_argument(
        "--out-model",
        type=Path,
        default=REPO_ROOT / "models" / "vanguard_v2_profit_agent.json",
    )
    ap.add_argument(
        "--out-meta",
        type=Path,
        default=REPO_ROOT / "models" / "vanguard_v2_profit_agent_threshold.json",
    )
    ap.add_argument(
        "--out-features",
        type=Path,
        default=REPO_ROOT / "models" / "vanguard_v2_profit_agent_features.json",
    )
    ap.add_argument("--train-frac", type=float, default=0.8)
    ap.add_argument("--top-frac", type=float, default=0.25)
    ap.add_argument("--train-challenger-split-brain", action="store_true")
    ap.add_argument("--challenger-out-dir", type=Path, default=REPO_ROOT / "models")
    args = ap.parse_args()

    if args.train_challenger_split_brain:
        return train_challenger_split_brain(args)

    raw = pd.read_csv(args.csv)
    raw = raw.loc[raw["realized_pnl_usd"].notna()].copy()
    n = len(raw)
    if n < 50:
        print("Not enough rows after filtering.", file=sys.stderr)
        return 1

    if "entry_ts" not in raw.columns:
        print("Missing entry_ts for chronological split.", file=sys.stderr)
        return 1

    raw["is_winner"] = (pd.to_numeric(raw["realized_pnl_usd"], errors="coerce") > 0).astype(np.int32)

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
    test_realized = pd.to_numeric(raw.iloc[split:]["realized_pnl_usd"], errors="coerce").to_numpy()

    clf = xgb.XGBClassifier(
        eval_metric="logloss",
        max_depth=4,
        learning_rate=0.06,
        n_estimators=200,
        subsample=0.9,
        colsample_bytree=0.85,
        random_state=42,
        n_jobs=0,
    )
    clf.fit(X_train.values, y_train)

    pred_default = clf.predict(X_test.values)
    acc = accuracy_score(y_test, pred_default)

    proba = clf.predict_proba(X_test.values)[:, 1]
    n_test = len(proba)
    top_frac = float(args.top_frac)
    k = max(1, int(math.ceil(top_frac * n_test)))
    order = np.argsort(-proba)
    thr = float(proba[order[k - 1]])
    approved_mask = proba >= thr
    n_ap = int(approved_mask.sum())
    win_rate_top = float(y_test[approved_mask].mean()) if n_ap else float("nan")
    net_pnl_top = float(np.nansum(test_realized[approved_mask])) if n_ap else float("nan")
    precision_top = (
        float(precision_score(y_test, approved_mask.astype(np.int32), zero_division=0))
        if n_test
        else float("nan")
    )
    recall_top = (
        float(recall_score(y_test, approved_mask.astype(np.int32), zero_division=0))
        if n_test
        else float("nan")
    )
    approved_pnl = test_realized[approved_mask]
    gross_profit_top = float(np.nansum(approved_pnl[approved_pnl > 0])) if n_ap else 0.0
    gross_loss_top = float(abs(np.nansum(approved_pnl[approved_pnl < 0]))) if n_ap else 0.0
    profit_factor_top = gross_profit_top / gross_loss_top if gross_loss_top > 0 else float("inf")

    imp = clf.feature_importances_
    order_imp = np.argsort(-imp)
    top10 = [(feat_names[i], float(imp[i])) for i in order_imp[:10]]

    print("=== Vanguard V2 Profit Agent (top-%s holdout slice) ===" % (int(top_frac * 100),))
    print("rows (filled, realized_pnl_usd not null):", n)
    print("train:", len(X_train), "test:", len(X_test))
    print("pre_decision_features_n:", len(feat_names))
    print("Test Accuracy (default 0.5 predict):", round(acc, 4))
    print("Top-quartile probability threshold (inclusive):", round(thr, 6))
    print("Approved count on holdout (proba >= thr):", n_ap, "of", n_test)
    print("Theoretical win rate on approved holdout slice:", round(win_rate_top, 4) if np.isfinite(win_rate_top) else "n/a")
    print("Theoretical net PnL (USD) on approved holdout slice:", round(net_pnl_top, 2) if np.isfinite(net_pnl_top) else "n/a")
    print("Holdout approved precision:", round(precision_top, 4) if np.isfinite(precision_top) else "n/a")
    print("Holdout approved recall:", round(recall_top, 4) if np.isfinite(recall_top) else "n/a")
    print("Holdout approved profit factor:", round(profit_factor_top, 4) if np.isfinite(profit_factor_top) else "inf")
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

    thr_payload = {
        "top_frac": top_frac,
        "holdout_probability_threshold": thr,
        "holdout_approved_n": n_ap,
        "holdout_total_n": n_test,
        "holdout_win_rate_among_approved": win_rate_top,
        "holdout_net_realized_pnl_usd_among_approved": net_pnl_top,
        "holdout_precision_approved": precision_top,
        "holdout_recall_approved": recall_top,
        "holdout_profit_factor_approved": profit_factor_top,
        "holdout_gross_profit_approved": gross_profit_top,
        "holdout_gross_loss_approved": gross_loss_top,
        "model_path": str(args.out_model.as_posix()),
    }
    args.out_meta.write_text(json.dumps(thr_payload, indent=2), encoding="utf-8")
    print("saved threshold meta:", args.out_meta.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
