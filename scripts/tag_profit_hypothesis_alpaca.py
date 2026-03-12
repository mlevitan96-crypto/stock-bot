#!/usr/bin/env python3
"""
Append a single hypothesis-ledger entry for Alpaca governance experiment 1.
Analysis-only; append-only. No execution gating, no deploy blocking.
Schema: change_id (Git commit SHA), timestamp (ISO8601), profit_hypothesis_present (YES | NO).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LEDGER_PATH = Path(__file__).resolve().parents[1] / "state" / "governance_experiment_1_hypothesis_ledger_alpaca.json"


def get_head_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
            cwd=Path(__file__).resolve().parents[1],
        )
        return (out.stdout or "").strip() or "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> int:
    # YES | NO from env or argv
    raw = (os.environ.get("PROFIT_HYPOTHESIS_PRESENT") or "").strip().upper()
    if not raw and len(sys.argv) > 1:
        raw = (sys.argv[1] or "").strip().upper()
    if raw not in ("YES", "NO"):
        print("Usage: tag_profit_hypothesis_alpaca.py [YES|NO]", file=sys.stderr)
        print("  or set PROFIT_HYPOTHESIS_PRESENT=YES|NO", file=sys.stderr)
        return 2
    profit_hypothesis_present = raw

    entry = {
        "change_id": get_head_sha(),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "profit_hypothesis_present": profit_hypothesis_present,
    }

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: list = []
    if LEDGER_PATH.exists():
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                existing = []
        except (json.JSONDecodeError, OSError):
            existing = []

    existing.append(entry)
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    print(f"Appended entry to {LEDGER_PATH}: change_id={entry['change_id']}, profit_hypothesis_present={profit_hypothesis_present}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
