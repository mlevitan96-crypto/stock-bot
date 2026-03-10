#!/usr/bin/env python3
"""
Verify full trade ledger JSON: exists, valid structure, optional duplicate check.
Used in Full Day Trading Intelligence Audit Phase 1.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify trade ledger integrity")
    ap.add_argument("--ledger", required=True, help="Path to FULL_TRADE_LEDGER_<date>.json")
    ap.add_argument("--fail-on-missing", action="store_true", default=True, help="Exit 1 if file missing")
    ap.add_argument("--fail-on-partial", action="store_true", default=True, help="Exit 1 if missing required keys")
    ap.add_argument("--fail-on-duplicate", action="store_true", help="Exit 1 if duplicate trade ids present")
    ap.add_argument("--base-dir", default=None, help="Repo root for relative ledger path")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    ledger_path = base / args.ledger if not Path(args.ledger).is_absolute() else Path(args.ledger)

    if not ledger_path.exists():
        if args.fail_on_missing:
            print("Ledger missing:", ledger_path, file=sys.stderr)
            return 1
        print("Ledger missing (not failing):", ledger_path)
        return 0

    try:
        data = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print("Invalid ledger:", e, file=sys.stderr)
        return 1

    required_keys = ["date", "executed", "blocked", "counter_intel", "summary"]
    if args.fail_on_partial:
        for k in required_keys:
            if k not in data:
                print("Ledger missing key:", k, file=sys.stderr)
                return 1

    if args.fail_on_duplicate:
        seen = set()
        for lst in [data.get("executed", []), data.get("blocked", []), data.get("counter_intel", [])]:
            for e in lst:
                tid = e.get("trade_id") or (e.get("ts"), e.get("symbol"), e.get("exit_ts"))
                if tid in seen:
                    print("Duplicate trade:", tid, file=sys.stderr)
                    return 1
                seen.add(tid)

    print("OK:", ledger_path, "summary:", data.get("summary", {}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
