#!/usr/bin/env python3
"""
Check UW health for the day: exit 1 if no UW adjustments logged or error rate > threshold.
Usage: python scripts/check_uw_health.py [--date YYYY-MM-DD] [--error-rate-threshold 0.05]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
UW_ADJUSTMENTS = REPO_ROOT / "logs" / "uw_entry_adjustments.jsonl"
UW_ERRORS = REPO_ROOT / "logs" / "uw_errors.jsonl"


def iter_jsonl(path: Path):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def main():
    ap = argparse.ArgumentParser(description="Check UW health for EOD")
    ap.add_argument("--date", default=None, help="Filter by date YYYY-MM-DD (default: today)")
    ap.add_argument("--error-rate-threshold", type=float, default=0.05, help="Fail if error rate > this (default 0.05)")
    args = ap.parse_args()
    date_str = args.date
    if not date_str:
        from datetime import datetime, timezone
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    adjustments = list(iter_jsonl(UW_ADJUSTMENTS))
    adjustments_today = [r for r in adjustments if date_str in str(r.get("timestamp", ""))[:10]]
    if not adjustments_today and adjustments:
        adjustments_today = adjustments
    errors = list(iter_jsonl(UW_ERRORS))
    errors_today = [r for r in errors if date_str in str(r.get("timestamp", ""))[:10]]
    if not errors_today and errors:
        errors_today = errors
    calls_today = len(adjustments_today)
    errors_count = len(errors_today)
    if calls_today == 0:
        print("FAIL: No UW entry adjustments logged for the day.", file=sys.stderr)
        sys.exit(1)
    total_calls = calls_today + errors_count
    error_rate = errors_count / total_calls if total_calls else 0.0
    if error_rate > args.error_rate_threshold:
        print(f"FAIL: UW error rate {error_rate:.2%} > {args.error_rate_threshold:.2%}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: UW adjustments={calls_today}, errors={errors_count}, error_rate={error_rate:.2%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
