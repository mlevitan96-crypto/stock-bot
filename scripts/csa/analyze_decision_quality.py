#!/usr/bin/env python3
"""
CSA: Analyze decision quality from full-day ledger.
Classifies blocks, counter-intel, and computes opportunity-cost proxy.
Output feeds idea harvesting and board packet. Stub implements schema.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="CSA decision quality analysis")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--classify-blocks", action="store_true", default=True)
    ap.add_argument("--classify-counter-intel", action="store_true", default=True)
    ap.add_argument("--compute-opportunity-cost", action="store_true", default=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    path = Path(args.ledger)
    if not path.exists():
        print(f"Ledger missing: {path}", file=sys.stderr)
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))
    executed = data.get("executed", [])
    blocked = data.get("blocked", [])
    counter_intel = data.get("counter_intel", [])

    # Classify blocks by reason
    block_reasons: defaultdict[str, int] = defaultdict(int)
    for e in blocked:
        if isinstance(e, dict):
            for r in e.get("reason_codes") or [e.get("block_reason") or "unknown"]:
                if r:
                    block_reasons[r] += 1

    ci_reasons: defaultdict[str, int] = defaultdict(int)
    for e in counter_intel:
        if isinstance(e, dict):
            for r in e.get("reason_codes") or [e.get("block_reason") or "counter_intel"]:
                if r:
                    ci_reasons[r] += 1

    # Opportunity cost: placeholder (would need shadow PnL comparison for real)
    executed_pnl = sum(
        float(e.get("realized_pnl") or 0)
        for e in executed
        if isinstance(e, dict)
    )
    out = {
        "date": data.get("date"),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "blocks_classified": dict(block_reasons),
        "counter_intel_classified": dict(ci_reasons),
        "opportunity_cost_usd": None,
        "opportunity_cost_note": "Placeholder; requires shadow comparison for real $.",
        "executed_count": len(executed),
        "blocked_count": len(blocked),
        "counter_intel_count": len(counter_intel),
        "executed_pnl_sum": round(executed_pnl, 4),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("Wrote", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
