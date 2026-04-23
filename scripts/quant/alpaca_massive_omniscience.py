#!/usr/bin/env python3
"""
Massive Omniscience: ensemble classifier + SHAP (with interaction scan) on enriched
Alpaca ML cohort CSV. Counter-intelligence vectors + shadow / AI PnL audit.

Usage:
  PYTHONPATH=. python scripts/quant/alpaca_massive_omniscience.py \\
    --csv reports/Alpaca/alpaca_ml_cohort_unified.csv \\
    --out-json reports/Alpaca/massive_omniscience_shap.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Momentum-like scoreflow columns for signal_density
_SCOREFLOW_MOM = [
    "mlf_scoreflow_components_flow",
    "mlf_scoreflow_components_market_tide",
    "mlf_scoreflow_components_motif_bonus",
    "mlf_scoreflow_components_regime",
    "mlf_scoreflow_components_shorts_squeeze",
    "mlf_scoreflow_components_squeeze_score",
    "mlf_scoreflow_components_institutional",
    "mlf_scoreflow_components_dark_pool",
    "mlf_scoreflow_components_etf_flow",
]


def _pnl_col(df: pd.DataFrame) -> str:
    for c in ("exit_realized_pnl_usd", "realized_pnl_usd"):
        if c in df.columns:
            return c
    raise ValueError("No PnL column (exit_realized_pnl_usd or realized_pnl_usd)")


def _session_slice_et(entry_ts: Any) -> str:
    """15-minute ET bins from market context (labels like 09:30-09:45)."""
    from datetime import datetime, timezone

    try:
        from zoneinfo import ZoneInfo

        et = ZoneInfo("America/New_York")
    except Exception:
        return "unknown"
    if pd.isna(entry_ts):
        return "unknown"
    s = str(entry_ts).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return "unknown"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    loc = dt.astimezone(et)
    # minutes since midnight ET
    m0 = loc.hour * 60 + loc.minute
    bin_start = (m0 // 15) * 15
    h1, m1 = divmod(bin_start, 60)
    h2, m2 = divmod(bin_start + 15, 60)
    return f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}"


def _engineer_vectors(df: pd.DataFrame, pnl_col: str) -> pd.DataFrame:
    out = df.copy()
    out["_entry_sort"] = pd.to_datetime(out["entry_ts"], utc=True, errors="coerce")
    out = out.sort_values("_entry_sort").reset_index(drop=True)

    out["session_slice"] = out["entry_ts"].map(_session_slice_et)

    pnl = pd.to_numeric(out[pnl_col], errors="coerce")
    chop = out["shadow_chop_block"].map(lambda x: bool(x) if not pd.isna(x) else False)
    # Counterfactual: if chop had blocked entry, PnL would be 0 vs realized → delta = -pnl
    out["shadow_delta"] = np.where(chop, -pnl, 0.0)

    prev1 = pnl.shift(1)
    prev2 = pnl.shift(2)
    out["sequence_pnl"] = prev1.fillna(0.0) + prev2.fillna(0.0)

    mfe = pd.to_numeric(out.get("exit_mfe_pct"), errors="coerce")
    mae = pd.to_numeric(out.get("exit_mae_pct"), errors="coerce")
    out["mfe_mae_proxy"] = (mfe.fillna(0.0) - mae.fillna(0.0)).replace([np.inf, -np.inf], np.nan)

    thr = 0.25
    mom_cols = [c for c in _SCOREFLOW_MOM if c in out.columns]
    if mom_cols:
        sub = out[mom_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
        out["signal_density"] = (sub > thr).sum(axis=1).astype(int)
    else:
        out["signal_density"] = 0
    out.drop(columns=["_entry_sort"], errors="ignore", inplace=True)
    return out


def _select_feature_matrix(
    df: pd.DataFrame, extra: Sequence[str], max_features: int = 45
) -> Tuple[pd.DataFrame, List[str]]:
    """Numeric columns only; one-hot session bins; cap width for SHAP stability."""
    work = df.copy()
    drop_sub = (
        "trade_id",
        "trade_key",
        "entry_ts",
        "exit_ts",
        "variant_id",
        "composite_version",
        "mlf_entry_uw_uw_intel_source",
        "mlf_entry_uw_uw_intel_version",
        "mlf_ml_feature_source",
        "regime_id",
        "_source_file",
        "ai_approved_v1_backfill_error",
    )
    drop_exact = {
        "symbol",
        "side",
        "session_slice",
        "is_winner",
        "realized_pnl_usd",
        "exit_realized_pnl_usd",
    }
    cols: List[str] = []
    for c in work.columns:
        if c in drop_exact or any(c.startswith(s) for s in drop_sub):
            continue
        if c in extra:
            cols.append(c)
            continue
        if work[c].dtype == object:
            continue
        if str(work[c].dtype).startswith("datetime"):
            continue
        cols.append(c)

    if "session_slice" in work.columns:
        dummies = pd.get_dummies(work["session_slice"].astype(str), prefix="sess")
        if dummies.shape[1] > 16:
            top = dummies.sum().nlargest(16).index
            dummies = dummies[top]
        work = pd.concat([work.drop(columns=["session_slice"], errors="ignore"), dummies], axis=1)
        cols = [c for c in cols if c != "session_slice"] + list(dummies.columns)

    use = [c for c in cols if c in work.columns]
    X = work[use].copy()
    for c in X.columns:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    if X.shape[1] > max_features:
        var = X.var(axis=0).sort_values(ascending=False)
        extra_ok = [c for c in extra if c in X.columns]
        n_base = max_features - len(extra_ok)
        keep = list(dict.fromkeys(extra_ok + list(var.index[:n_base])))
        X = X[[c for c in keep if c in X.columns]]
    return X, list(dict.fromkeys(list(X.columns)))


def _train_classifier(X: np.ndarray, y: np.ndarray) -> Any:
    try:
        from xgboost import XGBClassifier

        return XGBClassifier(
            n_estimators=160,
            max_depth=4,
            min_child_weight=5,
            subsample=0.8,
            colsample_bytree=0.65,
            colsample_bylevel=0.8,
            reg_lambda=2.0,
            reg_alpha=0.2,
            learning_rate=0.06,
            random_state=42,
            n_jobs=-1,
            eval_metric="logloss",
        ).fit(X, y)
    except Exception:
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            min_samples_leaf=8,
            min_samples_split=12,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        ).fit(X, y)


def _top_shap_interactions(
    X: np.ndarray,
    y: np.ndarray,
    feat_names: List[str],
    top_k_features: int = 12,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Refit a compact model on top-K features (by mutual information) so SHAP interaction
    matrix shape matches the explainer (avoids column subset mismatch on full trees).
    """
    from sklearn.feature_selection import mutual_info_classif

    k = min(top_k_features, X.shape[1], max(4, X.shape[1] // 3))
    mi = mutual_info_classif(X, y, discrete_features=False, random_state=42)
    order = np.argsort(-mi)[:k]
    sub_names = [feat_names[i] for i in order]
    X_sub = X[:, order].astype(np.float32)
    sub = _train_classifier(X_sub, y)
    import shap

    expl = shap.TreeExplainer(sub)
    n = min(500, len(X_sub))
    inter = expl.shap_interaction_values(X_sub[:n])
    if isinstance(inter, list):
        inter = inter[1]
    mean_inter = np.nanmean(inter, axis=0)
    p = mean_inter.shape[0]
    pairs: List[Tuple[float, int, int]] = []
    for i in range(p):
        for j in range(i + 1, p):
            pairs.append((float(mean_inter[i, j]), i, j))
    pairs.sort(key=lambda t: t[0])
    toxic: List[Dict[str, Any]] = []
    for val, i, j in pairs:
        if val >= 0:
            break
        toxic.append(
            {
                "feature_i": sub_names[i],
                "feature_j": sub_names[j],
                "mean_shap_interaction": val,
            }
        )
        if len(toxic) >= 3:
            break
    return toxic, sub_names


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=REPO / "reports" / "Alpaca" / "alpaca_ml_cohort_unified.csv")
    ap.add_argument("--out-json", type=Path, default=REPO / "reports" / "Alpaca" / "massive_omniscience_shap.json")
    ap.add_argument("--interaction-features", type=int, default=14, help="Top features for interaction matrix")
    args = ap.parse_args()

    df = pd.read_csv(args.csv, low_memory=False)
    pnl_col = _pnl_col(df)
    pnl = pd.to_numeric(df[pnl_col], errors="coerce")
    mask = np.isfinite(pnl)
    df = df.loc[mask].copy()
    df[pnl_col] = pnl[mask]
    df["is_winner"] = (df[pnl_col] > 0).astype(int)

    df = _engineer_vectors(df, pnl_col)
    for c in ("ai_approved_v1", "shadow_chop_block"):
        if c in df.columns:
            df[c] = df[c].map(
                lambda x: 1.0
                if x is True or (isinstance(x, str) and x.lower() == "true")
                else (0.0 if x is False or (isinstance(x, str) and x.lower() == "false") else 0.0)
            )

    extra = ["sequence_pnl", "shadow_delta", "mfe_mae_proxy", "signal_density"]
    X_df, feat_names = _select_feature_matrix(df, extra=extra)
    y = df["is_winner"].values.astype(int)
    X = X_df.values.astype(np.float32)

    from sklearn.model_selection import train_test_split

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    m_cv = _train_classifier(X_tr, y_tr)
    try:
        from sklearn.metrics import roc_auc_score

        if hasattr(m_cv, "predict_proba"):
            auc_holdout = float(roc_auc_score(y_te, m_cv.predict_proba(X_te)[:, 1]))
            auc_train = float(roc_auc_score(y_tr, m_cv.predict_proba(X_tr)[:, 1]))
        else:
            auc_holdout = auc_train = float("nan")
    except Exception:
        auc_holdout = auc_train = float("nan")

    model = _train_classifier(X, y)

    import shap

    explainer = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(X)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]
    mean_shap = np.mean(np.abs(shap_vals), axis=0)
    top_idx = np.argsort(-mean_shap)[:25]
    top_linear = [
        {"feature": feat_names[i], "mean_abs_shap": float(mean_shap[i])} for i in top_idx[:15]
    ]

    toxic_inter, _sub_feats = _top_shap_interactions(
        X,
        y,
        feat_names,
        top_k_features=min(args.interaction_features, X.shape[1]),
    )

    # Shadow audit: AI False branch
    ai = df["ai_approved_v1"]
    if ai.dtype == object:
        ai_bool = ai.map(lambda x: x is True if isinstance(x, bool) else (str(x).lower() == "true"))
    else:
        ai_bool = ai.fillna(False).astype(bool)
    mask_f = ~ai_bool
    pnl_f = df.loc[mask_f, pnl_col].astype(float)
    net_ai_false = float(pnl_f.sum())
    n_ai_false = int(mask_f.sum())

    win_rate = float(df["is_winner"].mean())
    mean_pnl = float(df[pnl_col].mean())

    report = {
        "rows_used": int(len(df)),
        "pnl_column": pnl_col,
        "win_rate": win_rate,
        "mean_trade_pnl": mean_pnl,
        "roc_auc_train_subset": auc_train,
        "roc_auc_holdout_25pct": auc_holdout,
        "top_mean_abs_shap": top_linear,
        "top_negative_shap_interactions": toxic_inter,
        "shadow_audit": {
            "trades_ai_approved_v1_false": n_ai_false,
            "net_pnl_usd_on_those_trades": net_ai_false,
            "interpretation": "Sum of realized PnL on rows where ai_approved_v1 is not True (False/NaN treated as not approved).",
        },
        "counter_intel_vectors": {
            "session_slice": "15m ET bins from entry_ts",
            "shadow_delta": "-pnl when shadow_chop_block else 0",
            "sequence_pnl": "sum of prior 2 trades pnl",
            "mfe_mae_proxy": "exit_mfe_pct - exit_mae_pct (NaN→0)",
            "signal_density": f"count of scoreflow momentum cols > 0.25 among {len(_SCOREFLOW_MOM)} names",
        },
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
