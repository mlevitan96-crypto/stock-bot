#!/usr/bin/env python3
"""
CSA: Analyze counter-intel economic impact — opportunity cost vs protection.
Surfaces would_have_pnl (foregone) vs risk_reason (protection) for board visibility.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze CI economic impact")
    ap.add_argument("--counter-intel", required=True, help="Path to COUNTER_INTEL_ENRICHED_<date>.json")
    ap.add_argument("--ledger", required=True, help="Path to FULL_TRADE_LEDGER_<date>.json")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    ci_path = Path(args.counter_intel)
    ledger_path = Path(args.ledger)
    if not ci_path.exists():
        print(f"Counter-intel file missing: {ci_path}", file=sys.stderr)
        return 2
    if not ledger_path.exists():
        print(f"Ledger missing: {ledger_path}", file=sys.stderr)
        return 2

    ci_data = json.loads(ci_path.read_text(encoding="utf-8"))
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    events = ci_data.get("events", []) or []

    opportunity_cost_usd = 0.0
    by_risk_reason = defaultdict(lambda: {"count": 0, "would_have_pnl_sum": 0.0})
    by_symbol = defaultdict(lambda: {"count": 0, "would_have_pnl": None})

    for e in events:
        if not isinstance(e, dict):
            continue
        wh = e.get("would_have_pnl")
        if wh is not None and isinstance(wh, (int, float)):
            opportunity_cost_usd += float(wh)
        risk = e.get("risk_reason") or "unknown"
        by_risk_reason[risk]["count"] += 1
        if wh is not None and isinstance(wh, (int, float)):
            by_risk_reason[risk]["would_have_pnl_sum"] += float(wh)
        sym = e.get("symbol") or "unknown"
        by_symbol[sym]["count"] += 1
        if by_symbol[sym]["would_have_pnl"] is None and wh is not None:
            by_symbol[sym]["would_have_pnl"] = wh

    out = {
        "date": ci_data.get("date"),
        "event_count": len(events),
        "opportunity_cost_usd": round(opportunity_cost_usd, 4),
        "protection_note": "CI blocks reduce exposure; opportunity_cost = foregone would_have_pnl when present.",
        "by_risk_reason": dict(by_risk_reason),
        "by_symbol": {k: dict(v) for k, v in sorted(by_symbol.items())},
        "summary": {
            "total_ci_events": len(events),
            "opportunity_cost_usd": round(opportunity_cost_usd, 4),
            "risk_reasons_count": len(by_risk_reason),
        },
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path, "opportunity_cost_usd:", out["opportunity_cost_usd"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
