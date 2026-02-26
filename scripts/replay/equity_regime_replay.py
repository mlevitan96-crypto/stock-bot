#!/usr/bin/env python3
"""B2: Equity regime replay. Filter by regime. Output: PnL, win_rate, expectancy by regime."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exclude-regime", type=str, default="")
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

    exclude = [x.strip() for x in (args.exclude_regime or "").split(",") if x.strip()]
    filtered = [r for r in joined if (r.get("entry_regime") or "") not in exclude] if exclude else joined
    n = len(filtered)
    total_pnl = sum(float(r.get("pnl", 0) or 0) for r in filtered) if filtered else 0
    wins = sum(1 for r in filtered if (float(r.get("pnl", 0) or 0) > 0) if filtered else 0
    result = {
        "trade_count": n,
        "total_pnl": round(total_pnl, 2),
        "win_rate": round(wins / n, 4) if n else 0,
        "expectancy_per_trade": round(total_pnl / n, 6) if n else 0,
        "exclude_regime": exclude,
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
