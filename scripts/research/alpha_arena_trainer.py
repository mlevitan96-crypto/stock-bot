#!/usr/bin/env python3
"""
Alpha 10 arena: regress a favorable-excursion / MFE-style target from mlf_* features.

When ``exit_mfe_pct`` is missing from the CSV (legacy flatten), the trainer can fall back to a
derived proxy. Prefer re-running ``alpaca_ml_flattener`` so ``exit_mfe_pct`` / ``exit_mae_pct`` are
populated from ``exit_quality_metrics``.

**Leakage guard:** any feature column whose name contains ``exit_`` (except the target) or starts
with ``mlf_v2_exit_`` is dropped so we do not regress MFE from exit-state telemetry.

**Chronology guard:** raw epoch / ISO timestamp telemetry columns (``CHRONO_LEAK_FEATURE_NAMES`` and
``mlf_*`` ``*_ts`` / ``*_timestamp`` / ``*ts_epoch*``) are never used as features.

If the requested target column is still missing, this script defaults to a **derived** lower-bound proxy:

  ``derived_favorable_move_pct`` — max(0, favorable price move %) from entry/exit/side
  (equals realized gain in % when the trade was profitable in the position direction; not
  full bar-reconstructed MFE).

Outputs (under ``reports/Gemini/`` by default):
  - alpha_arena_report.json
  - shap_mean_abs_ranking.json  (SHAP when ``shap`` is installed; else permutation importance)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_MFE_CANDIDATES = (
    "exit_mfe_pct",
    "mfe_pct",
    "mlf_exit_quality_mfe_pct",
    "mlf_exit_quality_mfe",
    "mfe_pct_so_far",
)

# Raw clock / trade-open surfaces — must never enter CV as regressors (chronological leakage).
CHRONO_LEAK_FEATURE_NAMES: frozenset[str] = frozenset(
    {
        "strict_open_epoch_utc",
        "mlf_scoreflow_snapshot_ts_epoch",
        "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_ts",
        "mlf_direction_intel_embed_intel_snapshot_entry_timestamp",
        "mlf_direction_intel_embed_intel_snapshot_exit_regime_posture_ts",
        "mlf_direction_intel_embed_intel_snapshot_exit_timestamp",
    }
)


def _is_chrono_leak_feature(name: str) -> bool:
    if not name:
        return False
    if name in CHRONO_LEAK_FEATURE_NAMES:
        return True
    low = name.lower()
    if "ts_epoch" in low:
        return True
    if low.endswith("_timestamp"):
        return True
    if low.endswith("_ts") and low.startswith("mlf_"):
        return True
    return False


def _finite_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return None
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _is_long_side(side_raw: str) -> bool:
    s = (side_raw or "").lower()
    if "short" in s or "sell" in s:
        return False
    if "long" in s or "buy" in s:
        return True
    return True


def _derived_favorable_move_pct(row: Dict[str, str]) -> Optional[float]:
    """Price % move in the favorable direction for the position (0 if adverse). Not true MFE."""
    ep = _finite_float(row.get("entry_price"))
    xp = _finite_float(row.get("exit_price"))
    if ep is None or xp is None or ep <= 0:
        return None
    long_p = _is_long_side(str(row.get("side") or ""))
    if long_p:
        raw = (xp - ep) / ep * 100.0
    else:
        raw = (ep - xp) / ep * 100.0
    return max(0.0, raw)


def _load_csv(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        headers = list(r.fieldnames or [])
        rows = [dict(x) for x in r]
    return headers, rows


def _resolve_target_column(
    headers: Sequence[str],
    rows: Sequence[Dict[str, str]],
    requested: str,
    *,
    allow_proxy: bool,
) -> Tuple[str, str, List[float]]:
    """
    Returns (actual_column_name, resolution_note, y_values).
    """
    hset = set(headers)
    if requested in hset and requested:
        ys = []
        for row in rows:
            v = _finite_float(row.get(requested))
            ys.append(v if v is not None else float("nan"))
        finite = sum(1 for x in ys if math.isfinite(x))
        thr = max(10, len(rows) // 10)
        if finite >= thr:
            return requested, "column_present_in_csv", ys
        if requested.startswith("target_ret_"):
            raise SystemExit(
                f"Target column {requested!r} exists in the CSV but only {finite} finite values "
                f"(need >= {thr}). Refusing to fall back to a different target. "
                f"For RTH labels, check Alpaca Data API access (SIP vs IEX feed) and label_*_reason columns."
            )

    for cand in _MFE_CANDIDATES:
        if cand in hset:
            ys = []
            for row in rows:
                v = _finite_float(row.get(cand))
                ys.append(v if v is not None else float("nan"))
            if sum(1 for x in ys if math.isfinite(x)) >= max(10, len(rows) // 10):
                return cand, f"fallback_csv_column:{cand}", ys

    if not allow_proxy:
        raise SystemExit(
            f"Target column {requested!r} not found or too sparse; no MFE candidates matched. "
            f"Re-run flattener with exit_quality export or pass --allow-mfe-proxy (default on)."
        )

    ys = []
    for row in rows:
        ys.append(_derived_favorable_move_pct(row) or float("nan"))
    return (
        "derived_favorable_move_pct",
        "derived_from_entry_price_exit_price_side_max0_favorable_pct_not_true_bar_mfe",
        ys,
    )


def _is_leaky_exit_feature(name: str, target: str) -> bool:
    """True if column encodes exit-time / exit-leg state (forbidden for entry-only MFE learning)."""
    if not name or name == target:
        return False
    low = name.lower()
    if "exit_" in low:
        return True
    if low.startswith("mlf_v2_exit_"):
        return True
    return False


def _feature_columns(headers: Sequence[str], target: str) -> List[str]:
    skip = {
        target,
        "symbol",
        "side",
        "trade_id",
        "trade_key",
        "entry_ts",
        "exit_ts",
        "exit_price",
        "exit_mae_pct",
        "variant_id",
        "composite_version",
        "mlf_entry_snapshot_match",
        "mlf_ml_feature_source",
        "mlf_scoreflow_join_tier",
        "realized_pnl_usd",
        "holding_time_minutes",
    }
    out: List[str] = []
    for h in headers:
        if not h or h in skip:
            continue
        if _is_leaky_exit_feature(h, target):
            continue
        if _is_chrono_leak_feature(h):
            continue
        if h.startswith("mlf_") or h.startswith("uw_") or h.startswith("mlx_"):
            out.append(h)
    return out


def _build_xy(
    rows: Sequence[Dict[str, str]],
    feat_cols: Sequence[str],
    y: Sequence[float],
) -> Tuple[Any, Any, List[int]]:
    import numpy as np

    keep_idx: List[int] = []
    for i, yi in enumerate(y):
        if math.isfinite(yi):
            keep_idx.append(i)
    if len(keep_idx) < 30:
        raise SystemExit(f"Too few finite targets: {len(keep_idx)}")

    X = np.zeros((len(keep_idx), len(feat_cols)), dtype=np.float64)
    yv = np.zeros(len(keep_idx), dtype=np.float64)
    for out_i, src_i in enumerate(keep_idx):
        yv[out_i] = float(y[src_i])
        for j, c in enumerate(feat_cols):
            X[out_i, j] = _finite_float(rows[src_i].get(c)) or 0.0
    return X, yv, keep_idx


def _drop_sparse_features(X: Any, feat_cols: List[str]) -> Tuple[Any, List[str]]:
    import numpy as np

    n = X.shape[0]
    keep: List[int] = []
    for j in range(X.shape[1]):
        col = X[:, j].astype(np.float64)
        nz = int(np.sum(np.abs(col) > 1e-12))
        std = float(np.nanstd(col))
        if std > 1e-9 or nz >= max(15, int(0.03 * n)):
            keep.append(j)
    if not keep:
        raise SystemExit("All features dropped as sparse; check CSV.")
    cols = [feat_cols[j] for j in keep]
    return X[:, keep], cols


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpha arena: regress MFE-style target vs mlf_* features.")
    ap.add_argument("--csv", type=Path, default=REPO_ROOT / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv")
    ap.add_argument("--target-col", type=str, default="exit_mfe_pct", help="Preferred target (CSV or derived).")
    ap.add_argument(
        "--no-mfe-proxy",
        action="store_true",
        help="Fail if target column missing (do not use derived favorable-move %%).",
    )
    ap.add_argument("--out-dir", type=Path, default=REPO_ROOT / "reports" / "Gemini")
    ap.add_argument("--cv", type=int, default=5)
    ap.add_argument("--random-state", type=int, default=42)
    ap.add_argument(
        "--export-alpha10",
        type=Path,
        default=None,
        help=(
            "Train RandomForestRegressor (entry-only features, same pipeline as arena) on all fit rows "
            "and write a joblib bundle (model + feature_names + impute_medians + meta). Exits after export."
        ),
    )
    args = ap.parse_args()

    csv_path = args.csv.resolve()
    if not csv_path.is_file():
        print(f"Missing CSV: {csv_path}", file=sys.stderr)
        return 1

    try:
        import numpy as np
        from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
        from sklearn.linear_model import ElasticNet, Ridge
        from sklearn.model_selection import KFold, cross_val_score
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as e:
        print(f"Need scikit-learn and numpy: {e}", file=sys.stderr)
        return 1

    headers, rows = _load_csv(csv_path)
    target_name, resolution_note, y_list = _resolve_target_column(
        headers, rows, args.target_col.strip(), allow_proxy=not args.no_mfe_proxy
    )

    feat_cols = _feature_columns(headers, target_name)
    if len(feat_cols) < 4:
        raise SystemExit("Too few feature columns (need mlf_/uw_/mlx_* after leakage filters).")

    X, y, _ = _build_xy(rows, feat_cols, y_list)
    X, feat_cols = _drop_sparse_features(X, feat_cols)

    if args.export_alpha10:
        try:
            import joblib  # type: ignore
        except ImportError:
            print("Need joblib for --export-alpha10 (install scikit-learn stack).", file=sys.stderr)
            return 1
        medians = np.nanmedian(X.astype(np.float64), axis=0)
        rf = RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=3,
            random_state=args.random_state,
            n_jobs=-1,
        )
        rf.fit(X, y)
        out_path = args.export_alpha10.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        bundle = {
            "model": rf,
            "feature_names": list(feat_cols),
            "impute_medians": [float(x) for x in medians.tolist()],
            "target": target_name,
            "target_resolution_note": resolution_note,
            "csv": str(csv_path),
            "n_rows_fit": int(X.shape[0]),
            "n_features": int(X.shape[1]),
            "kind": "alpha10_rf_mfe_bundle_v1",
        }
        joblib.dump(bundle, out_path)
        print(json.dumps({k: v for k, v in bundle.items() if k != "model"}, indent=2))
        print(f"\nWrote Alpha10 bundle: {out_path}")
        return 0

    kf = KFold(n_splits=min(args.cv, len(y)), shuffle=True, random_state=args.random_state)

    models: Dict[str, Any] = {
        "ridge": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("reg", Ridge(alpha=2.0, random_state=args.random_state)),
            ]
        ),
        "elasticnet": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "reg",
                    ElasticNet(alpha=0.01, l1_ratio=0.5, random_state=args.random_state, max_iter=5000),
                ),
            ]
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=3,
            random_state=args.random_state,
            n_jobs=-1,
        ),
        "gradient_boosting": GradientBoostingRegressor(
            random_state=args.random_state,
            max_depth=4,
            learning_rate=0.05,
            n_estimators=200,
        ),
    }

    cv_scores: Dict[str, float] = {}
    for name, est in models.items():
        scores = cross_val_score(est, X, y, cv=kf, scoring="r2", n_jobs=-1)
        cv_scores[name] = float(np.mean(scores))

    winner = max(cv_scores, key=lambda k: cv_scores[k])
    winner_est = models[winner]
    from sklearn.base import clone

    mae_scores = cross_val_score(
        clone(winner_est), X, y, cv=kf, scoring="neg_mean_absolute_error", n_jobs=-1
    )
    winner_cv_mae_mean = float(-np.mean(mae_scores))
    winner_est.fit(X, y)

    shap_path = {}
    top_features: List[Dict[str, Any]] = []

    try:
        import shap  # type: ignore

        explainer = shap.TreeExplainer(winner_est)
        sv = explainer.shap_values(X)
        if isinstance(sv, list):
            sv = sv[0]
        mean_abs = np.mean(np.abs(sv), axis=0)
        order = np.argsort(-mean_abs)
        for rank, j in enumerate(order[:25], start=1):
            top_features.append(
                {"rank": rank, "feature": feat_cols[int(j)], "mean_abs_shap": float(mean_abs[j])}
            )
        shap_path["engine"] = "shap_tree"
    except Exception:
        from sklearn.inspection import permutation_importance

        r = permutation_importance(
            winner_est,
            X,
            y,
            n_repeats=20,
            random_state=args.random_state,
            n_jobs=-1,
            scoring="r2",
        )
        order = np.argsort(-r.importances_mean)
        for rank, j in enumerate(order[:25], start=1):
            top_features.append(
                {
                    "rank": rank,
                    "feature": feat_cols[int(j)],
                    "mean_abs_shap": float(r.importances_mean[j]),
                    "importance_std": float(r.importances_std[j]),
                }
            )
        shap_path["engine"] = "sklearn_permutation_importance_r2"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    chrono_dropped = sorted(h for h in headers if _is_chrono_leak_feature(h))
    report = {
        "csv": str(csv_path),
        "n_rows_total": len(rows),
        "n_rows_fit": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "target_requested": args.target_col,
        "target_resolved": target_name,
        "target_resolution_note": resolution_note,
        "chrono_leak_features_dropped": chrono_dropped,
        "chrono_leak_policy": "CHRONO_LEAK_FEATURE_NAMES + mlf_* *_ts / *_timestamp / *ts_epoch*",
        "entry_only_leak_filter": "drop columns containing exit_ (except target) or starting with mlf_v2_exit_; skip exit_mae_pct, holding_time_minutes, realized_pnl_usd",
        "realized_pnl_column": "realized_pnl_usd",
        "cv_folds": int(kf.n_splits),
        "cv_metric": "r2",
        "cv_scores_by_model": cv_scores,
        "winner_model": winner,
        "winner_cv_r2_mean": cv_scores[winner],
        "winner_cv_mae_mean": winner_cv_mae_mean,
        "winner_cv_mae_note": "same KFold folds, scoring=neg_mean_absolute_error, sklearn inverts sign",
        "importance_method": shap_path.get("engine", "unknown"),
    }

    (args.out_dir / "alpha_arena_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (args.out_dir / "shap_mean_abs_ranking.json").write_text(
        json.dumps({"top": top_features[:50], "meta": shap_path}, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nWrote {args.out_dir / 'alpha_arena_report.json'}")
    print(f"Wrote {args.out_dir / 'shap_mean_abs_ranking.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
