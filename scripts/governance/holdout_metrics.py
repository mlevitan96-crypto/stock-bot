#!/usr/bin/env python3
"""
Compute backtest aggregates for a holdout period (last N days) only.
Use this to compare overlays without forward bias: tune on full window, evaluate on holdout.

Usage:
  python scripts/governance/holdout_metrics.py --backtest-dir backtests/30d_baseline_XXX --holdout-days 7
  python scripts/governance/holdout_metrics.py --backtest-dir backtests/30d_proposed_XXX --holdout-days 7 --out-json

Output: total_trades, total_pnl_usd, win_rate, avg_profit_giveback for exits in the last N days only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _day_utc(ts) -> str | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d")
        except Exception:
            return None
    s = str(ts)
    if len(s) >= 10:
        return s[:10]
    return None


def aggregate_exits_in_range(exits_path: Path, start_date: str, end_date: str) -> dict:
    """Compute aggregates from backtest_exits.jsonl for exits with date in [start_date, end_date]."""
    if not exits_path.exists():
        return {}
    total_pnl = 0.0
    wins = 0
    givebacks = []
    n = 0
    for line in exits_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            day = _day_utc(r.get("timestamp") or r.get("ts"))
            if day is None or day < start_date or day > end_date:
                continue
            pnl = float(r.get("pnl") or 0)
            total_pnl += pnl
            if pnl > 0:
                wins += 1
            gb = r.get("exit_quality_metrics", {}).get("profit_giveback")
            if gb is not None:
                givebacks.append(float(gb))
            n += 1
        except Exception:
            continue
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_trades": n,
        "total_pnl_usd": round(total_pnl, 2),
        "win_rate": round(wins / n, 4) if n else 0,
        "avg_profit_giveback": round(sum(givebacks) / len(givebacks), 4) if givebacks else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute holdout-period metrics from a backtest dir")
    ap.add_argument("--backtest-dir", type=Path, required=True, help="Backtest dir containing backtest_exits.jsonl")
    ap.add_argument("--holdout-days", type=int, default=7, help="Number of days at end of window to use as holdout")
    ap.add_argument("--out-json", action="store_true", help="Write metrics to backtest_dir/holdout_metrics.json")
    args = ap.parse_args()
    backtest_dir = args.backtest_dir.resolve()
    exits_path = backtest_dir / "backtest_exits.jsonl"
    if not exits_path.exists():
        print(f"Missing {exits_path}", file=sys.stderr)
        return 1

    # Infer date range from data: find max date, then holdout = [max - (N-1), max]
    max_date = None
    for line in exits_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            day = _day_utc(r.get("timestamp") or r.get("ts"))
            if day and (max_date is None or day > max_date):
                max_date = day
        except Exception:
            continue
    if not max_date:
        print("No dates found in backtest_exits.jsonl", file=sys.stderr)
        return 1
    end_d = datetime.strptime(max_date, "%Y-%m-%d").date()
    start_d = end_d - timedelta(days=args.holdout_days - 1)
    start_date = start_d.strftime("%Y-%m-%d")
    end_date = end_d.strftime("%Y-%m-%d")

    metrics = aggregate_exits_in_range(exits_path, start_date, end_date)
    print(f"Holdout: {start_date} .. {end_date} ({args.holdout_days} days)")
    print(json.dumps(metrics, indent=2))
    if args.out_json:
        (backtest_dir / "holdout_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"Wrote {backtest_dir / 'holdout_metrics.json'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
