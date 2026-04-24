"""
Harvester cohort calibration gate: L2-regularized win/loss model vs legacy total_score.

Institutional safeguards:
  - Training cohort: strict_scoreflow + skip_neutral_no_join=True (Real Join), same cutoff as milestones.
  - Sparse UW features (e.g. mlf_entry_uw_earnings_proximity) stay in the feature matrix — never dropped
    for low variance; L2 shrinks them instead of one-hot dropping.
  - Rows with mlf_scoreflow_total_score_imputed truthy get reduced sample_weight so imputed neutrals
    do not dominate the fit.
  - OLD signal: mlf_scoreflow_total_score (current normalization contract in flat CSV).
  - NEW signal: sklearn LogisticRegression L2 decision_function on z-scored features (no leakage from
    total_score into X — components + UW scalars only).

Promotion gate (default full model): PF on top 50% of trades by score must improve by >= 10% for NEW vs OLD.

Precision-narrow mode (--precision-narrow): X = congress + smile + entry_uw sentiment only; L2 C=0.1;
imputed scoreflow rows still sample_weight=0.25. Promotion requires BOTH the 10% PF gate AND strictly
positive mean time-series CV delta (top-half PF_new − PF_old).
"""
from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

# High-conviction narrow set (Quant mandate — precision calibration).
PRECISION_NARROW_FEATURES: Tuple[str, ...] = (
    "mlf_scoreflow_components_congress",
    "mlf_scoreflow_components_smile",
    "mlf_entry_uw_sentiment_score",
)

# Always retain these UW columns if present; if absent from CSV, synthetic zero column (sparse OK).
UW_NUMERIC_FEATURES = (
    "mlf_entry_uw_sentiment_score",
    "mlf_entry_uw_earnings_proximity",
    "mlf_entry_uw_flow_strength",
    "mlf_entry_uw_darkpool_bias",
    "mlf_entry_uw_regime_alignment",
    "mlf_entry_uw_sector_alignment",
)


def _strict_epoch_dt() -> datetime:
    from telemetry.alpaca_strict_completeness_gate import STRICT_EPOCH_START

    return datetime.fromtimestamp(float(STRICT_EPOCH_START), tz=timezone.utc)


def _since_datetime_utc() -> datetime:
    floor = _strict_epoch_dt()
    raw = (os.environ.get("TELEMETRY_MILESTONE_SINCE_DATE") or "").strip()
    if not raw:
        return floor
    try:
        y, m, d = (int(x) for x in raw.split("-", 2))
        env_start = datetime(y, m, d, tzinfo=timezone.utc)
    except Exception:
        return floor
    return env_start if env_start >= floor else floor


def _cohort_since_cutoff(
    kept: List[Dict[str, str]], cutoff: datetime,
) -> List[Dict[str, str]]:
    from src.ml.alpaca_cohort_train import _entry_epoch_from_flat_row

    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    ts_cut = cutoff.timestamp()
    out: List[Dict[str, str]] = []
    for row in kept:
        ep = _entry_epoch_from_flat_row(row)
        if ep is None or ep < ts_cut:
            continue
        out.append(row)
    return out


def _finite_float(x: Any) -> Optional[float]:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _profit_factor(pnls: Sequence[float]) -> Optional[float]:
    gw = sum(p for p in pnls if p > 0)
    gl = sum(p for p in pnls if p < 0)
    if gl >= 0:
        return None
    return gw / abs(gl)


def _win_rate(pnls: Sequence[float]) -> float:
    if not pnls:
        return 0.0
    return sum(1 for p in pnls if p > 0) / len(pnls)


def _top_fraction_metrics(
    pnls: List[float], scores: List[float], frac: float = 0.5,
) -> Dict[str, Any]:
    n = len(pnls)
    if n == 0:
        return {"n": 0, "profit_factor": None, "win_rate": 0.0}
    k = max(1, int(round(n * frac)))
    idx = sorted(range(n), key=lambda i: scores[i], reverse=True)
    sel = [pnls[i] for i in idx[:k]]
    return {
        "n": k,
        "fraction": frac,
        "profit_factor": _profit_factor(sel),
        "win_rate": _win_rate(sel),
    }


def _imputed_row(row: Dict[str, str]) -> bool:
    v = str(row.get("mlf_scoreflow_total_score_imputed") or "").strip().lower()
    return v in ("1", "true", "yes")


def _build_feature_matrix(
    rows: List[Dict[str, str]],
    feature_cols: List[str],
    *,
    imputed_weight: float,
    require_finite: frozenset,
    default_zero_if_missing: frozenset,
) -> Tuple[Any, List[str], List[float], List[float], List[float], List[float]]:
    """Returns X, feature_names, pnls, old_scores, sample_weights, sort_epoch."""
    import numpy as np

    pnls: List[float] = []
    old_scores: List[float] = []
    weights: List[float] = []
    epochs: List[float] = []
    feat_names = list(feature_cols)
    X_list: List[List[float]] = []

    for row in rows:
        p = _finite_float(row.get("realized_pnl_usd"))
        if p is None:
            continue
        old = _finite_float(row.get("mlf_scoreflow_total_score"))
        if old is None:
            continue
        vec: List[float] = []
        ok = True
        for c in feature_cols:
            fv = _finite_float(row.get(c))
            if c in default_zero_if_missing:
                vec.append(0.0 if fv is None else fv)
            elif c in require_finite:
                if fv is None:
                    ok = False
                    break
                vec.append(fv)
            else:
                raise ValueError(f"feature {c!r} not in require_finite or default_zero_if_missing")
        if not ok:
            continue
        X_list.append(vec)
        pnls.append(p)
        old_scores.append(old)
        weights.append(imputed_weight if _imputed_row(row) else 1.0)
        ep = _finite_float(row.get("strict_open_epoch_utc"))
        epochs.append(float(ep) if ep is not None else 0.0)

    if not X_list:
        raise ValueError("empty feature matrix")
    X = np.asarray(X_list, dtype=np.float64)
    return X, feat_names, pnls, old_scores, weights, epochs


@dataclass
class CalibrationResult:
    promotion_ok: bool
    pf_improvement_ratio: Optional[float]
    report: Dict[str, Any]


def run_calibration_gate(
    csv_path: Path,
    *,
    json_out: Optional[Path] = None,
    pf_gate_mult: float = 1.10,
    top_frac: float = 0.5,
    l2_c: Optional[float] = None,
    imputed_weight: float = 0.25,
    narrow_precision: bool = False,
    require_positive_cv: Optional[bool] = None,
) -> CalibrationResult:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    import numpy as np

    from src.ml.alpaca_cohort_train import load_and_filter
    from telemetry.ml_scoreflow_contract import mlf_scoreflow_component_column_names

    if require_positive_cv is None:
        require_positive_cv = bool(narrow_precision)
    if l2_c is None:
        l2_c = 0.1 if narrow_precision else 0.35

    csv_path = csv_path.resolve()
    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)

    cutoff = _since_datetime_utc()
    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        import csv as csv_mod

        headers = list((csv_mod.DictReader(f).fieldnames or []))

    _, kept_all, stats = load_and_filter(
        csv_path,
        feature_mode="strict_scoreflow",
        require_join_tier=None,
        skip_neutral_no_join=True,
    )
    cohort = _cohort_since_cutoff(kept_all, cutoff)

    sf_cols = [c for c in mlf_scoreflow_component_column_names() if c in headers]
    if len(sf_cols) != len(mlf_scoreflow_component_column_names()):
        missing = set(mlf_scoreflow_component_column_names()) - set(sf_cols)
        raise ValueError(f"CSV missing scoreflow columns: {sorted(missing)[:12]}")

    if narrow_precision:
        feat_names = list(PRECISION_NARROW_FEATURES)
        for c in feat_names:
            if c not in headers:
                raise ValueError(f"CSV missing precision feature column: {c}")
        req_fin = frozenset(
            {"mlf_scoreflow_components_congress", "mlf_scoreflow_components_smile"}
        )
        zero_if_miss = frozenset({"mlf_entry_uw_sentiment_score"})
        mode = "precision_narrow"
        sparse_note = list(PRECISION_NARROW_FEATURES)
    else:
        uw_cols = list(UW_NUMERIC_FEATURES)
        feat_names = sf_cols + uw_cols
        req_fin = frozenset(sf_cols)
        zero_if_miss = frozenset(uw_cols)
        mode = "full"
        sparse_note = list(UW_NUMERIC_FEATURES)

    X, feat_names_out, pnls, old_scores, sw_list, epochs = _build_feature_matrix(
        cohort,
        feat_names,
        imputed_weight=imputed_weight,
        require_finite=req_fin,
        default_zero_if_missing=zero_if_miss,
    )
    assert feat_names_out == feat_names
    sw = np.asarray(sw_list, dtype=np.float64)
    y = np.asarray([1 if p > 0 else 0 for p in pnls], dtype=np.int64)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    clf = LogisticRegression(
        penalty="l2",
        C=l2_c,
        class_weight="balanced",
        solver="lbfgs",
        max_iter=2000,
        random_state=42,
    )
    clf.fit(Xs, y, sample_weight=sw)
    new_scores = clf.decision_function(Xs).tolist()

    all_metrics = {
        "n": len(pnls),
        "profit_factor": _profit_factor(pnls),
        "win_rate": _win_rate(pnls),
    }
    old_top = _top_fraction_metrics(pnls, old_scores, top_frac)
    new_top = _top_fraction_metrics(pnls, new_scores, top_frac)

    pf_old = old_top.get("profit_factor")
    pf_new = new_top.get("profit_factor")
    ratio: Optional[float] = None
    pf_pass = False
    if pf_old is not None and pf_old > 0 and pf_new is not None:
        ratio = pf_new / pf_old
        pf_pass = pf_new >= pf_old * pf_gate_mult
    elif pf_new is not None and (pf_old is None or pf_old <= 0):
        pf_pass = pf_new is not None and pf_new > 1.0

    coef = clf.coef_[0]
    scale = scaler.scale_.copy()
    scale[scale == 0] = 1.0
    raw_approx = coef / scale
    intercept = float(clf.intercept_[0])
    weighting_matrix = {
        "intercept_decision_function": intercept,
        "features": [
            {
                "name": n,
                "coef_on_standardized_X": float(c),
                "weight_raw_scale_approx": float(w),
                "scaler_mean": float(scaler.mean_[i]),
                "scaler_scale": float(scaler.scale_[i]) if scaler.scale_[i] != 0 else 1.0,
            }
            for i, (n, w, c) in enumerate(zip(feat_names, raw_approx, coef))
        ],
    }
    ranked = sorted(
        zip(feat_names, raw_approx, coef),
        key=lambda t: abs(t[1]),
        reverse=True,
    )
    top5 = [
        {
            "feature": n,
            "weight_raw_scale_approx": float(w),
            "coef_standardized": float(c),
        }
        for n, w, c in ranked[:5]
    ]
    rank_full = [
        {"feature": n, "weight_raw_scale_approx": float(w), "coef_standardized": float(c)}
        for n, w, c in ranked[:40]
    ]

    # Time-series CV: sort by strict_open_epoch_utc then evaluate top-frac PF on test folds
    cv_note: Dict[str, Any] = {"folds": 0, "mean_delta_pf_top_half": None}
    try:
        order = sorted(range(len(epochs)), key=lambda i: epochs[i])
        X_ord = X[np.asarray(order)]
        y_ord = y[order]
        sw_ord = sw[order]
        pnl_ord = [pnls[i] for i in order]
        old_ord = [old_scores[i] for i in order]
        tss = TimeSeriesSplit(n_splits=min(5, max(2, len(pnl_ord) // 40)))
        deltas: List[float] = []
        for tr, te in tss.split(X_ord):
            if len(te) < 10:
                continue
            sc = StandardScaler()
            Xtr = sc.fit_transform(X_ord[tr])
            Xte = sc.transform(X_ord[te])
            cl = LogisticRegression(
                penalty="l2", C=l2_c, class_weight="balanced", solver="lbfgs", max_iter=2000, random_state=42
            )
            cl.fit(Xtr, y_ord[tr], sample_weight=sw_ord[tr])
            te_pnls = [pnl_ord[i] for i in te]
            te_old = [old_ord[i] for i in te]
            te_new = cl.decision_function(Xte).tolist()
            pfo = _top_fraction_metrics(te_pnls, te_old, top_frac).get("profit_factor")
            pfn = _top_fraction_metrics(te_pnls, te_new, top_frac).get("profit_factor")
            if pfo is not None and pfn is not None and pfo > 0:
                deltas.append(pfn - pfo)
        if deltas:
            cv_note = {
                "folds": len(deltas),
                "mean_delta_pf_top_half": float(sum(deltas) / len(deltas)),
            }
    except Exception as e:
        cv_note["error"] = str(e)

    md = cv_note.get("mean_delta_pf_top_half")
    cv_pass = True
    if require_positive_cv:
        cv_pass = md is not None and float(md) > 0.0
    promotion_ok = bool(pf_pass and cv_pass)

    report: Dict[str, Any] = {
        "calibration_mode": mode,
        "cutoff_utc": cutoff.isoformat(),
        "csv": str(csv_path),
        "strict_filter_stats": stats,
        "cohort_rows_since_cutoff": len(cohort),
        "training_rows_after_finite_gate": len(pnls),
        "imputed_row_downweight": imputed_weight,
        "l2_C": l2_c,
        "top_fraction_for_gate": top_frac,
        "pf_improvement_required": pf_gate_mult,
        "require_positive_cv": require_positive_cv,
        "pf_gate_passed": pf_pass,
        "cv_positive_passed": cv_pass,
        "all_trades": all_metrics,
        "old_total_score_top_slice": old_top,
        "new_calibrated_top_slice": new_top,
        "profit_factor_ratio_new_over_old": ratio,
        "win_rate_old_top_slice": old_top.get("win_rate"),
        "win_rate_new_top_slice": new_top.get("win_rate"),
        "top5_feature_weights": top5,
        "weighting_matrix": weighting_matrix,
        "feature_rank_top40": rank_full,
        "sparse_features_always_included": sparse_note,
        "time_series_cv": cv_note,
        "READY_FOR_LIVE_PROMOTION": promotion_ok,
    }

    if json_out:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")

    return CalibrationResult(
        promotion_ok=promotion_ok,
        pf_improvement_ratio=ratio,
        report=report,
    )


def print_report(report: Dict[str, Any]) -> None:
    print("=== Harvester Calibration / Backtest Comparison ===")
    print(f"mode: {report.get('calibration_mode', 'full')}")
    print(f"cohort_rows: {report['cohort_rows_since_cutoff']}  training_rows: {report['training_rows_after_finite_gate']}")
    print(f"L2_C: {report.get('l2_C')}  imputed_scoreflow_downweight: {report['imputed_row_downweight']}")
    print(
        f"PF gate passed: {report.get('pf_gate_passed')}  "
        f"CV positive required: {report.get('require_positive_cv')}  "
        f"CV passed: {report.get('cv_positive_passed')}"
    )
    print()
    print("--- All trades (same PnL set) ---")
    print(json.dumps(report["all_trades"], indent=2))
    print()
    print("--- Top slice by OLD score (mlf_scoreflow_total_score) ---")
    print(json.dumps(report["old_total_score_top_slice"], indent=2))
    print()
    print("--- Top slice by NEW calibrated score ---")
    print(json.dumps(report["new_calibrated_top_slice"], indent=2))
    print()
    print(f"PF ratio (new/old top slice): {report['profit_factor_ratio_new_over_old']}")
    print(f"Win rate OLD top slice: {report['win_rate_old_top_slice']}")
    print(f"Win rate NEW top slice: {report['win_rate_new_top_slice']}")
    print()
    print("--- Top 5 calibrated feature weights (raw-scale approx = coef / feature_std) ---")
    for i, row in enumerate(report["top5_feature_weights"], 1):
        print(
            f"  {i}. {row['feature']}  raw~{row['weight_raw_scale_approx']:.6f}  "
            f"std_coef={row['coef_standardized']:.6f}"
        )
    print()
    print(f"Time-series CV: {report['time_series_cv']}")
    print()
    wm = report.get("weighting_matrix")
    if wm:
        print("--- Weighting matrix (logistic decision function) ---")
        print(json.dumps(wm, indent=2))
        print()
    print(f"READY FOR LIVE PROMOTION: {'YES' if report['READY_FOR_LIVE_PROMOTION'] else 'NO'}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Harvester calibration gate (L2 logistic vs total_score).")
    ap.add_argument("--csv", type=Path, default=REPO_ROOT / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv")
    ap.add_argument("--json-out", type=Path, default=REPO_ROOT / "reports" / "Gemini" / "harvester_calibration_gate.json")
    ap.add_argument("--pf-gate-mult", type=float, default=1.10)
    ap.add_argument("--top-frac", type=float, default=0.5)
    ap.add_argument(
        "--precision-narrow",
        action="store_true",
        help="3-feature high-conviction set + C=0.1 + require positive CV for promotion",
    )
    ap.add_argument("--l2-c", type=float, default=None, help="Override L2 C (default: 0.35 full, 0.1 narrow)")
    args = ap.parse_args(list(argv) if argv is not None else None)

    jout = args.json_out
    if args.precision_narrow and args.json_out == (
        REPO_ROOT / "reports" / "Gemini" / "harvester_calibration_gate.json"
    ):
        jout = REPO_ROOT / "reports" / "Gemini" / "harvester_calibration_gate_precision.json"

    try:
        res = run_calibration_gate(
            args.csv,
            json_out=jout,
            pf_gate_mult=args.pf_gate_mult,
            top_frac=args.top_frac,
            l2_c=args.l2_c,
            narrow_precision=args.precision_narrow,
        )
    except Exception as e:
        print(f"Calibration gate failed: {e}", file=sys.stderr)
        return 1
    print_report(res.report)
    return 0 if res.promotion_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
