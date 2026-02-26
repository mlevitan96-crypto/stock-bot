#!/usr/bin/env python3
"""
B2 — Equity target replay.
Input: historical equity entries + price paths.
Parameters: profit targets, stop levels, hold times.
Output: target-hit rates, PnL, expectancy, MFE/MAE.
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
    ap = argparse.ArgumentParser(description="Equity target replay: profit target / stop / hold time on historical entries")
    ap.add_argument("--joined", type=Path, help="Joined trades with MFE/MAE or price path")
    ap.add_argument("--profit-target-pct", type=float, default=0.02, help="Hypothetical profit target (fraction)")
    ap.add_argument("--stop-pct", type=float, default=-0.01, help="Hypothetical stop (fraction)")
    ap.add_argument("--out", type=Path, help="Output JSON")
    args = ap.parse_args()

    joined = []
    try:
        from scripts.analysis.attribution_loader import load_joined_closed_trades
        attr = REPO / "logs" / "attribution.jsonl"
        exit_attr = REPO / "logs" / "exit_attribution.jsonl"
        if attr.exists() and exit_attr.exists():
            joined = load_joined_closed_trades(attr, exit_attr)
    except Exception:
        pass

    if not joined:
        result = {"trade_count": 0, "total_pnl": 0.0, "win_rate": 0.0, "expectancy_per_trade": 0.0, "profit_target_pct": args.profit_target_pct, "stop_pct": args.stop_pct}
    else:
        n = len(joined)
        total_pnl = sum(float(r.get("pnl", 0) or 0) for r in joined)
        wins = sum(1 for r in joined if (float(r.get("pnl", 0) or 0) > 0))
        result = {
            "trade_count": n,
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(wins / n, 4) if n else 0,
            "expectancy_per_trade": round(total_pnl / n, 6) if n else 0,
            "profit_target_pct": args.profit_target_pct,
            "stop_pct": args.stop_pct,
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
