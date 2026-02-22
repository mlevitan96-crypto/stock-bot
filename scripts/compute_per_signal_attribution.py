#!/usr/bin/env python3
"""
Compute per-signal PnL attribution from backtest_trades.jsonl (trades with context.attribution_components).
Writes: per_signal_pnl.json (signal_id -> trade_count, total_pnl, win_rate, avg_pnl).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True, help="Path to backtest_trades.jsonl")
    ap.add_argument("--out", required=True, help="Path to output per_signal_pnl.json")
    args = ap.parse_args()
    trades_path = Path(args.trades)
    out_path = Path(args.out)
    if not trades_path.is_absolute():
        trades_path = REPO / trades_path
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    trades = []
    for line in trades_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            trades.append(json.loads(line))
        except Exception:
            continue

    by_signal = {}
    for t in trades:
        pnl = float(t.get("pnl_usd") or 0)
        ctx = t.get("context") or {}
        comps = ctx.get("attribution_components") or []
        if not comps:
            continue
        for c in comps:
            sid = c.get("signal_id")
            if not sid:
                continue
            if sid not in by_signal:
                by_signal[sid] = {"pnls": [], "wins": 0, "losses": 0}
            by_signal[sid]["pnls"].append(pnl)
            if pnl > 0:
                by_signal[sid]["wins"] += 1
            elif pnl < 0:
                by_signal[sid]["losses"] += 1

    out = {}
    for sid, data in by_signal.items():
        pnls = data["pnls"]
        n = len(pnls)
        total_pnl = sum(pnls)
        wins = data["wins"]
        losses = data["losses"]
        win_rate = (wins / n * 100.0) if n else 0.0
        avg_pnl = total_pnl / n if n else 0.0
        out[sid] = {
            "trade_count": n,
            "total_pnl_usd": round(total_pnl, 2),
            "win_rate_pct": round(win_rate, 2),
            "avg_pnl_usd": round(avg_pnl, 2),
            "wins": wins,
            "losses": losses,
        }

    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Per-signal attribution ->", str(out_path), "(" + str(len(out)) + " signals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
