#!/usr/bin/env python3
"""
Validate the Alpaca governance experiment 1 hypothesis ledger.
Analysis-only; no execution gating. Exit 0 if valid, non-zero if invalid or stale.
Safe if file missing or empty (treated as invalid for validation purposes; no blocking).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

LEDGER_PATH = Path(__file__).resolve().parents[1] / "state" / "governance_experiment_1_hypothesis_ledger_alpaca.json"

REQUIRED_KEYS = {"change_id", "timestamp", "profit_hypothesis_present"}
VALID_VALUES = {"YES", "NO"}


def main() -> int:
    if not LEDGER_PATH.exists():
        print(f"Ledger missing: {LEDGER_PATH}", file=sys.stderr)
        return 1
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Ledger invalid or unreadable: {e}", file=sys.stderr)
        return 1

    if not isinstance(data, list):
        print("Ledger root must be a list of entries", file=sys.stderr)
        return 1

    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            print(f"Entry {i}: not an object", file=sys.stderr)
            return 1
        missing = REQUIRED_KEYS - set(entry)
        if missing:
            print(f"Entry {i}: missing keys {missing}", file=sys.stderr)
            return 1
        if entry.get("profit_hypothesis_present") not in VALID_VALUES:
            print(f"Entry {i}: profit_hypothesis_present must be YES or NO", file=sys.stderr)
            return 1

    print(f"Ledger valid: {LEDGER_PATH} ({len(data)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
