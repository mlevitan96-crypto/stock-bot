#!/usr/bin/env python3
"""
Proof of resolution: after a UW data fix, run this to show failure rate before vs after
and impact on candidate flow. Writes reports/uw_health/uw_fix_verification.md.
Usage: python scripts/uw_fix_verification.py [--before YYYY-MM-DD] [--after YYYY-MM-DD]
If no dates given, uses last 7 days as "after" and 7 days before that as "before".
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
UW_FAILURE_EVENTS = REPO / "reports" / "uw_health" / "uw_failure_events.jsonl"
OUT_MD = REPO / "reports" / "uw_health" / "uw_fix_verification.md"


def load_events_in_range(start_ts: float, end_ts: float) -> list[dict]:
    if not UW_FAILURE_EVENTS.exists():
        return []
    out = []
    for line in UW_FAILURE_EVENTS.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            ts = float(r.get("ts") or r.get("event_ts") or 0)
            if start_ts <= ts <= end_ts:
                out.append(r)
        except Exception:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default=None, help="End date of 'before' window (YYYY-MM-DD)")
    ap.add_argument("--after", default=None, help="Start date of 'after' window (YYYY-MM-DD)")
    ap.add_argument("--days", type=int, default=7, help="Window length in days for each period")
    args = ap.parse_args()
    now = datetime.now(timezone.utc)
    if args.after:
        try:
            after_start = datetime.strptime(args.after, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            after_start = now - timedelta(days=args.days)
        after_end = after_start + timedelta(days=args.days)
    else:
        after_end = now
        after_start = now - timedelta(days=args.days)
    if args.before:
        try:
            before_end = datetime.strptime(args.before, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            before_end = after_start - timedelta(days=1)
        before_start = before_end - timedelta(days=args.days)
    else:
        before_end = after_start - timedelta(days=1)
        before_start = before_end - timedelta(days=args.days)

    before_events = load_events_in_range(before_start.timestamp(), before_end.timestamp())
    after_events = load_events_in_range(after_start.timestamp(), after_end.timestamp())
    before_by_class = Counter(r.get("failure_class") or "UNKNOWN" for r in before_events)
    after_by_class = Counter(r.get("failure_class") or "UNKNOWN" for r in after_events)
    before_total = len(before_events)
    after_total = len(after_events)
    before_days = (before_end - before_start).total_seconds() / 86400
    after_days = (after_end - after_start).total_seconds() / 86400
    rate_before = before_total / before_days if before_days else 0
    rate_after = after_total / after_days if after_days else 0

    lines = [
        "# UW fix verification",
        "",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Windows",
        f"- **Before**: {before_start.date()} to {before_end.date()} ({before_days:.0f} days)",
        f"- **After**: {after_start.date()} to {after_end.date()} ({after_days:.0f} days)",
        "",
        "## Failure rate",
        f"- Before: **{before_total}** events ({rate_before:.1f}/day)",
        f"- After: **{after_total}** events ({rate_after:.1f}/day)",
        "",
        "## Failure class distribution",
        "",
        "### Before",
        "",
    ]
    for cls, count in before_by_class.most_common():
        lines.append(f"- {cls}: {count}")
    lines.extend(["", "### After", ""])
    for cls, count in after_by_class.most_common():
        lines.append(f"- {cls}: {count}")
    lines.extend([
        "",
        "## Impact on candidate flow",
        "",
    ])
    if after_total < before_total:
        pct = 100.0 * (before_total - after_total) / before_total if before_total else 0
        lines.append(f"- Failure events **decreased** by {before_total - after_total} ({pct:.1f}%). Fix likely reduced data-related blocks.")
    elif after_total > before_total:
        lines.append(f"- Failure events increased by {after_total - before_total}. Investigate for regression or new data gaps.")
    else:
        lines.append("- No change in event count. Verify fix was deployed in the 'after' window.")
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
