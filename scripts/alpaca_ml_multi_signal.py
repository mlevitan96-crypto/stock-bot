#!/usr/bin/env python3
"""
Temporary Alpaca equities multi-signal review: slippage-adjusted baseline + shallow decision tree.

Loads reports/stock_100_trades_clean.csv (path configurable).
Requires: numpy, scikit-learn
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]

FEATURE_PATTERN = re.compile(r"score|flow|dark_pool|greeks|component_|uw_", re.I)
SLIPPAGE_BPS = 0.02 / 100.0  # 2 bps
DEFAULT_NOTIONAL_USD = 100.0


def _to_float(x: Any) -> Optional[float]:
    if x is None or x == "":
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_trades(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        headers = list(r.fieldnames or [])
        rows = [dict(row) for row in r]
    return headers, rows


def pick_pnl(row: Dict[str, str]) -> Optional[float]:
    for k in ("realized_pnl", "pnl_usd", "realized_pnl_usd", "pnl"):
        if k in row:
            v = _to_float(row.get(k))
            if v is not None:
                return v
    return None


def pick_notional(row: Dict[str, str]) -> float:
    for k in ("notional", "position_size_usd", "notional_usd", "size_usd"):
        v = _to_float(row.get(k))
        if v is not None and v > 0:
            return v
    return DEFAULT_NOTIONAL_USD


def feature_columns(headers: Sequence[str]) -> List[str]:
    out: List[str] = []
    skip = {
        "trade_id",
        "timestamp_utc",
        "symbol",
        "close_reason",
        "is_win",
        "realized_pnl",
        "pnl_usd",
        "realized_pnl_usd",
        "pnl",
        "slippage_adjusted_pnl",
        "notional",
        "position_size_usd",
        "notional_usd",
        "size_usd",
    }
    for h in headers:
        if not h or h in skip:
            continue
        if FEATURE_PATTERN.search(h):
            out.append(h)
    return out


def rows_to_matrix(rows: List[Dict[str, str]], cols: List[str], *, strict_finite: bool = False) -> np.ndarray:
    X = np.zeros((len(rows), len(cols)), dtype=np.float64)
    for i, row in enumerate(rows):
        for j, c in enumerate(cols):
            v = _to_float(row.get(c))
            if strict_finite and (v is None or not np.isfinite(v)):
                raise ValueError(f"strict_finite: missing/NaN feature {c!r} row {i}")
            X[i, j] = 0.0 if v is None or not np.isfinite(v) else float(v)
    return X


def filter_rows_strict_finite_features(
    rows: List[Dict[str, str]], cols: List[str]
) -> List[Dict[str, str]]:
    """Drop rows with any missing/non-finite value in cols (no imputation)."""
    out: List[Dict[str, str]] = []
    for row in rows:
        ok = True
        for c in cols:
            v = _to_float(row.get(c))
            if v is None or not np.isfinite(v):
                ok = False
                break
        if ok:
            out.append(row)
    return out


def leaf_paths_with_stats(
    tree_,
    feature_names: List[str],
) -> List[Dict[str, Any]]:
    """Collect each leaf's rule path and win concentration (sklearn value = class proportions)."""
    results: List[Dict[str, Any]] = []

    def recurse(node_id: int, rules: List[str]) -> None:
        left = tree_.children_left[node_id]
        if left == -1:
            v = tree_.value[node_id][0]
            n = int(tree_.n_node_samples[node_id])
            # value[node] holds normalized class proportions (sum to 1) for this sklearn version
            p_win = float(v[1]) if len(v) > 1 else 0.0
            wins = int(round(p_win * n)) if n else 0
            results.append(
                {
                    "rules": list(rules),
                    "n_samples": n,
                    "wins": wins,
                    "win_rate": p_win if n else 0.0,
                }
            )
            return
        right = tree_.children_right[node_id]
        feat = tree_.feature[node_id]
        thr = tree_.threshold[node_id]
        name = feature_names[feat] if feat >= 0 else f"feature_{feat}"
        recurse(left, rules + [f"{name} <= {thr:.6g}"])
        recurse(right, rules + [f"{name} > {thr:.6g}"])

    recurse(0, [])
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca 100-trade multi-signal decision tree review")
    ap.add_argument(
        "--csv",
        type=Path,
        default=REPO_ROOT / "reports" / "stock_100_trades_clean.csv",
        help="Path to stock_100_trades_clean.csv",
    )
    ap.add_argument(
        "--strict-gold-features",
        action="store_true",
        help="Drop any row with missing/NaN in selected feature columns before training (no zero-fill).",
    )
    args = ap.parse_args()
    path = args.csv.resolve()
    if not path.is_file():
        print(f"Missing CSV: {path}", file=sys.stderr)
        return 1

    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
    except ImportError:
        print("Install scikit-learn: pip install scikit-learn", file=sys.stderr)
        return 1

    headers, rows = load_trades(path)
    if not rows:
        print("No rows in CSV.", file=sys.stderr)
        return 1

    enriched: List[Dict[str, str]] = []
    pnls_adj: List[float] = []
    for row in rows:
        pnl = pick_pnl(row)
        if pnl is None:
            continue
        n = pick_notional(row)
        slip_cost = SLIPPAGE_BPS * n
        adj = pnl - slip_cost
        r = dict(row)
        r["_slippage_adjusted_pnl"] = adj
        r["_notional_used"] = n
        enriched.append(r)
        pnls_adj.append(adj)

    if not enriched:
        print("No rows with usable PnL.", file=sys.stderr)
        return 1

    feat_cols = feature_columns(headers)
    if not feat_cols:
        print("No feature columns matched (score/flow/dark_pool/greeks/component_/uw_).", file=sys.stderr)
        return 1

    if args.strict_gold_features:
        before = len(enriched)
        enriched = filter_rows_strict_finite_features(enriched, feat_cols)
        dropped = before - len(enriched)
        if dropped:
            print(f"strict_gold_features: dropped {dropped} rows with incomplete features ({len(enriched)} kept).")
        if not enriched:
            print("No rows left after strict feature filter.", file=sys.stderr)
            return 1
        X = rows_to_matrix(enriched, feat_cols, strict_finite=True)
    else:
        X = rows_to_matrix(enriched, feat_cols)

    y = np.array([1 if float(r["_slippage_adjusted_pnl"]) > 0 else 0 for r in enriched], dtype=np.int64)
    pnls_adj = [float(r["_slippage_adjusted_pnl"]) for r in enriched]
    n_trades = len(enriched)
    wins = sum(1 for x in pnls_adj if x > 0)
    win_rate = wins / n_trades if n_trades else 0.0
    expectancy = float(np.mean(pnls_adj)) if n_trades else 0.0

    from collections import defaultdict

    sym_pnls: Dict[str, List[float]] = defaultdict(list)
    for r, adj in zip(enriched, pnls_adj):
        sym = (r.get("symbol") or "").strip().upper()
        if sym:
            sym_pnls[sym].append(adj)

    sym_counts = sorted(sym_pnls.items(), key=lambda kv: -len(kv[1]))[:3]
    top3_lines: List[str] = []
    for sym, adjs in sym_counts:
        wr = sum(1 for x in adjs if x > 0) / len(adjs)
        top3_lines.append(f"  - {sym}: n={len(adjs)}, slippage-adj win rate={wr:.2%}")

    clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=5, random_state=42)
    clf.fit(X, y)

    tree_txt = export_text(clf, feature_names=feat_cols)

    leaves = leaf_paths_with_stats(clf.tree_, feat_cols)
    # Highest concentration of wins: sort by win_rate then sample count
    leaves_sorted = sorted(
        leaves,
        key=lambda d: (d["win_rate"], d["n_samples"]),
        reverse=True,
    )
    top_paths = [L for L in leaves_sorted if L["n_samples"] >= 5][:3]

    print("=" * 72)
    print("Alpaca Equities Multi-Signal Report (100-trade slice)")
    print("=" * 72)
    print(f"\nData: {path}")
    print(
        f"Slippage model: {SLIPPAGE_BPS * 10000:.0f} bps of notional per trade "
        f"(default notional ${DEFAULT_NOTIONAL_USD:.0f} if missing)\n"
    )

    print("--- Baseline metrics (slippage-adjusted) ---")
    print(f"  Total trades analyzed: {n_trades}")
    print(f"  Slippage-adjusted win rate: {win_rate:.2%}")
    print(f"  Slippage-adjusted expectancy: ${expectancy:.4f} / trade")
    print("  Top 3 tickers by trade count (slippage-adj win rate):")
    for line in top3_lines:
        print(line)

    print(f"\n--- Model ---")
    print(f"  Features used ({len(feat_cols)}): {', '.join(feat_cols)}")
    print(f"  Decision tree (max_depth=3, min_samples_leaf=5):\n")
    print(tree_txt)

    print("--- Top paths (highest win-rate leaves, n >= 5) ---")
    if not top_paths:
        print("  (No leaves with n>=5; check tree depth / data.)")
    for i, leaf in enumerate(top_paths, 1):
        print(f"\n  Path {i}: win_rate={leaf['win_rate']:.2%}, n={leaf['n_samples']}, wins={leaf['wins']}")
        for rule in leaf["rules"]:
            print(f"    AND {rule}")

    print("\n--- Kraken / crypto contrast (qualitative) ---")
    print(
        "  Unlike a typical crypto book where edge often clusters on funding, liquidations, "
        "and wide-spread taker flow, this equities slice is scored with compact 2 bps friction "
        "and multi-signal UW-style components (flow, dark pool, greeks, etc.). "
        "The tree above highlights which of those engineered signals best separate "
        "slippage-adjusted winners from losers in this 100-trade window - not on-chain unwind risk."
    )
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
