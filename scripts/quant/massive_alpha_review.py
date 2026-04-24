#!/usr/bin/env python3
"""
Massive Alpha EDA on alpaca_ml_cohort_flat.csv (Vanguard Board pack).

Phases:
  1 — CI / opportunity cost: optional blocked-reason JSON; cohort winner vs loser feature deltas.
  2 — Time-of-day (US/Eastern) buckets vs win rate and mean PnL.
  3 — Holding time vs PnL; average winner vs average loser (realized USD).
  4 — DecisionTreeRegressor(max_depth=2) on top-|corr| numeric features + split summary.
  5 — PCA on standardized numeric slice; top loadings on PC1 + PC1–PC2 synergy (corr).
  6 — Correlation heatmap (subset) -> reports/Gemini/alpha_correlation_heatmap.png
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError as e:  # pragma: no cover
    print("matplotlib/seaborn required:", e, file=sys.stderr)
    sys.exit(1)

try:
    from sklearn.decomposition import PCA
    from sklearn.impute import SimpleImputer
    from sklearn.tree import DecisionTreeRegressor, export_text
except ImportError as e:  # pragma: no cover
    print("scikit-learn required:", e, file=sys.stderr)
    sys.exit(1)

try:
    from zoneinfo import ZoneInfo

    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None


def _load_blocked_reason_summary(path: Path) -> Optional[List[dict]]:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data.get("by_reason") if isinstance(data, dict) else None


def _numeric_feature_matrix(
    df: pd.DataFrame,
    y_col: str,
    max_features: int,
    exclude_substrings: Sequence[str],
) -> Tuple[pd.DataFrame, List[str]]:
    num = df.select_dtypes(include=[np.number]).copy()
    drop = {
        y_col,
        "qty",
        "strict_open_epoch_utc",
        "realized_pnl_usd",
        "exit_price",
        "entry_price",
    }
    for c in list(num.columns):
        if c in drop:
            num.drop(columns=[c], inplace=True)
            continue
        low = any(s in c.lower() for s in exclude_substrings)
        if low:
            num.drop(columns=[c], inplace=True)
    num = num.loc[:, num.columns[num.notna().sum() >= max(20, int(0.05 * len(df)))]]
    if y_col in num.columns:
        num.drop(columns=[y_col], inplace=True, errors="ignore")
    corrs = num.corrwith(df[y_col]).abs().sort_values(ascending=False)
    keep = [c for c in corrs.index if np.isfinite(corrs[c])][:max_features]
    return num[keep], keep


def _entry_hour_et(entry_ts: pd.Series) -> pd.Series:
    if _ET is None:
        return pd.to_datetime(entry_ts, utc=True).dt.hour
    dt = pd.to_datetime(entry_ts, utc=True, errors="coerce")
    return dt.dt.tz_convert(_ET).dt.hour


def _tod_bucket(h: Any) -> str:
    try:
        hi = int(float(h))
    except (TypeError, ValueError):
        return "unknown"
    if hi < 9:
        return "pre_market"
    if hi < 11:
        return "open_morning"
    if hi < 14:
        return "midday_chop"
    if hi < 16:
        return "afternoon_power"
    return "post_rth_et"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--csv",
        type=Path,
        default=REPO_ROOT / "reports" / "Gemini" / "alpaca_ml_cohort_flat.csv",
    )
    ap.add_argument(
        "--blocked-summary",
        type=Path,
        default=REPO_ROOT
        / "reports"
        / "blocked_expectancy"
        / "by_reason_summary_droplet.json",
    )
    ap.add_argument(
        "--out-heatmap",
        type=Path,
        default=REPO_ROOT / "reports" / "Gemini" / "alpha_correlation_heatmap.png",
    )
    ap.add_argument("--max-tree-features", type=int, default=12)
    args = ap.parse_args()

    df = pd.read_csv(args.csv).copy()
    n = len(df)
    print("=== MASSIVE ALPHA REVIEW ===")
    print("rows:", n, "cols:", df.shape[1], "csv:", args.csv)

    y = pd.to_numeric(df["realized_pnl_usd"], errors="coerce")
    win = y > 0
    avg_trade = float(y.mean()) if y.notna().any() else float("nan")
    print(f"\n--- PHASE 0: cohort economics ---\nmean realized_pnl_usd per row: {avg_trade:.4f}")

    # --- PHASE 1 ---
    print("\n--- PHASE 1: CI & opportunity cost ---")
    print(
        "Note: flat cohort rows are **filled / closed** executions only; "
        "per-trade Filled-vs-Blocked labels are not in this CSV."
    )
    br = _load_blocked_reason_summary(args.blocked_summary)
    if br:
        print(f"Loaded blocked-reason summary: {args.blocked_summary}")
        for row in br[:12]:
            r = row.get("reason", "")
            n_ext = row.get("n_extracted", "")
            wr = row.get("win_rate_pct", "")
            hypo = row.get("hypothetical_total_pnl_usd_fixed_notional", "")
            print(f"  blocked_reason={r!r} n={n_ext} replay_win_rate_pct={wr} hypo_usd={hypo}")
    else:
        print("No blocked-reason JSON (or parse failed); Phase 1 uses winner/loser feature gap only.")

    exclude = ("timestamp", "trade_id", "trade_key", "variant", "version", "symbol", "side")
    Xraw, feat_names = _numeric_feature_matrix(
        df.assign(_y=y),
        "_y",
        max_features=40,
        exclude_substrings=exclude,
    )
    med = Xraw.median(numeric_only=True)
    win_m = Xraw.loc[win.fillna(False), feat_names].median()
    loss_m = Xraw.loc[~win.fillna(False) & y.notna(), feat_names].median()
    gap = (win_m - loss_m).abs().sort_values(ascending=False)
    _keep_gap = [
        c
        for c in gap.index
        if not str(c).endswith("_ts_epoch") and "epoch" not in str(c).lower()
    ]
    gap = gap.reindex(_keep_gap).dropna().sort_values(ascending=False)
    print("\nTop 10 features by |median_winner - median_loser| (proxy: what separates wins):")
    for name in gap.head(10).index:
        print(
            f"  {name[:100]}: win_med={win_m[name]:.4g} loss_med={loss_m[name]:.4g} gap={gap[name]:.4g}"
        )

    # --- PHASE 2 ---
    print("\n--- PHASE 2: time-of-day (ET hour from entry_ts) ---")
    if "entry_ts" not in df.columns:
        print("missing entry_ts")
    else:
        h = _entry_hour_et(df["entry_ts"])
        df["_hod"] = h
        df["_bucket"] = h.map(_tod_bucket)
        g = df.groupby("_bucket", dropna=False).agg(
            n=("realized_pnl_usd", "count"),
            win_rate=("realized_pnl_usd", lambda s: (pd.to_numeric(s, errors="coerce") > 0).mean()),
            mean_pnl=("realized_pnl_usd", lambda s: pd.to_numeric(s, errors="coerce").mean()),
        )
        g = g.sort_values("mean_pnl")
        print(g.to_string())
        worst = g["mean_pnl"].idxmin()
        print(f"worst mean_pnl bucket: {worst}")

    # --- PHASE 3 ---
    print("\n--- PHASE 3: duration & yield skew ---")
    ht = pd.to_numeric(df["holding_time_minutes"], errors="coerce")
    corr = ht.corr(y)
    print(f"corr(holding_time_minutes, realized_pnl_usd): {corr:.4f}")
    wvals = y[win & y.notna()]
    lvals = y[~win & y.notna()]
    aw = float(wvals.mean()) if len(wvals) else float("nan")
    al = float(lvals.mean()) if len(lvals) else float("nan")
    print(f"avg winner (realized_pnl_usd): {aw:.4f}  n={len(wvals)}")
    print(f"avg loser  (realized_pnl_usd): {al:.4f}  n={len(lvals)}")
    if np.isfinite(aw) and np.isfinite(al) and al != 0:
        print(f"|avg_winner / avg_loser| ratio: {abs(aw / al):.4f}")

    # --- PHASE 4 ---
    print("\n--- PHASE 4: non-linear tipping (DecisionTreeRegressor max_depth=2) ---")
    tree_feats = feat_names[: int(args.max_tree_features)]
    X = df.reindex(columns=tree_feats).apply(pd.to_numeric, errors="coerce")
    imp = SimpleImputer(strategy="median")
    X_i = imp.fit_transform(X)
    y_clean = y.fillna(0.0).values
    tree = DecisionTreeRegressor(max_depth=2, random_state=42, min_samples_leaf=max(15, n // 80))
    tree.fit(X_i, y_clean)
    print(export_text(tree, feature_names=tree_feats, decimals=3))

    # Leaf win rates
    leaves = tree.apply(X_i)
    print("Leaf stats (mean realized_pnl, win_rate):")
    for leaf in np.unique(leaves):
        m = leaves == leaf
        yy = y.values[m]
        yy = yy[np.isfinite(yy)]
        if len(yy) == 0:
            continue
        wr = (yy > 0).mean()
        print(f"  leaf={leaf} n={len(yy)} mean_pnl={yy.mean():.4f} win_rate={wr*100:.1f}%")

    # --- PHASE 5 ---
    print("\n--- PHASE 5: PCA (super-cluster loadings) ---")
    pca_n = min(8, X_i.shape[1], X_i.shape[0] // 3)
    scaler_mean = X_i.mean(axis=0)
    scaler_std = X_i.std(axis=0, ddof=0)
    scaler_std = np.where(scaler_std < 1e-9, 1.0, scaler_std)
    Z = (X_i - scaler_mean) / scaler_std
    k = min(5, Z.shape[1], Z.shape[0])
    pca = PCA(n_components=k, random_state=42)
    pca.fit(Z)
    load = np.abs(pca.components_[0])
    order = np.argsort(-load)
    print("Top 5 |loadings| on PC1 (move together in primary variance direction):")
    for j in order[:5]:
        print(f"  {tree_feats[j]}: {pca.components_[0][j]:.4f}")
    if pca.n_components_ >= 2:
        syn = np.corrcoef(pca.components_[0], pca.components_[1])[0, 1]
        print(f"corr(PC1 loadings vector, PC2 loadings vector): {syn:.4f} (axis interpretation only)")

    top5_idx = order[:5]
    subcols = [tree_feats[j] for j in top5_idx]
    syn_mat = X[subcols].corr()
    print("\nPairwise corr among top-5 PC1 features:")
    print(syn_mat.round(3).to_string())

    # --- PHASE 6 ---
    print("\n--- PHASE 6: heatmap ---")
    heat_cols = ["realized_pnl_usd", "holding_time_minutes", "exit_mfe_pct", "exit_mae_pct"]
    heat_cols = [c for c in heat_cols if c in df.columns] + subcols[:6]
    heat_cols = list(dict.fromkeys(heat_cols))
    H = df[heat_cols].apply(pd.to_numeric, errors="coerce")
    H = H.loc[:, H.notna().sum() >= max(10, n // 20)]
    cm = H.corr()
    plt.figure(figsize=(max(10, len(cm) * 0.6), max(8, len(cm) * 0.5)))
    sns.heatmap(cm, annot=True, fmt=".2f", cmap="RdBu_r", center=0, square=False)
    plt.title("Alpha correlation heatmap (subset)")
    plt.tight_layout()
    args.out_heatmap.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.out_heatmap, dpi=150)
    plt.close()
    print("wrote", args.out_heatmap.resolve())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
