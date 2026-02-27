#!/usr/bin/env python3
"""
Validate daily governance run artifacts per docs/ALPACA_DAILY_RUN_INTEGRITY_CONTRACT.md.

Verifies: required files exist, non-empty, timestamps within run window;
state/molt_last_run.json present and exit_code 0.
Exit non-zero on any FAIL. Produces concise PASS/FAIL summary.

Usage:
  python scripts/validate_daily_governance_artifacts.py [--date YYYY-MM-DD] [--base-dir PATH] [--skip-timestamps]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _run_window(date_str: str):
    """Run window: 00:00 UTC on date through 23:59:59 UTC on date + 12h."""
    d = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start = d.replace(hour=0, minute=0, second=0, microsecond=0)
    end = d.replace(hour=23, minute=59, second=59, microsecond=999999) + timedelta(hours=12)
    return start, end


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate daily governance artifacts (fail-closed)")
    ap.add_argument("--date", default=None, help="Run date YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--base-dir", default=None, help="Repo root (default: script parent)")
    ap.add_argument("--skip-timestamps", action="store_true", help="Do not fail on timestamp misalignment")
    args = ap.parse_args()

    base = Path(args.base_dir) if args.base_dir else REPO
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_start, run_end = _run_window(date_str)
    failures: list[str] = []
    warnings: list[str] = []

    # 1. Molt last run state
    molt_json = base / "state" / "molt_last_run.json"
    if not molt_json.exists():
        failures.append("state/molt_last_run.json missing (Molt did not run or failed before writing)")
    else:
        try:
            data = json.loads(molt_json.read_text(encoding="utf-8"))
            if data.get("exit_code") != 0:
                failures.append(f"state/molt_last_run.json exit_code={data.get('exit_code')} (Molt exited with error)")
            run_date = str(data.get("date", ""))
            if run_date != date_str:
                warnings.append(f"state/molt_last_run.json date={run_date} != validate date {date_str}")
        except Exception as e:
            failures.append(f"state/molt_last_run.json invalid: {e}")

    # 2. Required report files (must exist and non-empty)
    required = [
        f"reports/LEARNING_STATUS_{date_str}.md",
        f"reports/ENGINEERING_HEALTH_{date_str}.md",
        f"reports/PROMOTION_DISCIPLINE_{date_str}.md",
        f"reports/MEMORY_BANK_CHANGE_PROPOSAL_{date_str}.md",
        "reports/GOVERNANCE_DISCOVERY_INDEX.md",
    ]
    board_one = [
        base / f"reports/PROMOTION_PROPOSAL_{date_str}.md",
        base / f"reports/REJECTION_WITH_REASON_{date_str}.md",
    ]
    board_ok = any(p.exists() and p.stat().st_size > 0 for p in board_one)
    if not board_ok:
        failures.append("Governance chair output missing: neither PROMOTION_PROPOSAL nor REJECTION_WITH_REASON present and non-empty")

    for rel in required:
        path = base / rel
        if not path.exists():
            failures.append(f"Missing: {rel}")
        elif path.stat().st_size == 0:
            failures.append(f"Empty: {rel}")
        elif not args.skip_timestamps:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < run_start:
                failures.append(f"Timestamp before run window: {rel} (mtime={mtime.isoformat()})")
            elif mtime > run_end:
                failures.append(f"Timestamp after run window: {rel} (mtime={mtime.isoformat()})")

    # 3. At least one diagnostics summary
    diag_candidates = [
        base / f"reports/EXIT_JOIN_HEALTH_{date_str}.md",
        base / f"reports/BLOCKED_TRADE_INTEL_{date_str}.md",
    ]
    diag_ok = any(p.exists() and p.stat().st_size > 0 for p in diag_candidates)
    if not diag_ok:
        failures.append("No diagnostics summary: neither EXIT_JOIN_HEALTH nor BLOCKED_TRADE_INTEL present and non-empty")

    for p in diag_candidates:
        if p.exists() and p.stat().st_size > 0 and not args.skip_timestamps:
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            if mtime < run_start or mtime > run_end:
                failures.append(f"Timestamp misalignment: {p.relative_to(base)} (mtime={mtime.isoformat()})")
            break

    # 4. Board artifact timestamp if present
    for p in board_one:
        if p.exists() and p.stat().st_size > 0 and not args.skip_timestamps:
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            if mtime < run_start or mtime > run_end:
                failures.append(f"Timestamp misalignment: {p.relative_to(base)} (mtime={mtime.isoformat()})")
            break

    # Summary
    verdict = "PASS" if not failures else "FAIL"
    print(f"Daily governance artifact validation ({date_str})")
    print(f"Verdict: {verdict}")
    if failures:
        print("Failures:")
        for f in failures:
            print(f"  - {f}")
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")
    if verdict == "PASS":
        print("All required artifacts present, non-empty, and within run window.")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
