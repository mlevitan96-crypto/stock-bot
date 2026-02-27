#!/usr/bin/env python3
"""One-off: compute comparison JSON from baseline/proposed backtest_exits.jsonl. Output to stdout."""
import json
import sys

def agg(path):
    total_pnl = 0.0
    wins = 0
    givebacks = []
    n = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
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
        "total_trades": n,
        "total_pnl_usd": round(total_pnl, 2),
        "win_rate": round(wins / n, 4) if n else 0,
        "avg_profit_giveback": round(sum(givebacks) / len(givebacks), 4) if givebacks else None,
    }


def main():
    base_path = "backtests/30d_baseline_20260218_032951/backtest_exits.jsonl"
    prop_path = "backtests/30d_proposed_20260218_032957/backtest_exits.jsonl"
    base = agg(base_path)
    prop = agg(prop_path)
    deltas = {
        "total_pnl_usd": round(prop["total_pnl_usd"] - base["total_pnl_usd"], 2),
        "win_rate": round(prop["win_rate"] - base["win_rate"], 4),
    }
    if prop.get("avg_profit_giveback") is not None and base.get("avg_profit_giveback") is not None:
        deltas["avg_profit_giveback"] = round(
            prop["avg_profit_giveback"] - base["avg_profit_giveback"], 4
        )
    out = {
        "baseline_dir": "backtests/30d_baseline_20260218_032951",
        "proposed_dir": "backtests/30d_proposed_20260218_032957",
        "aggregates": {"baseline": base, "proposed": prop},
        "deltas": deltas,
        "entry_vs_exit_blame": {"baseline": None, "proposed": None},
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
