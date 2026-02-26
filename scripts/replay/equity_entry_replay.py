#!/usr/bin/env python3
"""
B2 — Equity entry replay.
Input: historical equity signals (entry_score, features).
Parameters: MIN_EXEC_SCORE thresholds, signal weights.
Output: hypothetical trade set, PnL, win_rate, expectancy, trade_count.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description="Equity entry replay: MIN_EXEC_SCORE / signal weights on historical signals")
    ap.add_argument("--joined", type=Path, help="Joined trades JSONL or effectiveness dir (effectiveness_aggregates + joined source)")
    ap.add_argument("--min-exec-score", type=float, default=2.5, help="Threshold: only trades with entry_score >= this")
    ap.add_argument("--out", type=Path, help="Output JSON: trade_count, total_pnl, win_rate, expectancy")
    args = ap.parse_args()

    joined = []
    if args.joined and args.joined.exists():
        if args.joined.is_dir():
            # Load from attribution + exit_attribution using same date range as effectiveness
            try:
                from scripts.analysis.attribution_loader import load_joined_closed_trades
                attr = REPO / "logs" / "attribution.jsonl"
                exit_attr = REPO / "logs" / "exit_attribution.jsonl"
                if attr.exists() and exit_attr.exists():
                    joined = load_joined_closed_trades(attr, exit_attr)
            except Exception:
                pass
        else:
            for line in args.joined.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        joined.append(json.loads(line))
                    except Exception:
                        pass

    # Filter by hypothetical MIN_EXEC_SCORE
    entry_score_key = "entry_score"
    filtered = [r for r in joined if (float(r.get(entry_score_key) or 0) >= args.min_exec_score)]
    if not filtered:
        filtered = joined  # no scores: use all

    if not filtered:
        result = {"trade_count": 0, "total_pnl": 0.0, "win_rate": 0.0, "expectancy_per_trade": 0.0, "min_exec_score": args.min_exec_score}
    else:
        n = len(filtered)
        total_pnl = sum(float(r.get("pnl", 0) or 0) for r in filtered)
        wins = sum(1 for r in filtered if (float(r.get("pnl", 0) or 0) > 0))
        result = {
            "trade_count": n,
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(wins / n, 4) if n else 0,
            "expectancy_per_trade": round(total_pnl / n, 6) if n else 0,
            "min_exec_score": args.min_exec_score,
        }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
