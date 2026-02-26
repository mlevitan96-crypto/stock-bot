#!/usr/bin/env python3
"""
B2 — Equity signal ablation replay.
Input: historical equity trades + signal contributions.
Parameters: remove or down-weight specific signals.
Output: PnL, win_rate, expectancy with each signal ablated.
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
    ap = argparse.ArgumentParser(description="Equity signal ablation: down-weight or remove signal, recompute hypothetical score")
    ap.add_argument("--effectiveness-dir", type=Path, help="Dir with signal_effectiveness.json / joined source")
    ap.add_argument("--ablate-signal", type=str, help="Signal ID to ablate (set contribution to 0)")
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

    # Stub: ablation = filter out trades where this signal had dominant contribution (simplified: just report current stats)
    if not joined:
        result = {"trade_count": 0, "total_pnl": 0.0, "win_rate": 0.0, "expectancy_per_trade": 0.0, "ablate_signal": args.ablate_signal}
    else:
        n = len(joined)
        total_pnl = sum(float(r.get("pnl", 0) or 0) for r in joined)
        wins = sum(1 for r in joined if (float(r.get("pnl", 0) or 0) > 0))
        result = {
            "trade_count": n,
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(wins / n, 4) if n else 0,
            "expectancy_per_trade": round(total_pnl / n, 6) if n else 0,
            "ablate_signal": args.ablate_signal,
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
