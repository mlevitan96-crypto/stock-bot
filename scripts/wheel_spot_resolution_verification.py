#!/usr/bin/env python3
"""
Generate wheel spot resolution verification report from logs/system_events.jsonl.
Run on droplet or locally: python3 scripts/wheel_spot_resolution_verification.py [--repo /path] [--days 7]
Output: reports/wheel_spot_resolution_verification_<date>.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _tail_lines(path: Path, max_lines: int) -> list[str]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        return lines[-max_lines:] if len(lines) > max_lines else lines
    except Exception:
        return []


def main() -> int:
    ap = argparse.ArgumentParser(description="Wheel spot resolution verification report")
    ap.add_argument("--repo", type=str, default=str(ROOT), help="Repo root (logs, reports)")
    ap.add_argument("--days", type=int, default=7, help="Lookback days")
    args = ap.parse_args()
    base = Path(args.repo)
    logs_dir = base / "logs"
    reports_dir = base / "reports"
    sys_events_path = logs_dir / "system_events.jsonl"

    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=args.days)).date().isoformat()
    wheel_events: list[dict] = []
    for line in _tail_lines(sys_events_path, 100_000):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if rec.get("subsystem") == "wheel":
                ts = (rec.get("timestamp") or "")[:10]
                if ts >= cutoff_date:
                    wheel_events.append(rec)
        except json.JSONDecodeError:
            continue

    resolved = [e for e in wheel_events if e.get("event_type") == "wheel_spot_resolved"]
    unavailable = [e for e in wheel_events if e.get("event_type") == "wheel_spot_unavailable"]
    source_dist: dict[str, int] = defaultdict(int)
    for e in resolved:
        src = e.get("spot_source") or "unknown"
        source_dist[src] += 1

    run_started_ts: list[str] = []
    for e in wheel_events:
        if e.get("event_type") == "wheel_run_started":
            run_started_ts.append(e.get("timestamp") or "")
    first_run_after_cutoff = run_started_ts[0] if run_started_ts else None

    # First cycle where option chains were reached: first no_contracts_in_range or wheel_order_submitted after a run
    first_no_contracts = None
    first_order_submitted = None
    for e in wheel_events:
        if e.get("event_type") == "wheel_csp_skipped" and e.get("reason") == "no_contracts_in_range":
            first_no_contracts = first_no_contracts or e.get("timestamp")
        if e.get("event_type") == "wheel_order_submitted":
            first_order_submitted = first_order_submitted or e.get("timestamp")

    order_submitted_count = sum(1 for e in wheel_events if e.get("event_type") == "wheel_order_submitted")
    order_filled_count = sum(1 for e in wheel_events if e.get("event_type") == "wheel_order_filled")
    skip_counts: dict[str, int] = defaultdict(int)
    for e in wheel_events:
        if e.get("event_type") == "wheel_csp_skipped":
            skip_counts[e.get("reason") or "unknown"] += 1

    # Build report
    today = datetime.now(timezone.utc).date().isoformat()
    report_path = reports_dir / f"wheel_spot_resolution_verification_{today}.md"
    reports_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [
        "# Wheel Spot Resolution Verification Report",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}Z",
        f"**Repo:** {base}",
        f"**Lookback:** {args.days} days (since {cutoff_date})",
        "",
        "## 1. Spot resolution counts",
        f"- **wheel_spot_resolved:** {len(resolved)}",
        f"- **wheel_spot_unavailable:** {len(unavailable)}",
        "",
        "## 2. Spot source distribution (resolved only)",
    ]
    for src, count in sorted(source_dist.items(), key=lambda x: -x[1]):
        lines.append(f"- **{src}:** {count}")
    if not source_dist:
        lines.append("- (none)")
    lines.extend([
        "",
        "## 3. Option chain and orders",
        f"- **First wheel_run_started in window:** {first_run_after_cutoff or 'N/A'}",
        f"- **First no_contracts_in_range (option chains reached):** {first_no_contracts or 'N/A'}",
        f"- **First wheel_order_submitted:** {first_order_submitted or 'N/A'}",
        f"- **wheel_order_submitted count:** {order_submitted_count}",
        f"- **wheel_order_filled count:** {order_filled_count}",
        "",
        "## 4. Skip reasons (wheel_csp_skipped)",
    ])
    for reason, count in sorted(skip_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- **{reason}:** {count}")
    if not skip_counts:
        lines.append("- (none)")
    lines.append("")

    # Verdict and next blocker
    if len(resolved) == 0 and len(unavailable) > 0:
        lines.extend([
            "## 5. Verdict",
            "**FAIL — No spot resolved.** All cycles emitted wheel_spot_unavailable only. Wheel cannot reach option chain or submit orders until spot resolution succeeds (check Alpaca quote/bar API and normalize_alpaca_quote contract).",
            "",
        ])
    elif len(resolved) > 0 and order_submitted_count == 0:
        top_skip = max(skip_counts.items(), key=lambda x: x[1]) if skip_counts else ("none", 0)
        lines.extend([
            "## 5. Verdict",
            "**Spot resolution OK.** wheel_spot_resolved > 0. Wheel reaches spot resolution; next blocker (if any) is skip reason.",
            f"- **Dominant skip reason:** {top_skip[0]} ({top_skip[1]} occurrences). Address this to allow orders.",
            "",
        ])
    elif order_submitted_count > 0:
        lines.extend([
            "## 5. Verdict",
            "**PASS.** Spot resolved and wheel_order_submitted > 0. Wheel is capable of submitting CSP orders.",
            "",
        ])
    else:
        lines.extend([
            "## 5. Verdict",
            "Insufficient wheel events in window (no runs or no spot attempts). Run during market hours and re-run verification.",
            "",
        ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
