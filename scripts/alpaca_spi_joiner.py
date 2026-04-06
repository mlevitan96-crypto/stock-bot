#!/usr/bin/env python3
"""
As-of join closed trades to SPI (Gemini extract) for multi-signal decision tree.

- Resolves entry_time from: CSV columns entry_time/entry_ts, then logs/attribution.jsonl,
  else falls back to timestamp_utc (close) with an explicit warning count.
- Requires: pandas, numpy, scikit-learn
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

try:
    import numpy as np
    import pandas as pd
except ImportError:
    print("Install pandas and numpy: pip install pandas numpy", file=sys.stderr)
    raise SystemExit(1)

SLIPPAGE_BPS = 0.02 / 100.0
DEFAULT_NOTIONAL_USD = 100.0


def find_spi_csv(repo: Path, explicit: Optional[Path]) -> Path:
    if explicit and explicit.is_file():
        return explicit.resolve()
    default = repo / "reports" / "Gemini" / "signal_intelligence_spi.csv"
    if default.is_file():
        return default.resolve()
    alt = list((repo / "reports" / "Gemini").glob("*spi*.csv"))
    if alt:
        return alt[0].resolve()
    raise FileNotFoundError(f"No SPI CSV under {repo / 'reports' / 'Gemini'}")


def load_entry_ts_from_attribution(repo: Path) -> Dict[str, "pd.Timestamp"]:
    r = str(repo.resolve())
    if r not in sys.path:
        sys.path.insert(0, r)
    from config.registry import LogFiles

    path = (repo / LogFiles.ATTRIBUTION).resolve()
    out: Dict[str, pd.Timestamp] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if rec.get("type") != "attribution":
                continue
            tid = str(rec.get("trade_id") or "")
            if not tid:
                continue
            ctx = rec.get("context") if isinstance(rec.get("context"), dict) else {}
            ets = ctx.get("entry_ts") or rec.get("entry_ts")
            if not ets:
                continue
            ts = pd.to_datetime(ets, utc=True)
            out[tid] = ts
        except Exception:
            continue
    return out


def pick_notional(row: pd.Series) -> float:
    for k in ("notional", "position_size_usd", "notional_usd", "size_usd"):
        if k in row.index and pd.notna(row[k]):
            try:
                v = float(row[k])
                if v > 0:
                    return v
            except (TypeError, ValueError):
                pass
    return DEFAULT_NOTIONAL_USD


def normalize_spi_timestamp_column(df: pd.DataFrame) -> pd.DataFrame:
    for c in ("timestamp_utc", "timestamp", "utc", "ts_utc"):
        if c in df.columns:
            if c != "timestamp_utc":
                df = df.rename(columns={c: "timestamp_utc"})
            break
    else:
        raise ValueError("SPI CSV missing a timestamp column (expected timestamp_utc, timestamp, utc)")
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    return df


def dedupe_spi(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.sort_values(["symbol", "timestamp_utc"]).drop_duplicates(
        subset=["symbol", "timestamp_utc"], keep="last"
    )
    dropped = before - len(df)
    return df, dropped


def build_entry_time(
    trades: pd.DataFrame,
    entry_map: Dict[str, pd.Timestamp],
) -> Tuple[pd.Series, int, int, int]:
    """
    Returns (entry_time series, n_from_csv, n_from_attribution, n_fallback_close).
    """
    n_csv = n_attr = n_fb = 0
    times: List[Optional[pd.Timestamp]] = []
    for _, row in trades.iterrows():
        tid = str(row.get("trade_id") or "")
        et: Optional[pd.Timestamp] = None
        if "entry_time" in trades.columns:
            raw_et = row.get("entry_time")
            if pd.notna(raw_et) and str(raw_et).strip():
                et = pd.to_datetime(raw_et, utc=True)
                n_csv += 1
        if et is None and "entry_ts" in trades.columns:
            raw_ts = row.get("entry_ts")
            if pd.notna(raw_ts) and str(raw_ts).strip():
                et = pd.to_datetime(raw_ts, utc=True)
                n_csv += 1
        if et is None and tid in entry_map:
            et = entry_map[tid]
            n_attr += 1
        if et is None:
            et = pd.to_datetime(row.get("timestamp_utc"), utc=True, errors="coerce")
            n_fb += 1
        times.append(et)
    return pd.Series(times, index=trades.index), n_csv, n_attr, n_fb


def main() -> int:
    try:
        from sklearn.tree import DecisionTreeClassifier, export_text
    except ImportError:
        print("Install scikit-learn: pip install scikit-learn", file=sys.stderr)
        return 1

    ap = argparse.ArgumentParser(description="As-of join trades to SPI + decision tree")
    ap.add_argument(
        "--trades",
        type=Path,
        default=REPO_ROOT / "reports" / "stock_100_trades_clean.csv",
    )
    ap.add_argument("--spi", type=Path, default=None, help="Override path to signal_intelligence_spi.csv")
    ap.add_argument("--repo", type=Path, default=REPO_ROOT)
    args = ap.parse_args()
    repo = args.repo.resolve()

    trades_path = args.trades.resolve()
    if not trades_path.is_file():
        print(f"Missing trades CSV: {trades_path}", file=sys.stderr)
        return 1

    spi_path = find_spi_csv(repo, args.spi.resolve() if args.spi is not None else None)

    trades = pd.read_csv(trades_path)
    if "timestamp_utc" in trades.columns:
        trades["timestamp_utc"] = pd.to_datetime(trades["timestamp_utc"], utc=True, errors="coerce")

    entry_map = load_entry_ts_from_attribution(repo)
    entry_time, n_csv, n_attr, n_fb = build_entry_time(trades, entry_map)
    trades = trades.copy()
    trades["entry_time"] = entry_time
    trades = trades.dropna(subset=["entry_time"])
    trades = trades.sort_values(["symbol", "entry_time"], kind="mergesort")

    spi = pd.read_csv(spi_path)
    spi = normalize_spi_timestamp_column(spi)
    spi = spi.dropna(subset=["timestamp_utc", "symbol"])
    spi["symbol"] = spi["symbol"].astype(str).str.strip().str.upper()
    trades["symbol"] = trades["symbol"].astype(str).str.strip().str.upper()

    spi, spi_dup_dropped = dedupe_spi(spi)
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
    # Use resolved entry_time (from CSV / attribution / fallback), not the pre-build column name collision
    trade_keep = ["entry_time"] + [c for c in trade_keep if c != "entry_time"]
    t2 = trades[trade_keep].copy()

    # Per-symbol merge_asof avoids "left keys must be sorted" when entry_time is not
    # globally monotonic across symbols (pandas still validates whole-column order in some versions).
    parts: List[pd.DataFrame] = []
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

    join_matched = joined["spi_timestamp_utc"].notna()
    n_matched = int(join_matched.sum())
    n_total = len(joined)

    staleness_hours = (
        joined.loc[join_matched, "entry_time"] - joined.loc[join_matched, "spi_timestamp_utc"]
    ).dt.total_seconds() / 3600.0

    pnl_col = None
    for c in ("realized_pnl", "pnl_usd", "realized_pnl_usd", "pnl"):
        if c in joined.columns:
            pnl_col = c
            break
    if pnl_col is None:
        print("No PnL column found on trades.", file=sys.stderr)
        return 1

    merged = joined.copy()
    notionals = merged.apply(pick_notional, axis=1)
    pnl = pd.to_numeric(merged[pnl_col], errors="coerce")
    merged["slippage_adjusted_pnl"] = pnl - SLIPPAGE_BPS * notionals
    merged = merged.dropna(subset=["slippage_adjusted_pnl"])
    merged["is_win"] = (merged["slippage_adjusted_pnl"] > 0).astype(int)

    # SPI component columns (new + legacy names)
    comp_cols = sorted(
        {
            c
            for c in merged.columns
            if str(c).startswith("component_") and not str(c).endswith("_trade") and not str(c).endswith("_spi")
        }
    )
    # If merge created no plain component_ (unlikely), take _spi suffixed
    if not comp_cols:
        comp_cols = sorted(c for c in merged.columns if str(c).startswith("component_"))

    if not comp_cols:
        print("No component_* columns after join — check SPI schema.", file=sys.stderr)
        return 1

    X = merged[comp_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    y = merged["is_win"].to_numpy()
    if len(merged) < 5:
        print("Too few rows after join/filter for a tree.", file=sys.stderr)
        return 1

    clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=5, random_state=42)
    clf.fit(X, y)
    tree_txt = export_text(clf, feature_names=comp_cols)

    # Top win-rate leaves (sklearn 1.x: value = class proportions)
    tree_ = clf.tree_
    leaves: List[Tuple[float, int, int, List[str]]] = []

    def walk(node_id: int, rules: List[str]) -> None:
        left = tree_.children_left[node_id]
        if left == -1:
            v = tree_.value[node_id][0]
            n = int(tree_.n_node_samples[node_id])
            p_win = float(v[1]) if len(v) > 1 else 0.0
            wins = int(round(p_win * n))
            leaves.append((p_win, n, wins, list(rules)))
            return
        right = tree_.children_right[node_id]
        feat = tree_.feature[node_id]
        thr = tree_.threshold[node_id]
        name = comp_cols[feat]
        walk(left, rules + [f"{name} <= {thr:.6g}"])
        walk(right, rules + [f"{name} > {thr:.6g}"])

    walk(0, [])
    leaves.sort(key=lambda x: (x[0], x[1]), reverse=True)
    top_paths = [L for L in leaves if L[1] >= 5][:3]

    print("=" * 72)
    print("True UW Multi-Signal Report (trades as-of joined to SPI)")
    print("=" * 72)
    print(f"\nTrades CSV: {trades_path}")
    print(f"SPI CSV:    {spi_path}")
    print(f"SPI dedupe: dropped {spi_dup_dropped} duplicate (symbol, timestamp) rows")
    print("\n--- Entry time resolution ---")
    print(f"  From CSV entry_time/entry_ts: {n_csv}")
    print(f"  From logs/attribution.jsonl:  {n_attr}")
    print(f"  Fallback (timestamp_utc close): {n_fb}")
    if n_fb:
        print("  NOTE: close-time fallback biases as-of context toward exit window, not true entry.")

    print("\n--- Join ---")
    print(f"  merge_asof backward on entry_time <- SPI timestamp_utc, by symbol")
    print(f"  Trades with SPI match: {n_matched} / {n_total}")
    if n_matched < n_total:
        print(f"  Unmatched: {n_total - n_matched} (no prior SPI row for that symbol)")

    if len(staleness_hours):
        print(
            f"  Match staleness (hours, matched rows): median={staleness_hours.median():.2f}, "
            f"max={staleness_hours.max():.2f}"
        )

    wr = float(merged["is_win"].mean())
    expn = float(merged["slippage_adjusted_pnl"].mean())
    print("\n--- Slippage-adjusted baseline (joined sample) ---")
    print(f"  Rows in tree: {len(merged)}")
    print(f"  Win rate: {wr:.2%}")
    print(f"  Expectancy: ${expn:.4f} / trade")

    print(f"\n--- Component features ({len(comp_cols)}) ---")
    print("  " + ", ".join(comp_cols))

    print("\n--- Decision tree (export_text) ---\n")
    print(tree_txt)

    print("\n--- Top 2-3 paths (by win rate in leaf, n >= 5) ---")
    if not top_paths:
        print("  (no leaves with n>=5)")
    else:
        for i, (p_win, n, wins, rules) in enumerate(top_paths, 1):
            print(f"\n  Path {i}: win_rate={p_win:.2%}, n={n}, wins={wins}")
            for r in rules:
                print(f"    AND {r}")

    print("\n--- Edge read (this file + tree) ---")
    print(
        "  Interpret splits above as drivers of is_win on the joined sample. "
        "If the tree uses component_dark_pool / flow / greeks, those UW sub-components dominate "
        "this slice; if it falls back to spi total_score only, SPI rows lacked component variance."
    )
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
