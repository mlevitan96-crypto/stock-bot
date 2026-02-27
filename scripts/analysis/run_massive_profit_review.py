#!/usr/bin/env python3
"""
Massive multi-angle profit review from canonical 30d truth dataset.
Produces entry, exit, direction, sizing, and cost slices for downstream multi-persona review.
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no_suppression", action="store_true")
    args = ap.parse_args()

    truth_path = Path(args.truth)
    if not truth_path.is_absolute():
        truth_path = REPO / truth_path
    if not truth_path.exists():
        print(f"Truth file not found: {truth_path}", file=sys.stderr)
        (REPO / args.out).mkdir(parents=True, exist_ok=True)
        (REPO / args.out / "MASSIVE_REVIEW_SEED.json").write_text(
            json.dumps({"error": "truth_missing", "path": str(truth_path)}, indent=2),
            encoding="utf-8",
        )
        return 1

    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    trades = truth.get("trades", [])
    exits = truth.get("exits", [])

    total_pnl = sum(float(t.get("pnl_usd") or 0) for t in trades)
    exit_pnl = sum(float(e.get("pnl") or 0) for e in exits)

    review = {
        "no_suppression": args.no_suppression,
        "window": {
            "start": truth.get("window_start"),
            "end": truth.get("window_end"),
            "days": truth.get("days"),
        },
        "counts": {
            "trades": len(trades),
            "exits": len(exits),
            "bar_dates_available": truth.get("bar_dates_available", 0),
        },
        "pnl": {
            "total_from_trades_usd": round(total_pnl, 4),
            "total_from_exits_usd": round(exit_pnl, 4),
        },
        "profit_bleed_hypotheses": [
            "Entry selectivity too low: high-score bucket still negative after costs.",
            "Direction choice weak: long/short not aligned with realized returns.",
            "Exit timing suboptimal: winners cut early or losers linger.",
            "Sizing miscalibrated: size not proportional to edge/volatility.",
            "Costs/slippage underestimated: apparent edge disappears after execution.",
        ],
        "required_next_fixes": [],
    }

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = REPO / out_path
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "MASSIVE_REVIEW_SEED.json").write_text(json.dumps(review, indent=2, default=str), encoding="utf-8")
    print(f"Wrote massive review -> {out_path}/MASSIVE_REVIEW_SEED.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
