#!/usr/bin/env python3
"""
Validate Alpaca lifecycle events (gate traces / blocked_trades, shadow stream)
against docs/ALPACA_LIFECYCLE_EVENTS_SCHEMA.md.

Reads state/blocked_trades.jsonl and logs/shadow.jsonl (optional).
Emits WARN/FAIL to stdout and optionally writes a report.
Default: WARN only (--fail-on-required for strict mode).

Usage:
  python scripts/validate_lifecycle_events_schema.py [--date YYYY-MM-DD] [--report PATH] [--fail-on-required]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BLOCKED_PATH = REPO / "state" / "blocked_trades.jsonl"
SHADOW_PATH = REPO / "logs" / "shadow.jsonl"
GATE_PATH = REPO / "logs" / "gate.jsonl"


def _iter_jsonl(path: Path, date_str: str | None = None):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").strip().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            if date_str:
                ts = rec.get("timestamp") or rec.get("ts") or ""
                if isinstance(ts, str) and not ts.startswith(date_str):
                    continue
            yield rec
        except Exception:
            continue


def validate_blocked_trades(blocked_path: Path, date_str: str | None) -> list[str]:
    errs: list[str] = []
    for rec in _iter_jsonl(blocked_path, date_str):
        if not isinstance(rec, dict):
            errs.append("FAIL: blocked_trades record is not a dict")
            continue
        if not rec.get("timestamp"):
            errs.append("FAIL: blocked_trades missing required 'timestamp'")
        if not rec.get("symbol"):
            errs.append("FAIL: blocked_trades missing required 'symbol'")
        if not rec.get("reason") and not rec.get("block_reason"):
            errs.append("FAIL: blocked_trades missing required 'reason' (or 'block_reason')")
        if not (rec.get("score") is not None or rec.get("candidate_score") is not None):
            errs.append("WARN: blocked_trades missing score/candidate_score (optional but recommended)")
    return errs


def validate_shadow(shadow_path: Path, date_str: str | None) -> list[str]:
    errs: list[str] = []
    for rec in _iter_jsonl(shadow_path, date_str):
        if not isinstance(rec, dict):
            errs.append("FAIL: shadow record is not a dict")
            continue
        et = rec.get("event_type")
        if not et:
            errs.append("FAIL: shadow record missing required 'event_type'")
        ts = rec.get("ts") or rec.get("timestamp_utc")
        if not ts:
            errs.append("FAIL: shadow record missing timestamp ('ts' or 'timestamp_utc')")
        if et == "shadow_executed" and not rec.get("symbol"):
            errs.append("WARN: shadow_executed missing 'symbol'")
        if et == "shadow_candidate" and not rec.get("symbol"):
            errs.append("WARN: shadow_candidate missing 'symbol'")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate lifecycle events schema (blocked_trades, shadow)")
    ap.add_argument("--date", default=None, help="Filter to date YYYY-MM-DD (default: today)")
    ap.add_argument("--report", default=None, help="Write report to PATH (optional)")
    ap.add_argument("--fail-on-required", action="store_true", help="Exit 1 on any FAIL (required field missing)")
    ap.add_argument("--shadow", action="store_true", default=True, help="Validate shadow.jsonl (default: True)")
    ap.add_argument("--no-shadow", action="store_false", dest="shadow", help="Skip shadow.jsonl")
    args = ap.parse_args()

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    all_warn: list[str] = []
    all_fail: list[str] = []

    # Blocked trades
    if BLOCKED_PATH.exists():
        for e in validate_blocked_trades(BLOCKED_PATH, date_str):
            if e.startswith("FAIL:"):
                all_fail.append(e)
            else:
                all_warn.append(e)
    else:
        all_warn.append("WARN: state/blocked_trades.jsonl not found (skip)")

    # Shadow
    if args.shadow:
        if SHADOW_PATH.exists():
            for e in validate_shadow(SHADOW_PATH, date_str):
                if e.startswith("FAIL:"):
                    all_fail.append(e)
                else:
                    all_warn.append(e)
        else:
            all_warn.append("WARN: logs/shadow.jsonl not found (skip)")

    # Report
    lines = [
        f"Lifecycle schema validation ({date_str})",
        f"FAIL: {len(all_fail)}",
        f"WARN: {len(all_warn)}",
        "",
    ]
    for f in all_fail:
        lines.append(f"  {f}")
    for w in all_warn:
        lines.append(f"  {w}")
    report_text = "\n".join(lines)
    print(report_text)

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(report_text, encoding="utf-8")

    if args.fail_on_required and all_fail:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
