#!/usr/bin/env python3
"""
Assert that the daily promotion quota is satisfied for the given date.
Reads CSA_PROMOTION_RECORD_<date>.json; exits 1 if missing or quota_satisfied false.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Assert daily promotion quota satisfied")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--promotion-record", required=True, help="CSA_PROMOTION_RECORD_<date>.json")
    args = ap.parse_args()

    path = Path(args.promotion_record)
    if not path.exists():
        print(f"Promotion record missing: {path}", file=sys.stderr)
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("date") != args.date:
        print(f"Record date {data.get('date')} != requested {args.date}", file=sys.stderr)
        return 1
    if not data.get("quota_satisfied", False):
        print("Quota not satisfied: quota_satisfied is false", file=sys.stderr)
        return 1

    print("Daily promotion quota satisfied:", data.get("promotion_type"), data.get("selected_parameter"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
