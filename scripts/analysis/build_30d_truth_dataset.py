#!/usr/bin/env python3
"""
Build a canonical 30d truth dataset from attribution + exit_attribution + bars dir.
Output: single JSON with window, trade_count, exit_count, bar_coverage, and joined records
for downstream massive review and profitability campaign.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _day_utc(ts) -> str | None:
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d")
        s = str(ts)
        if len(s) >= 10:
            return s[:10]
        return None
    except Exception:
        return None


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--attribution", required=True)
    ap.add_argument("--exit_attribution", required=True)
    ap.add_argument("--bars", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base = REPO
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=args.days)
    window_days = []
    d = start
    while d <= end:
        window_days.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)

    attr_path = base / args.attribution
    exit_path = base / args.exit_attribution
    bars_dir = base / args.bars

    trades = []
    for r in _iter_jsonl(attr_path):
        if r.get("type") != "attribution":
            continue
        day = _day_utc(r.get("timestamp") or r.get("ts"))
        if day not in window_days:
            continue
        trades.append({
            "timestamp": r.get("timestamp") or r.get("ts"),
            "symbol": r.get("symbol"),
            "entry_score": r.get("entry_score"),
            "pnl_usd": r.get("pnl_usd"),
            "pnl_pct": r.get("pnl_pct"),
            "hold_minutes": r.get("hold_minutes"),
            "context": r.get("context") or {},
        })

    exits = []
    for r in _iter_jsonl(exit_path):
        day = _day_utc(r.get("timestamp") or r.get("ts"))
        if day not in window_days:
            continue
        exits.append({
            "timestamp": r.get("timestamp") or r.get("ts"),
            "symbol": r.get("symbol"),
            "exit_reason": r.get("exit_reason"),
            "pnl": r.get("pnl"),
            "pnl_pct": r.get("pnl_pct"),
            "time_in_trade_minutes": r.get("time_in_trade_minutes"),
        })

    bar_dates = set()
    if bars_dir.exists():
        for d in bars_dir.iterdir():
            if d.is_dir() and len(d.name) == 10 and d.name[:4].isdigit():
                bar_dates.add(d.name)

    truth = {
        "window_start": str(start),
        "window_end": str(end),
        "days": args.days,
        "trade_count": len(trades),
        "exit_count": len(exits),
        "bar_dates_available": len(bar_dates),
        "bar_dates_sample": sorted(bar_dates)[:10],
        "trades": trades,
        "exits": exits,
    }

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(truth, indent=2, default=str), encoding="utf-8")
    print(f"Wrote truth_30d.json: {len(trades)} trades, {len(exits)} exits, {len(bar_dates)} bar dates -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
