#!/usr/bin/env python3
"""
Definitive 250-trade OOS review: closed trades + SPI merge_asof + slippage metrics + depth-3 tree.

Defaults: reports/stock_250_OOS_review.csv, reports/Gemini/signal_intelligence_spi_droplet.csv (pull from droplet).
Requires: pandas, numpy, scikit-learn
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
SLIPPAGE_BPS = 0.02 / 100.0
DEFAULT_NOTIONAL = 100.0
BASELINE_WIN_RATE = 0.5859
BASELINE_EXPECTANCY = 0.1638


def _load_spi_joiner_helpers():
    p = REPO_ROOT / "scripts" / "alpaca_spi_joiner.py"
    spec = importlib.util.spec_from_file_location("_alpaca_spi_joiner_mod", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    try:
        import numpy as np
        import pandas as pd
        from sklearn.tree import DecisionTreeClassifier, export_text
    except ImportError as e:
        print(f"Missing dependency: {e}", file=sys.stderr)
        return 1

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--trades",
        type=Path,
        default=REPO_ROOT / "reports" / "stock_250_OOS_review.csv",
    )
    droplet_spi = REPO_ROOT / "reports" / "Gemini" / "signal_intelligence_spi_droplet.csv"
    local_spi = REPO_ROOT / "reports" / "Gemini" / "signal_intelligence_spi.csv"
    ap.add_argument(
        "--spi",
        type=Path,
        default=droplet_spi if droplet_spi.is_file() else local_spi,
    )
    ap.add_argument("--cohort", type=int, default=250, help="Max unique closed trades (most recent first)")
    ap.add_argument("--repo", type=Path, default=REPO_ROOT)
    args = ap.parse_args()
    repo = args.repo.resolve()

    j = _load_spi_joiner_helpers()
    trades_path = args.trades.resolve()
    spi_path = args.spi.resolve()
    if not trades_path.is_file():
        print(f"Missing trades: {trades_path}", file=sys.stderr)
        return 1
    if not spi_path.is_file():
        print(f"Missing SPI: {spi_path}", file=sys.stderr)
        return 1

    trades = pd.read_csv(trades_path)
    raw_n = len(trades)
    trades = trades.drop_duplicates(subset=["trade_id"], keep="first")
    dedup_n = len(trades)
    trades = trades.head(max(1, args.cohort)).copy()

    if "timestamp_utc" in trades.columns:
        trades["timestamp_utc"] = pd.to_datetime(trades["timestamp_utc"], utc=True, errors="coerce")

    entry_map = j.load_entry_ts_from_attribution(repo)
    entry_time, n_csv, n_attr, n_fb = j.build_entry_time(trades, entry_map)
    trades["entry_time"] = entry_time
    trades = trades.dropna(subset=["entry_time"])
    trades["symbol"] = trades["symbol"].astype(str).str.strip().str.upper()
    trades = trades.sort_values(["symbol", "entry_time"], kind="mergesort")

    spi = pd.read_csv(spi_path)
    spi = j.normalize_spi_timestamp_column(spi)
    spi = spi.dropna(subset=["timestamp_utc", "symbol"])
    spi["symbol"] = spi["symbol"].astype(str).str.strip().str.upper()
    spi, spi_dedup = j.dedupe_spi(spi)
    spi = spi.rename(columns={"timestamp_utc": "spi_timestamp_utc"})

    trade_keep = [
        c
        for c in (
            "trade_id",
            "symbol",
            "pnl_usd",
            "realized_pnl",
            "notional",
            "position_size_usd",
            "timestamp_utc",
            "close_reason",
            "entry_score",
            "total_score",
        )
        if c in trades.columns
    ]
    trade_keep = ["entry_time"] + [c for c in trade_keep if c != "entry_time"]
    t2 = trades[trade_keep].copy()

    parts: List[Any] = []
    for sym, g_left in t2.groupby("symbol", sort=False):
        g_left = g_left.sort_values("entry_time", kind="mergesort")
        g_right = spi.loc[spi["symbol"] == sym].sort_values("spi_timestamp_utc", kind="mergesort")
        if g_right.empty:
            out = g_left.copy()
            for c in spi.columns:
                if c not in out.columns:
                    out[c] = np.nan
            parts.append(out)
            continue
        parts.append(
            pd.merge_asof(
                g_left,
                g_right,
                left_on="entry_time",
                right_on="spi_timestamp_utc",
                direction="backward",
            )
        )
    joined = pd.concat(parts, axis=0, ignore_index=True)
    matched = joined["spi_timestamp_utc"].notna()
    staleness_h = (
        joined.loc[matched, "entry_time"] - joined.loc[matched, "spi_timestamp_utc"]
    ).dt.total_seconds() / 3600.0

    pnl_col = next((c for c in ("pnl_usd", "realized_pnl", "realized_pnl_usd") if c in joined.columns), None)
    if not pnl_col:
        print("No PnL column", file=sys.stderr)
        return 1

    def _notional(row: pd.Series) -> float:
        for k in ("notional", "position_size_usd", "notional_usd"):
            if k in row.index and pd.notna(row[k]):
                try:
                    v = float(row[k])
                    if v > 0:
                        return v
                except (TypeError, ValueError):
                    pass
        return DEFAULT_NOTIONAL

    work = joined.copy()
    work["_n"] = work.apply(_notional, axis=1)
    work["_pnl"] = pd.to_numeric(work[pnl_col], errors="coerce")
    work = work.dropna(subset=["_pnl"])
    work["slippage_adjusted_pnl"] = work["_pnl"] - SLIPPAGE_BPS * work["_n"]
    work["is_win"] = (work["slippage_adjusted_pnl"] > 0).astype(int)
    work["_spi_ok"] = work["spi_timestamp_utc"].notna()

    n = len(work)
    wr = float(work["is_win"].mean()) if n else 0.0
    expn = float(work["slippage_adjusted_pnl"].mean()) if n else 0.0

    comp_cols = sorted(c for c in work.columns if str(c).startswith("component_"))
    if not comp_cols:
        print("No component_* columns after join.", file=sys.stderr)
        return 1

    matched_df = work.loc[work["_spi_ok"]].copy()
    n_m = len(matched_df)
    wr_m = float(matched_df["is_win"].mean()) if n_m else 0.0
    expn_m = float(matched_df["slippage_adjusted_pnl"].mean()) if n_m else 0.0

    # Tree on SPI-matched rows only (honest microstructure audit)
    if n_m >= 20:
        tree_df = matched_df
        tree_label = "SPI-matched rows only"
    else:
        tree_df = work
        tree_label = f"full PnL cohort (matched n={n_m}<20; zeros imputed for missing SPI)"
    X = tree_df[comp_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    y = tree_df["is_win"].to_numpy()
    clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=5, random_state=42)
    clf.fit(X, y)
    tree_txt = export_text(clf, feature_names=comp_cols)

    root_feat = comp_cols[clf.tree_.feature[0]] if clf.tree_.children_left[0] != -1 else "(leaf)"
    uses_tox = "component_toxicity_penalty" in tree_txt
    uses_gamma = "component_greeks_gamma" in tree_txt

    print("=" * 76)
    print("Alpaca 250-Trade OOS Definitive Report (local analysis)")
    print("=" * 76)
    print(f"Trades file: {trades_path}")
    print(f"SPI file:    {spi_path}")
    print(f"\n--- Cohort & join ---")
    print(f"  Raw rows in export:     {raw_n}")
    print(f"  After trade_id dedupe:  {dedup_n}")
    print(f"  Cohort cap applied:     {len(trades)} (cap={args.cohort})")
    print(f"  Rows with valid PnL:    {n}")
    print(f"  SPI rows deduped:       {spi_dedup}")
    print(f"  SPI match rate:         {int(matched.sum())} / {len(joined)}")
    if len(staleness_h):
        print(
            f"  Staleness (h): median={staleness_h.median():.4f}, max={staleness_h.max():.4f}"
        )
    print(f"  entry_time: CSV={n_csv}, attribution={n_attr}, close_fallback={n_fb}")

    print(f"\n--- OOS performance (2 bps slippage, default notional ${DEFAULT_NOTIONAL} if missing) ---")
    print(f"  Full cohort (all valid PnL): n={n}")
    print(f"    Win rate:   {wr:.2%}")
    print(f"    Expectancy: ${expn:.4f} / trade")
    print(f"  SPI-matched subset only:     n={n_m}")
    print(f"    Win rate:   {wr_m:.2%}")
    print(f"    Expectancy: ${expn_m:.4f} / trade")
    print(f"\n  Baseline (prior 99-trade review): {BASELINE_WIN_RATE:.2%} win, ${BASELINE_EXPECTANCY:.4f} / trade")
    d_wr = wr - BASELINE_WIN_RATE
    d_ex = expn - BASELINE_EXPECTANCY
    print(f"  Delta vs baseline (full):     {d_wr:+.2%} win, ${d_ex:+.4f} / trade")
    if n_m:
        print(
            f"  Delta vs baseline (matched):  {wr_m - BASELINE_WIN_RATE:+.2%} win, "
            f"${expn_m - BASELINE_EXPECTANCY:+.4f} / trade"
        )

    print(f"\n--- Microstructure tree (depth=3, min_samples_leaf=5) ---")
    print(f"  Training rows: {len(tree_df)} ({tree_label})")
    print(f"  Root split feature: {root_feat}")
    print(f"  Tree text mentions toxicity_penalty: {uses_tox}")
    print(f"  Tree text mentions greeks_gamma:     {uses_gamma}")
    print("\n" + tree_txt)

    print("\n--- Quant verdict (heuristic) ---")
    ref_wr, ref_ex = (wr_m, expn_m) if n_m >= 50 else (wr, expn)
    if ref_wr >= BASELINE_WIN_RATE - 0.02 and ref_ex >= BASELINE_EXPECTANCY - 0.05:
        verdict = (
            "Edge broadly **consistent** with the prior baseline on the reference slice; "
            "not proof of OOS alpha but no obvious collapse."
        )
    elif ref_wr < BASELINE_WIN_RATE - 0.05 or ref_ex < 0:
        verdict = (
            "Material **decay vs baseline** — treat as **not production-cert** until "
            "burst regime, SPI coverage, and selection bias are unpacked."
        )
    else:
        verdict = "Mixed vs baseline — **monitor** and require longer true-OOS before production sign-off."

    prod_book = wr >= 0.52 and expn > 0 and n >= 200
    prod_matched_only = wr_m >= 0.52 and expn_m > 0 and n_m >= 80
    print(f"  Narrative: {verdict}")
    print(
        f"  Book-level production-ready (full n>=200, WR>=52%, exp>0): "
        f"{'YES' if prod_book else 'NO'}"
    )
    print(
        f"  SPI-matched microstructure slice (n>={80}, WR>=52%, exp>0): "
        f"{'YES' if prod_matched_only else 'NO'}"
    )
    print("=" * 76)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
