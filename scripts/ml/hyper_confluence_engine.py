#!/usr/bin/env python3
"""
N-dimensional hyper-confluence discovery: high-order feature crosses, XGBoost manifold scan,
optional SHAP interaction values, t-SNE 3D projection, blocked-intent audit, and Markdown report.

**Quant impact:** Surfaces non-linear ``If-A∧B∧C`` regions in PnL space so gates can be
tightened on false positives and relaxed where hyper-volumes show positive expectancy.

Usage (repo root):
  PYTHONPATH=. python scripts/ml/hyper_confluence_engine.py --root . --write-report
  PYTHONPATH=. python scripts/ml/hyper_confluence_engine.py --root /root/stock-bot \\
      --cohort-csv reports/Gemini/alpaca_ml_cohort_flat.csv --out-dir artifacts/ml
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import xgboost as xgb
except ImportError as e:  # pragma: no cover
    raise SystemExit(f"xgboost required: {e}") from e

try:
    import shap

    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

try:
    from sklearn.inspection import permutation_importance
    from sklearn.manifold import TSNE
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    HAS_SK = True
except ImportError as e:  # pragma: no cover
    raise SystemExit(f"scikit-learn required: {e}") from e


# Preferred "theory" columns (first match in cohort CSV wins).
THEORY_COLUMN_PRIORITY: Sequence[str] = (
    "mlf_entry_uw_flow_strength",
    "mlf_entry_uw_darkpool_bias",
    "mlf_scoreflow_components_dark_pool",
    "mlf_scoreflow_components_flow",
    "mlf_scoreflow_components_iv_skew",
    "mlf_scoreflow_total_score",
    "mlf_entry_uw_sentiment_score",
    "mlf_scoreflow_components_toxicity_penalty",
    "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_spy_overnight_ret",
    "mlf_direction_intel_embed_intel_snapshot_entry_volatility_intel_realized_vol_20d",
    "mlf_direction_intel_embed_intel_snapshot_entry_overnight_intel_overnight_dark_pool_imbalance",
    "mlf_direction_intel_embed_intel_snapshot_entry_regime_posture_market_context_qqq_overnight_ret",
    "mlf_scoreflow_components_whale",
    "mlf_scoreflow_components_motif_bonus",
    "holding_time_minutes",
    "exit_mfe_pct",
    "exit_mae_pct",
)


def _safe_float(x: Any) -> float:
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return v
    except (TypeError, ValueError):
        return 0.0


def _pick_theory_columns(df: pd.DataFrame, max_cols: int = 12) -> List[str]:
    cols: List[str] = []
    for name in THEORY_COLUMN_PRIORITY:
        if name in df.columns and name not in cols:
            cols.append(name)
        if len(cols) >= max_cols:
            break
    if len(cols) < 6:
        for c in df.columns:
            if c.startswith("mlf_scoreflow_components_") and c not in cols:
                cols.append(c)
            if len(cols) >= max_cols:
                break
    return cols[:max_cols]


def _numeric_matrix(df: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
    out = df[list(cols)].copy()
    for c in cols:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out.fillna(0.0)


def _build_cross_features(
    base: pd.DataFrame,
    base_names: Sequence[str],
    orders: Tuple[int, ...] = (3, 4, 5),
    max_per_order: int = 150,
    rng: Optional[Any] = None,
) -> Tuple[pd.DataFrame, List[str]]:
    rng = rng or np.random.default_rng(42)
    names = list(base_names)
    series_list: List[pd.Series] = []
    new_cols: List[str] = []
    pools = {n: list(combinations(range(len(names)), n)) for n in orders}
    for n in orders:
        combos = pools[n]
        if len(combos) > max_per_order:
            idx = rng.choice(len(combos), size=max_per_order, replace=False)
            combos = [combos[i] for i in idx]
        for tup in combos:
            parts = [names[i] for i in tup]
            # Prefix ``hc__`` avoids ``x``+``mlf...`` parsing confusion in truncated XGB feature names.
            col = ("hc__" + "__".join(parts))[:200]
            prod = np.ones(len(base), dtype=float)
            for j in tup:
                prod *= base.iloc[:, j].values.astype(float)
            series_list.append(pd.Series(prod, index=base.index, name=col))
            new_cols.append(col)
    Xc = pd.concat(series_list, axis=1) if series_list else pd.DataFrame(index=base.index)
    return Xc, new_cols


def _triad_scores_from_main_effects(mean_abs: np.ndarray, labels: Sequence[str], top_k: int = 5) -> List[Tuple[str, float]]:
    """Geometric mass proxy: score triad (a,b,c) = mean(|SHAP|)_a * mean(|SHAP|)_b * mean(|SHAP|)_c."""
    n = len(labels)
    triads: List[Tuple[str, str, str, float]] = []
    for i, j, k in combinations(range(n), 3):
        s = float(mean_abs[i] * mean_abs[j] * mean_abs[k])
        triads.append((labels[i], labels[j], labels[k], s))
    triads.sort(key=lambda t: -t[3])
    out: List[Tuple[str, float]] = []
    for a, b, c, s in triads[:top_k]:
        out.append((f"{a} :: {b} :: {c}", s))
    return out


def _quartet_scores_main_effects(mean_abs: np.ndarray, labels: Sequence[str], top_k: int = 5) -> List[Tuple[str, float]]:
    quads: List[Tuple[float, str]] = []
    for idxs in combinations(range(len(labels)), 4):
        s = float(np.prod([mean_abs[i] for i in idxs]))
        names = "::".join(labels[i] for i in idxs)
        quads.append((s, names))
    quads.sort(key=lambda t: -t[0])
    return [(nm, sc) for sc, nm in quads[:top_k]]


def _iter_jsonl(path: Path, max_lines: Optional[int] = None) -> Iterable[dict]:
    if not path.is_file():
        return
    lines: List[str] = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        if max_lines:
            deq = f.readlines()
            lines = deq[-max_lines:] if len(deq) > max_lines else deq
        else:
            lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(o, dict):
            yield o


def _load_blocked_intents(root: Path, max_lines: int = 80000) -> pd.DataFrame:
    runp = root / "logs" / "run.jsonl"
    rows: List[dict] = []
    for o in _iter_jsonl(runp, max_lines=max_lines):
        if str(o.get("event_type") or "").lower() != "trade_intent":
            continue
        if str(o.get("decision_outcome") or "").lower() != "blocked":
            continue
        rows.append(
            {
                "symbol": o.get("symbol"),
                "blocked_reason": o.get("blocked_reason") or o.get("reason"),
                "ts": o.get("ts") or o.get("timestamp"),
            }
        )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _fmt_mass(sc: float) -> str:
    if sc != sc:  # NaN
        return "nan"
    ax = abs(float(sc))
    if ax > 0 and ax < 1e-3:
        return f"{float(sc):.4e}"
    return f"{float(sc):.4f}"


def _humanize_feature(fname: str) -> str:
    f = fname.replace("hc__", "").replace("__", " * ").replace("mlf_", "").replace("_", " ")
    if len(f) > 90:
        return f[:87] + "..."
    return f


def _parse_hc_theories(fname: str) -> List[str]:
    """Split ``hc__a__b__c`` into short human labels for each base theory column."""
    if not fname.startswith("hc__"):
        return []
    body = fname[4:]
    parts = [p for p in body.split("__") if p]
    out: List[str] = []
    for p in parts:
        fname_seg = p if p.startswith("mlf_") or p.startswith("exit_") or p.startswith("holding_") else f"mlf_{p}"
        out.append(_humanize_feature(fname_seg))
    return out


def _gut_from_top_gain_feature(top_feat_name: str) -> List[str]:
    """One 4-ingredient recipe: first four theories from the top gain cross, else single feature."""
    theories = _parse_hc_theories(top_feat_name)
    if len(theories) >= 4:
        return theories[:4]
    if len(theories) >= 1:
        return theories
    return [_humanize_feature(top_feat_name)]


def _triad_quartet_from_importance(
    importances: np.ndarray,
    labels: Sequence[str],
    top_k: int = 5,
) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    """Rank triads/quartets by product of non-negative importance masses (SHAP or permutation)."""
    imp = np.maximum(np.asarray(importances, dtype=float).ravel(), 0.0)
    n = min(len(imp), len(labels))
    imp = imp[:n]
    labs = list(labels[:n])
    triads = _triad_scores_from_main_effects(imp, labs, top_k=top_k)
    quartets = _quartet_scores_main_effects(imp, labs, top_k=top_k) if n >= 4 else []
    return triads, quartets


def run_pipeline(
    root: Path,
    cohort_csv: Path,
    out_dir: Path,
    write_report: bool,
    random_state: int = 42,
) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(cohort_csv, low_memory=False)
    if "realized_pnl_usd" not in df.columns:
        raise SystemExit("cohort CSV must contain realized_pnl_usd")
    y = pd.to_numeric(df["realized_pnl_usd"], errors="coerce").fillna(0.0)
    win = (y > 0).astype(int)

    base_names = _pick_theory_columns(df, max_cols=11)
    if len(base_names) < 4:
        raise SystemExit(f"too few theory columns found (got {len(base_names)})")

    Xb = _numeric_matrix(df, base_names)
    Xcross, cross_names = _build_cross_features(
        Xb, base_names, orders=(3, 4, 5), max_per_order=120, rng=np.random.default_rng(random_state)
    )
    X = pd.concat([Xb, Xcross], axis=1)
    # Duplicate / truncated names can yield nested columns that break XGBoost.
    X = X.loc[:, ~X.columns.duplicated(keep="first")]
    X = X.select_dtypes(include=[np.number])
    # Cap width for small-N stability
    if X.shape[1] > 220:
        variances = X.var(axis=0).sort_values(ascending=False)
        keep = list(variances.index[:220])
        X = X[keep]

    mask = np.isfinite(y) & np.isfinite(X.to_numpy()).all(axis=1)
    X = X.loc[mask].reset_index(drop=True)
    y = y.loc[mask].reset_index(drop=True)
    win = win.loc[mask].reset_index(drop=True)

    n = len(X)
    if n < 40:
        raise SystemExit(f"insufficient rows after cleaning: {n}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_state
    )
    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.7,
        reg_lambda=1.5,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    pred = model.predict(X_test)
    mae = float(np.mean(np.abs(pred - y_test)))
    spearman_test, _ = spearmanr(pred, y_test)

    booster = model.get_booster()
    imp = booster.get_score(importance_type="gain")
    # ``get_score`` keys can be truncated vs ``DataFrame`` columns; align ranks to training names.
    if hasattr(model, "feature_names_in_") and model.feature_names_in_ is not None:
        names_all = list(model.feature_names_in_)
        fi = np.asarray(model.feature_importances_, dtype=float)
        fi_order = np.argsort(-fi)
    else:
        names_all = list(X.columns)
        fi = np.asarray(getattr(model, "feature_importances_", np.ones(len(names_all))), dtype=float)
        if fi.shape[0] != len(names_all):
            fi = np.array([float(imp.get(c, 0.0)) for c in names_all], dtype=float)
        fi_order = np.argsort(-fi)

    def _gain_for_column(nm: str, fi_i: float) -> float:
        v = imp.get(nm)
        if v is not None:
            return float(v)
        # Truncated booster keys: pick longest key that is a prefix of ``nm``.
        best_k, best_v = "", 0.0
        for k, gv in imp.items():
            ks = str(k)
            if nm.startswith(ks) and len(ks) > len(best_k):
                best_k, best_v = ks, float(gv)
        if best_k:
            return best_v
        return float(fi_i)

    top_feats = [(names_all[i], _gain_for_column(names_all[i], fi[i])) for i in fi_order[:25]]

    triad_lines: List[Tuple[str, float]] = []
    quartet_lines: List[Tuple[str, float]] = []
    gut_recipe: List[str] = []
    sensitivity_method = "none"
    tsne_summary = ""

    # Rank 3/4-way sensitivity: prefer mean-|SHAP| on a tiny matrix; many XGB+SHAP builds error
    # (chunksize * rows mismatch). Fall back to sklearn permutation importance on the same slice.
    top_k_rank = min(8, len(names_all))
    top_names = [names_all[i] for i in fi_order[:top_k_rank]]
    sample_n = min(96, len(X))
    # XGBoost sklearn wrapper requires the **full** training column set at ``predict`` time.
    X_sh_full = X.iloc[:sample_n].astype(float)
    y_sh = y.iloc[:sample_n].values
    col_index = {nm: i for i, nm in enumerate(X.columns)}
    top_ix = [col_index[nm] for nm in top_names if nm in col_index]

    mean_abs: Optional[np.ndarray] = None

    if HAS_SHAP:
        try:
            explainer = shap.TreeExplainer(model)
            sv = explainer.shap_values(X_sh_full)
            sv_arr = np.asarray(sv)
            if sv_arr.ndim == 1:
                sv_arr = sv_arr.reshape(X_sh_full.shape[0], -1)
            ma_all = np.mean(np.abs(sv_arr), axis=0).ravel()
            mean_abs = np.array([float(ma_all[j]) for j in top_ix], dtype=float)
            sensitivity_method = "mean_abs_shap_top_gain_columns"
        except Exception:  # pragma: no cover
            mean_abs = None

    if mean_abs is None:
        try:
            perm = permutation_importance(
                model,
                X_sh_full,
                y_sh,
                n_repeats=6,
                random_state=random_state,
                n_jobs=-1,
            )
            ma_all = np.abs(perm.importances_mean).astype(float)
            mean_abs = np.array([float(ma_all[j]) for j in top_ix], dtype=float)
            sensitivity_method = "permutation_importance_abs_mean_top_gain_columns"
        except Exception as e:  # pragma: no cover
            triad_lines = [(f"(sensitivity_failed: {str(e)[:200]})", 0.0)]
            sensitivity_method = f"failed: {str(e)[:200]}"

    if mean_abs is not None and mean_abs.size:
        n_ia = min(len(mean_abs), len(top_names))
        mean_abs = mean_abs[:n_ia]
        labels_use = list(top_names[:n_ia])
        triad_lines, quartet_lines = _triad_quartet_from_importance(mean_abs, labels_use, top_k=5)
        if quartet_lines:
            top_q = [x.strip() for x in quartet_lines[0][0].split("::")]
            gut_recipe = [_humanize_feature(x) for x in top_q[:4]]

    if not gut_recipe and top_feats:
        gut_recipe = _gut_from_top_gain_feature(str(top_feats[0][0]))
    if not gut_recipe:
        gut_recipe = ["(no top gain feature)"]

    # t-SNE 3D on scaled numeric subset (theory + top crosses)
    try:
        n_feat = min(50, len(names_all))
        cols_tsne = [names_all[i] for i in fi_order[:n_feat]]
        Z = StandardScaler().fit_transform(X[cols_tsne].astype(float).values)
        perplexity = max(5, min(30, (n - 1) // 3))
        tsne = TSNE(n_components=3, perplexity=perplexity, random_state=random_state, init="pca")
        emb = tsne.fit_transform(Z[: min(n, 500)])
        y_sub = y.values[: emb.shape[0]]
        hi = y_sub >= np.percentile(y_sub, 85)
        lo = y_sub <= np.percentile(y_sub, 15)
        tsne_summary = (
            f"t-SNE 3D on top-{n_feat} gain features, n={emb.shape[0]}, perplexity={perplexity}. "
            f"Top-decile PnL mean={float(np.mean(y_sub[hi])):.4f} vs bottom-decile mean={float(np.mean(y_sub[lo])):.4f}."
        )
        np.savez_compressed(out_dir / "hyper_tsne_embedding.npz", embedding=emb, y=y_sub, hi=hi, lo=lo)
    except Exception as e:  # pragma: no cover
        tsne_summary = f"t-SNE skipped: {e}"

    X.to_csv(out_dir / "hyper_features_matrix.csv.gz", index=False, compression="gzip")
    pd.DataFrame(top_feats, columns=["feature", "gain"]).to_csv(out_dir / "hyper_xgb_gain_rank.csv", index=False)

    blocked_df = _load_blocked_intents(root, max_lines=100000)
    blocked_n = len(blocked_df)

    report_path = out_dir / "HYPER_CONFLUENCE_REPORT.md"
    if write_report:
        lines: List[str] = []
        lines.append("# Hyper-Confluence Manifold Report")
        lines.append("")
        lines.append("**Generated:** `scripts/ml/hyper_confluence_engine.py`")
        lines.append("")
        lines.append("## 1. Data inventory")
        lines.append(f"- **Cohort:** `{cohort_csv}`")
        lines.append(f"- **Rows (clean):** {n}")
        lines.append(f"- **Base theory columns:** {len(base_names)}")
        lines.append(f"- **Cross features (3/4/5-way products):** {len(cross_names)} (capped per order)")
        lines.append(f"- **Blocked intents sampled:** {blocked_n} (from `logs/run.jsonl` tail)")
        lines.append("")
        lines.append("## 2. Gradient boosted manifold (XGBoost regressor → realized PnL USD)")
        lines.append(f"- **Test MAE (USD):** {mae:.4f}")
        lines.append(f"- **Test Spearman(pred, y):** {float(spearman_test) if spearman_test == spearman_test else float('nan'):.4f}")
        lines.append("")
        lines.append("### Top 12 gain features")
        for feat, g in top_feats[:12]:
            lines.append(f"- `{feat}` — gain {g:.1f}")
        lines.append("")
        lines.append("## 3. High-order sensitivity (triads & quartets)")
        lines.append(
            f"_Method:_ `{sensitivity_method}` — product of per-feature masses over the top-{top_k_rank} "
            "gain columns (SHAP mean-|value| when available; else sklearn `permutation_importance`). "
            "This ranks **which simultaneous feature bundle** the booster leans on; it is **not** the full "
            "SHAP interaction tensor (omitted here for XGBoost+SHAP stability on wide models)."
        )
        if not HAS_SHAP:
            lines.append("_Note: `shap` not installed; permutation-only path._")
        lines.append("### Top triads (3-way geometric mass)")
        for name, sc in triad_lines:
            lines.append(f"- **{_fmt_mass(sc)}** — `{name}`")
        lines.append("")
        lines.append("### Top quartets")
        for name, sc in quartet_lines:
            lines.append(f"- **{_fmt_mass(sc)}** — `{name}`")
        lines.append("")
        lines.append("## 4. Manifold projection (t-SNE 3D)")
        lines.append(tsne_summary)
        lines.append("")
        lines.append("## 5. Lost World — blocked intents vs hyper-volumes")
        lines.append(
            "Counterfactual PnL for blocked rows requires joining each intent timestamp to post-trade "
            "outcomes (replay or forward marks). **Heuristic audit:** compare `blocked_reason` histogram "
            "to top gain crosses; if `score_below_min` dominates while crosses show edge, floor may be "
            "mis-calibrated vs confluence."
        )
        if blocked_n > 0 and "blocked_reason" in blocked_df.columns:
            br = blocked_df["blocked_reason"].fillna("unknown").astype(str).value_counts().head(12)
            lines.append("")
            lines.append("| blocked_reason (top) | count |")
            lines.append("|---|---:|")
            for k, v in br.items():
                lines.append(f"| {k} | {int(v)} |")
        lines.append("")
        lines.append("## 6. Grand Unified Theory (single 4-ingredient recipe)")
        lines.append(
            "_Operational definition:_ the four base signals named in the **top quartet** above "
            "(or, if absent, the first four theories inside the **#1 gain cross** `hc__…`). "
            "Validate OOS; descriptive only."
        )
        lines.append("")
        for i, item in enumerate(gut_recipe, 1):
            lines.append(f"{i}. **{item}**")
        lines.append("")
        lines.append("---")
        lines.append("*This report is descriptive, not prescriptive for live routing. Validate on hold-out eras.*")
        report_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "rows": n,
        "mae": mae,
        "spearman": float(spearman_test) if spearman_test == spearman_test else None,
        "sensitivity_method": sensitivity_method,
        "top_feats": top_feats[:12],
        "triads": triad_lines,
        "quartets": quartet_lines,
        "gut": gut_recipe,
        "report": str(report_path) if write_report else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Hyper-confluence engine + HYPER_CONFLUENCE_REPORT.md")
    ap.add_argument("--root", type=Path, default=REPO_ROOT)
    ap.add_argument(
        "--cohort-csv",
        type=Path,
        default=None,
        help="Default: <root>/reports/Gemini/alpaca_ml_cohort_flat.csv",
    )
    ap.add_argument("--out-dir", type=Path, default=None, help="Default: <root>/artifacts/ml")
    ap.add_argument("--write-report", action="store_true", help="Write artifacts/ml/HYPER_CONFLUENCE_REPORT.md")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    root = args.root.resolve()
    cohort = args.cohort_csv or (root / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv")
    out_dir = args.out_dir or (root / "artifacts" / "ml")
    if not cohort.is_file():
        # Allow droplet-only path under artifacts
        alt = root / "artifacts" / "alpaca_ml_cohort_flat.csv"
        if alt.is_file():
            cohort = alt
        else:
            raise SystemExit(f"missing cohort csv: {cohort}")
    summary = run_pipeline(root, cohort, out_dir, write_report=args.write_report, random_state=args.seed)
    print(json.dumps({k: v for k, v in summary.items() if k != "top_feats"}, indent=2, default=str))
    print("top_feats:", summary.get("top_feats"))


if __name__ == "__main__":
    main()
