#!/usr/bin/env python3
"""
CSA: Assert that the ledger contains at least --min-events counter-intel events.
FAIL-CLOSED: exit non-zero if counter_intel count < min_events.
Use --min-events 0 for days when no counter-intel activity is expected.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Assert counter-intel presence in ledger or counter-intel file")
    ap.add_argument("--ledger", required=True, help="Path to FULL_TRADE_LEDGER_<date>.json")
    ap.add_argument("--counter-intel", default=None, help="Optional path to COUNTER_INTEL_EVENTS_<date>.json; if set, count from this file")
    ap.add_argument("--min-events", type=int, default=1, help="Minimum counter_intel events (default 1; use 0 to allow none)")
    args = ap.parse_args()

    ledger_path = Path(args.ledger)
    if not ledger_path.exists():
        print(f"Ledger missing: {ledger_path}", file=sys.stderr)
        return 2

    if args.counter_intel:
        ci_path = Path(args.counter_intel)
        if not ci_path.exists():
            print(f"Counter-intel file missing: {ci_path}", file=sys.stderr)
            return 2
        ci_data = json.loads(ci_path.read_text(encoding="utf-8"))
        events = ci_data.get("events", [])
        if not isinstance(events, list):
            print("Counter-intel file 'events' is not a list", file=sys.stderr)
            return 2
        n = len(events)
    else:
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
        counter_intel = data.get("counter_intel", [])
        if not isinstance(counter_intel, list):
            print("Ledger counter_intel is not a list", file=sys.stderr)
            return 2
        n = len(counter_intel)

    if n < args.min_events:
        print(
            f"COUNTER_INTEL_ASSERTION: FAIL (count={n} < min_events={args.min_events})",
            file=sys.stderr,
        )
        return 3
    print(f"COUNTER_INTEL_ASSERTION: PASS (count={n})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
