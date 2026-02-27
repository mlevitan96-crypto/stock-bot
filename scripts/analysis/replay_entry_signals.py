#!/usr/bin/env python3
"""
Replay entry signals against labeled moves to find leading indicators.
Correlates entry_score with outcome (pnl). Output: signal_leading_stats.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--labeled_moves", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no_suppression", action="store_true")
    args = ap.parse_args()

    truth_path = Path(args.truth)
    if not truth_path.is_absolute():
        truth_path = REPO / truth_path
    labeled_path = Path(args.labeled_moves)
    if not labeled_path.is_absolute():
        labeled_path = REPO / labeled_path

    if not truth_path.exists():
        print(f"Truth not found: {truth_path}", file=sys.stderr)
        return 1
    if not labeled_path.exists():
        print(f"Labeled moves not found: {labeled_path}", file=sys.stderr)
        return 1

    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    labeled = json.loads(labeled_path.read_text(encoding="utf-8"))
    moves_by_ts_sym = {(m.get("timestamp"), m.get("symbol")): m for m in labeled.get("labeled", [])}

    trades = truth.get("trades", [])
    entry_buckets = defaultdict(list)  # bucket -> [pnl_pct]
    for t in trades:
        ts = t.get("timestamp") or t.get("ts")
        symbol = t.get("symbol")
        entry_score = t.get("entry_score")
        pnl_pct = t.get("pnl_pct")
        if ts is None or symbol is None:
            continue
        try:
            score = float(entry_score) if entry_score is not None else 0.0
        except (TypeError, ValueError):
            score = 0.0
        try:
            pct = float(pnl_pct) if pnl_pct is not None else 0.0
        except (TypeError, ValueError):
            pct = 0.0
        bucket = "low" if score < 0.3 else "mid" if score < 0.6 else "high"
        entry_buckets[bucket].append(pct)

    entry_bucket_stats = {
        k: {
            "count": len(v),
            "avg_pnl_pct": round(sum(v) / len(v), 4) if v else 0,
            "win_rate": round(100 * sum(1 for x in v if x > 0) / len(v), 2) if v else 0,
        }
        for k, v in entry_buckets.items()
    }
    stats = {
        "no_suppression": args.no_suppression,
        "trade_count": len(trades),
        "labeled_count": len(labeled.get("labeled", [])),
        "entry_buckets": entry_bucket_stats,
        "leading_indicators": [
            {"bucket": k, "avg_pnl_pct": entry_bucket_stats[k]["avg_pnl_pct"], "win_rate": entry_bucket_stats[k]["win_rate"]}
            for k in sorted(entry_buckets.keys())
        ],
    }

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(stats, indent=2, default=str), encoding="utf-8")
    print(f"Signal leading stats -> {out_path} (buckets: {list(stats['entry_buckets'].keys())})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
