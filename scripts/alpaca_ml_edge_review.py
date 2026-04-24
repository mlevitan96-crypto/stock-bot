#!/usr/bin/env python3
"""
Temporary / offline: ML edge review on Alpaca cohort from unified JSONL.

Reads logs/alpaca_unified_events.jsonl (+ optional strict_backfill merge).
Joins alpaca_entry_attribution -> alpaca_exit_attribution on trade_id.
Does NOT modify live trading.

Usage:
  python3 scripts/alpaca_ml_edge_review.py
  python3 scripts/alpaca_ml_edge_review.py --log path/to/alpaca_unified_events.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple


def _repo_root() -> Path:
    env = os.environ.get("STOCKBOT_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    cwd = Path.cwd()
    if (cwd / "main.py").is_file() and (cwd / "logs").is_dir():
        return cwd.resolve()
    p = Path(__file__).resolve().parent
    for _ in range(6):
        if (p / "logs").is_dir() and (p / "main.py").is_file():
            return p
        p = p.parent
    return Path(__file__).resolve().parents[1]


def _stream_jsonl_paths(paths: List[Path]) -> Iterator[dict]:
    for p in paths:
        if not p.is_file():
            continue
        with p.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def _float_pnl(exit_rec: dict) -> Optional[float]:
    if exit_rec.get("realized_pnl_usd") is not None:
        try:
            return float(exit_rec["realized_pnl_usd"])
        except (TypeError, ValueError):
            pass
    snap = exit_rec.get("snapshot")
    if isinstance(snap, dict) and snap.get("pnl") is not None:
        try:
            return float(snap["pnl"])
        except (TypeError, ValueError):
            pass
    return None


def _numeric_features(raw: Any) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            try:
                out[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
        elif v is not None and str(v).strip() != "":
            try:
                out[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
    return out


def load_cohort(
    log_paths: List[Path],
    *,
    prefer_terminal_exit: bool = True,
) -> Tuple[List[dict], List[str]]:
    """
    Returns list of rows: {trade_id, symbol, pnl, win, features: {k: v}, entry_rec meta}
    and sorted list of feature column names (intersection or union strategy).
    """
    entries: Dict[str, dict] = {}
    exits_by_tid: Dict[str, List[dict]] = {}

    for rec in _stream_jsonl_paths(log_paths):
        et = rec.get("event_type")
        if et == "alpaca_entry_attribution":
            tid = str(rec.get("trade_id") or "")
            if tid:
                entries[tid] = rec
        elif et == "alpaca_exit_attribution":
            tid = str(rec.get("trade_id") or "")
            if tid:
                exits_by_tid.setdefault(tid, []).append(rec)

    rows: List[dict] = []
    all_keys: set[str] = set()

    for tid, ent in entries.items():
        ex_list = exits_by_tid.get(tid) or []
        if not ex_list:
            continue
        if prefer_terminal_exit:
            term = [e for e in ex_list if e.get("terminal_close") is True]
            chosen = term[-1] if term else ex_list[-1]
        else:
            chosen = ex_list[-1]
        pnl = _float_pnl(chosen)
        if pnl is None:
            continue
        raw = ent.get("raw_signals")
        if not isinstance(raw, dict) or not raw:
            raw = ent.get("contributions")
        feats = _numeric_features(raw)
        if not feats:
            continue
        for k in feats:
            all_keys.add(k)
        rows.append(
            {
                "trade_id": tid,
                "symbol": str(ent.get("symbol") or ""),
                "pnl": pnl,
                "win": pnl > 0.0,
                "features": feats,
            }
        )

    # Stable column order: known UW-style order first, then rest sorted
    preferred = [
        "flow_deterioration",
        "darkpool_deterioration",
        "sentiment_deterioration",
        "score_deterioration",
        "regime_shift",
        "sector_shift",
        "vol_expansion",
        "thesis_invalidated",
        "earnings_risk",
        "overnight_flow_risk",
    ]
    cols = [c for c in preferred if c in all_keys]
    cols.extend(sorted(k for k in all_keys if k not in cols))
    return rows, cols


def divergence_report(rows: List[dict], feature_cols: List[str]) -> None:
    n = len(rows)
    if n == 0:
        print("No joined entry+exit rows with PnL and numeric features.")
        return

    pnls = [r["pnl"] for r in rows]
    wins = [r for r in rows if r["win"]]
    losses = [r for r in rows if not r["win"]]

    wr = len(wins) / n
    total_pnl = sum(pnls)
    avg_pnl = total_pnl / n

    print("=== Alpaca ML Edge Report ===")
    print(f"Cohort trades (joined):     {n}")
    print(f"Base win rate (pnl > 0):     {wr:.4f} ({len(wins)}W / {len(losses)}L)")
    print(f"Total PnL (sum):             {total_pnl:.4f}")
    print(f"Average expectancy (mean):   {avg_pnl:.6f}")
    print()

    ranked: List[Tuple[str, float, float, float, float, int, int]] = []
    for col in feature_cols:
        wvals = [r["features"].get(col) for r in wins if col in r["features"]]
        lvals = [r["features"].get(col) for r in losses if col in r["features"]]
        if not wvals and not lvals:
            continue
        mw = sum(wvals) / len(wvals) if wvals else 0.0
        ml = sum(lvals) / len(lvals) if lvals else 0.0
        div = abs(mw - ml)
        ranked.append((col, div, mw, ml, mw - ml, len(wvals), len(lvals)))

    ranked.sort(key=lambda x: -x[1])

    print("Feature divergence: abs(mean(win) - mean(loss)) (ranked):")
    print(f"{'feature':<28} {'divergence':>12} {'mean_win':>12} {'mean_loss':>12} {'nW':>6} {'nL':>6}")
    for col, div, mw, ml, _, nw, nl in ranked:
        print(f"{col:<28} {div:12.6f} {mw:12.6f} {ml:12.6f} {nw:6d} {nl:6d}")

    print()
    top3 = ranked[:3]
    if top3:
        print("=== Top 3 predictive (by absolute mean gap) ===")
        for i, (col, div, mw, ml, raw_diff, nw, nl) in enumerate(top3, 1):
            print(f"{i}. {col}")
            print(f"   abs_gap = {div:.6f}  (winners avg {mw:.6f} vs losers avg {ml:.6f}, diff {raw_diff:+.6f})")
            print(f"   coverage: {nw} wins with feature, {nl} losses with feature")

    print()
    print("=== Quant recommendation (next-gen weights) ===")
    print(
        "- Treat absolute mean gaps as a coarse effect size only: no controls for symbol, regime, "
        "hold time, or multiple testing; use shadow / OOS before live weight moves."
    )
    if top3:
        up = [t for t in top3 if t[4] > 0]
        down = [t for t in top3 if t[4] < 0]
        if up:
            print(
                "- Features higher in **winners**: consider **mild upward** weight nudges "
                f"({', '.join(t[0] for t in up)}) in composite entry scoring, capped (small pct band) "
                "until validated on a frozen holdout."
            )
        if down:
            print(
                "- Features higher in **losers**: consider **down-weighting or gating** "
                f"({', '.join(t[0] for t in down)}) when magnitude exceeds a learned percentile."
            )
        if not up and not down:
            pass
    else:
        print("- Insufficient ranked features; expand raw_signals coverage or fix joins.")
    print()
    print("Done. (No live trading logic modified.)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Alpaca ML edge review from unified JSONL")
    ap.add_argument(
        "--log",
        type=Path,
        default=None,
        help="Primary alpaca_unified_events.jsonl (default: repo logs/)",
    )
    ap.add_argument(
        "--no-backfill",
        action="store_true",
        help="Do not merge logs/strict_backfill_alpaca_unified_events.jsonl",
    )
    args = ap.parse_args()

    logs_dir = _repo_root() / "logs"
    primary = args.log or (logs_dir / "alpaca_unified_events.jsonl")
    paths = [primary]
    if not args.no_backfill:
        bf = logs_dir / "strict_backfill_alpaca_unified_events.jsonl"
        if bf.is_file():
            paths.append(bf)

    rows, cols = load_cohort(paths)
    # Restrict to the standard 10 UW keys when all present (user request); else use all numeric keys found
    standard_10 = [
        "flow_deterioration",
        "darkpool_deterioration",
        "sentiment_deterioration",
        "score_deterioration",
        "regime_shift",
        "sector_shift",
        "vol_expansion",
        "thesis_invalidated",
        "earnings_risk",
        "overnight_flow_risk",
    ]
    if all(k in cols for k in standard_10):
        use_cols = standard_10
    else:
        use_cols = cols

    divergence_report(rows, use_cols)
    return 0


if __name__ == "__main__":
    rr = _repo_root()
    sys.path.insert(0, str(rr))
    raise SystemExit(main())
