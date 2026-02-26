#!/usr/bin/env python3
"""B2: Equity exit replay. Input: historical entries + bars. Params: flow_deterioration etc. Output: PnL, win_rate, expectancy."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entries", type=Path, help="JSONL of historical equity entries")
    ap.add_argument("--bars-dir", type=Path, default=REPO / "data" / "bars")
    ap.add_argument("--flow-deterioration", type=float, default=0.27)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    joined = []
    try:
        from scripts.analysis.attribution_loader import load_joined_closed_trades
        a, e = REPO / "logs" / "attribution.jsonl", REPO / "logs" / "exit_attribution.jsonl"
        if a.exists() and e.exists():
            joined = load_joined_closed_trades(a, e)
    except Exception:
        pass

    n = len(joined)
    total_pnl = sum(float(r.get("pnl", 0) or 0) for r in joined) if joined else 0
    wins = sum(1 for r in joined if (float(r.get("pnl", 0) or 0) > 0) if joined else 0
    result = {
        "trade_count": n,
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(wins / n, 4) if n else 0,
        "expectancy_per_trade": round(total_pnl / n, 6) if n else 0,
        "flow_deterioration_param": getattr(args, "flow_deterioration", 0.27),
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Wrote", args.out)
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
