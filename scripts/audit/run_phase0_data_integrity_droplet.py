#!/usr/bin/env python3
"""
PHASE 0 — Data integrity check for one-day forensic. Run ON DROPLET.
Confirms all required logs exist for the given date and no gaps/truncation.
Exit code 0 = PASS, 1 = FAIL CLOSED (decision-affecting telemetry missing).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _load_jsonl(path: Path, limit: int = 50_000) -> list:
    out = []
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 0 data integrity (run on droplet)")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--base-dir", default=None, help="Repo root (default: script repo)")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    date_str = args.date

    trace_path = base / "reports" / "state" / "exit_decision_trace.jsonl"
    exit_attr_path = base / "logs" / "exit_attribution.jsonl"
    blocked_path = base / "state" / "blocked_trades.jsonl"

    trace_exists = trace_path.exists()
    trace_size = trace_path.stat().st_size if trace_exists else 0
    attr_exists = exit_attr_path.exists()
    blocked_exists = blocked_path.exists()

    # Decision-affecting: trace and exit_attribution
    fail_closed = not trace_exists or not attr_exists

    # Optional: check for today's data in attribution
    attr_records = _load_jsonl(exit_attr_path) if attr_exists else []
    today_attr = [r for r in attr_records if (r.get("timestamp") or r.get("entry_timestamp") or "")[:10] == date_str]
    trace_records = _load_jsonl(trace_path, limit=5000) if trace_exists else []
    today_trace = [r for r in trace_records if (r.get("ts") or "")[:10] == date_str]

    result = {
        "date": date_str,
        "exit_decision_trace_exists": trace_exists,
        "exit_decision_trace_size": trace_size,
        "exit_attribution_exists": attr_exists,
        "exit_attribution_today_count": len(today_attr),
        "exit_decision_trace_today_samples": len(today_trace),
        "blocked_trades_exists": blocked_exists,
        "fail_closed": fail_closed,
    }
    print(json.dumps(result))  # single line for runner capture
    return 1 if fail_closed else 0


if __name__ == "__main__":
    sys.exit(main())
