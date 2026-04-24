#!/usr/bin/env python3
"""
Harvest promotion candidates from ledger, decision quality, and signal profitability.
Mass extraction: emit all ideas above min opportunity cost. Feeds dedupe + persona review.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Harvest promotion candidates")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--decision-quality", required=True)
    ap.add_argument("--signal-profitability", required=True)
    ap.add_argument("--min-opportunity-cost-usd", type=float, default=10.0)
    ap.add_argument("--emit-all-ideas", action="store_true", default=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    ledger_path = Path(args.ledger)
    dq_path = Path(args.decision_quality)
    sig_path = Path(args.signal_profitability)
    if not ledger_path.exists():
        print(f"Ledger missing: {ledger_path}", file=sys.stderr)
        return 2
    if not dq_path.exists():
        print(f"Decision quality missing: {dq_path}", file=sys.stderr)
        return 2
    if not sig_path.exists():
        print(f"Signal profitability missing: {sig_path}", file=sys.stderr)
        return 2

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    dq = json.loads(dq_path.read_text(encoding="utf-8"))
    sig = json.loads(sig_path.read_text(encoding="utf-8"))

    ideas = []
    # From executed: ideas as symbol + side + opportunity proxy
    for e in (ledger.get("executed") or [])[:200]:
        if isinstance(e, dict):
            ideas.append({
                "type": "executed",
                "symbol": e.get("symbol"),
                "direction": e.get("direction"),
                "realized_pnl": e.get("realized_pnl"),
                "opportunity_cost_usd": None,
            })
    # From blocked: high-opportunity proxy (stub)
    for e in (ledger.get("blocked") or [])[:100]:
        if isinstance(e, dict):
            ideas.append({
                "type": "blocked",
                "symbol": e.get("symbol"),
                "reason_codes": e.get("reason_codes"),
                "opportunity_cost_usd": None,
            })

    out = {
        "date": ledger.get("date"),
        "ideas": ideas,
        "count": len(ideas),
        "min_opportunity_cost_usd": args.min_opportunity_cost_usd,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path, "ideas:", len(ideas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
