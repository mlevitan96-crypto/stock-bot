#!/usr/bin/env python3
"""
Expectancy-gate diagnostic: are we selecting for marginal/low-expectancy trades?

Reads the same joined attribution data as effectiveness reports. Computes:
- Entry score distribution (min, max, percentiles) in executed trades
- Trade count and expectancy by score bucket (e.g. [2.5-2.7], [2.7-2.9], [2.9+])
- Whether "marginal" buckets (just above common thresholds) have worse expectancy

Additive only: does not change LOCK/REVERT or recommendation. Writes
expectancy_gate_diagnostic.json to --out-dir for review.

Usage:
  python scripts/analysis/run_expectancy_gate_diagnostic.py --start YYYY-MM-DD --end YYYY-MM-DD --out-dir reports/effectiveness_baseline_blame
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.analysis.attribution_loader import load_joined_closed_trades


def _safe_float(x, default=None):
    if x is None:
        return default
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def main() -> int:
    ap = argparse.ArgumentParser(description="Expectancy gate diagnostic: entry score distribution vs outcomes")
    ap.add_argument("--start", type=str, default=None, help="Start date YYYY-MM-DD")
    ap.add_argument("--end", type=str, default=None, help="End date YYYY-MM-DD")
    ap.add_argument("--base-dir", type=Path, default=REPO, help="Repo base (logs/attribution.jsonl, logs/exit_attribution.jsonl)")
    ap.add_argument("--out-dir", type=Path, required=True, help="Output directory (e.g. effectiveness baseline dir)")
    args = ap.parse_args()

    base = args.base_dir.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    attr_path = base / "logs" / "attribution.jsonl"
    exit_path = base / "logs" / "exit_attribution.jsonl"
    if not attr_path.exists() or not exit_path.exists():
        out = {"message": "missing logs", "attribution": str(attr_path), "exit_attribution": str(exit_path)}
        (out_dir / "expectancy_gate_diagnostic.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print("Expectancy gate diagnostic: missing logs, wrote placeholder", file=sys.stderr)
        return 0

    joined = load_joined_closed_trades(attr_path, exit_path, start_date=args.start, end_date=args.end)
    if not joined:
        out = {"message": "no joined trades in range", "start": args.start, "end": args.end}
        (out_dir / "expectancy_gate_diagnostic.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print("Expectancy gate diagnostic: no joined trades, wrote placeholder", file=sys.stderr)
        return 0

    # Scores in executed trades
    scores = []
    for r in joined:
        s = r.get("entry_score")
        if s is not None:
            v = _safe_float(s)
            if v is not None:
                scores.append(v)
    scores.sort()

    n = len(scores)
    if n == 0:
        out = {"message": "no entry_score in joined trades", "joined_count": len(joined)}
        (out_dir / "expectancy_gate_diagnostic.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
        print("Expectancy gate diagnostic: no entry_score in joined trades", file=sys.stderr)
        return 0

    def pctile(arr, p):
        if not arr:
            return None
        k = (len(arr) - 1) * p / 100.0
        f = int(k)
        if f >= len(arr) - 1:
            return arr[-1]
        return arr[f] + (k - f) * (arr[f + 1] - arr[f])

    dist = {
        "min": round(scores[0], 4),
        "max": round(scores[-1], 4),
        "p25": round(pctile(scores, 25), 4),
        "p50": round(pctile(scores, 50), 4),
        "p75": round(pctile(scores, 75), 4),
        "count_with_score": n,
        "joined_count": len(joined),
    }

    # Buckets: common threshold bands (vs MIN_EXEC_SCORE 2.5, 2.7, 2.9)
    buckets = [
        ("below_2_5", None, 2.5),
        ("2_5_to_2_7", 2.5, 2.7),
        ("2_7_to_2_9", 2.7, 2.9),
        ("2_9_to_3_2", 2.9, 3.2),
        ("above_3_2", 3.2, None),
    ]
    by_bucket = {}
    for label, lo, hi in buckets:
        trades = []
        for r in joined:
            s = _safe_float(r.get("entry_score"))
            if s is None:
                continue
            if lo is not None and s < lo:
                continue
            if hi is not None and s >= hi:
                continue
            pnl = _safe_float(r.get("pnl"), 0.0)
            trades.append(pnl)
        tc = len(trades)
        if tc == 0:
            by_bucket[label] = {"trade_count": 0, "expectancy_per_trade": None, "win_rate": None}
        else:
            wins = sum(1 for p in trades if p > 0)
            exp = sum(trades) / tc
            by_bucket[label] = {
                "trade_count": tc,
                "expectancy_per_trade": round(exp, 6),
                "win_rate": round(wins / tc, 4),
            }
    dist["by_score_bucket"] = by_bucket

    # Marginal share: % of trades with score in [2.5, 2.9] (just above common floors)
    marginal_lo, marginal_hi = 2.5, 2.9
    marginal_count = sum(1 for s in scores if marginal_lo <= s < marginal_hi)
    dist["pct_marginal_2_5_to_2_9"] = round(100.0 * marginal_count / n, 2) if n else None
    dist["interpretation"] = (
        "High pct_marginal_2_5_to_2_9 suggests many executed trades are just above threshold; "
        "compare by_score_bucket expectancy to see if marginal bucket underperforms."
    )

    out = {
        "start": args.start,
        "end": args.end,
        "distribution": dist,
    }
    (out_dir / "expectancy_gate_diagnostic.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_dir / 'expectancy_gate_diagnostic.json'} (n={n}, p50_score={dist['p50']}, pct_marginal={dist.get('pct_marginal_2_5_to_2_9')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
