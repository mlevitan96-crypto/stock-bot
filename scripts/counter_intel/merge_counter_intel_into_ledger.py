#!/usr/bin/env python3
"""
Merge COUNTER_INTEL_EVENTS into the ledger's counter_intel list and overwrite ledger.
Called after emit_counter_intel_events so Phase 3 assertion can pass from ledger.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge counter-intel events into ledger")
    ap.add_argument("--ledger", required=True, help="Path to FULL_TRADE_LEDGER_<date>.json (modified in place)")
    ap.add_argument("--counter-intel", required=True, help="Path to COUNTER_INTEL_EVENTS_<date>.json")
    args = ap.parse_args()

    ledger_path = Path(args.ledger)
    ci_path = Path(args.counter_intel)
    if not ledger_path.exists():
        print(f"Ledger missing: {ledger_path}", file=sys.stderr)
        return 2
    if not ci_path.exists():
        print(f"Counter-intel file missing: {ci_path}", file=sys.stderr)
        return 2

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ci_data = json.loads(ci_path.read_text(encoding="utf-8"))
    events = ci_data.get("events", [])
    if not isinstance(events, list):
        print("Counter-intel 'events' is not a list", file=sys.stderr)
        return 2

    existing = list(ledger.get("counter_intel") or [])
    merged = existing + events
    ledger["counter_intel"] = merged
    if "summary" in ledger and isinstance(ledger["summary"], dict):
        ledger["summary"]["counter_intel_count"] = len(merged)

    ledger_path.write_text(json.dumps(ledger, indent=2, default=str), encoding="utf-8")
    print("Merged", len(events), "CI events into ledger; counter_intel count:", len(merged))
    return 0


if __name__ == "__main__":
    sys.exit(main())
