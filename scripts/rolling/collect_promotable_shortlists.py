#!/usr/bin/env python3
"""
Collect daily promotable shortlists over a date range into a single history JSON.
Read-only; used by rolling daily review (shadow-only).
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


def _parse_date(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def _date_range(start: datetime, end: datetime):
    d = start
    while d <= end:
        yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect promotable shortlists over date range.")
    parser.add_argument("--start-date", required=True, help="Start date YYYY-MM-DD.")
    parser.add_argument("--end-date", required=True, help="End date YYYY-MM-DD.")
    parser.add_argument("--input-dir", default="reports/shadow", help="Directory containing shortlist files.")
    parser.add_argument("--output", required=True, help="Output PROMOTABLE_HISTORY_${END_DATE}.json path.")
    args = parser.parse_args()

    root = Path(os.getcwd())
    input_dir = root / args.input_dir
    start = _parse_date(args.start_date)
    end = _parse_date(args.end_date)

    history = {
        "start_date": args.start_date,
        "end_date": args.end_date,
        "days": [],
    }

    for date_str in _date_range(start, end):
        # Prefer .promotable.backfill.json, then .promotable.json
        for suffix in (".promotable.backfill.json", ".promotable.json"):
            path = input_dir / f"PROMOTION_SHORTLIST_{date_str}{suffix}"
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                shortlist = data.get("shortlist", [])
                history["days"].append({
                    "date": date_str,
                    "path": str(path.relative_to(root)),
                    "count": len(shortlist),
                    "entries": [
                        {
                            "rank": e.get("rank"),
                            "config_id": e.get("config_id"),
                            "metrics": e.get("metrics"),
                        }
                        for e in shortlist
                    ],
                })
                break
    # If no file for a date, skip (don't add empty day)

    out_path = root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    print(f"Wrote {out_path} ({len(history['days'])} days)")


if __name__ == "__main__":
    main()
