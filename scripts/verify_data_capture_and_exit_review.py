#!/usr/bin/env python3
"""
Verify data capture and exit review wiring for the full organism loop.

Checks (locally):
- Key capture files/dirs exist (logs/, state/, paths from EOD_DATA_PIPELINE)
- Exit review script and its dependencies exist
- Reports/exit_review output dir exists

Use --bootstrap to create state/ and state/blocked_trades.jsonl if missing
(so verification passes before first bot run or when no blocks have occurred).

Does NOT require droplet; for droplet checks use run_exit_review_on_droplet.py.
Run from repo root.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _bootstrap_capture_paths() -> None:
    """Create state/ and state/blocked_trades.jsonl if missing."""
    (REPO / "state").mkdir(parents=True, exist_ok=True)
    blocked = REPO / "state" / "blocked_trades.jsonl"
    if not blocked.is_file():
        blocked.write_text("", encoding="utf-8")
        print("Created state/blocked_trades.jsonl", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify data capture and exit review wiring.")
    parser.add_argument("--bootstrap", action="store_true", help="Create state/ and state/blocked_trades.jsonl if missing")
    args = parser.parse_args()
    if args.bootstrap:
        _bootstrap_capture_paths()

    errors: list[str] = []
    warnings: list[str] = []

    # Key capture paths (relative to REPO)
    capture_paths = [
        "logs",  # attribution.jsonl, exit_attribution.jsonl, run.jsonl
        "state",  # blocked_trades.jsonl, daily_start_equity.json, etc.
    ]
    for p in capture_paths:
        if not (REPO / p).exists():
            warnings.append(f"Dir missing (create when running live): {p}/")

    # Exit review script and dependencies
    exit_review_script = REPO / "scripts" / "run_exit_review_on_droplet.py"
    if not exit_review_script.exists():
        errors.append("scripts/run_exit_review_on_droplet.py not found")
    deps = [
        "scripts/analysis/attribution_loader.py",
        "scripts/analysis/run_exit_effectiveness_v2.py",
        "scripts/exit_tuning/suggest_exit_tuning.py",
        "src/exit/exit_attribution.py",
        "src/exit/exit_pressure_v3.py",
    ]
    for rel in deps:
        if not (REPO / rel).exists():
            errors.append(f"Missing dependency: {rel}")

    # Optional: key log files (may not exist until first run)
    optional_logs = [
        "logs/attribution.jsonl",
        "logs/exit_attribution.jsonl",
        "logs/master_trade_log.jsonl",
        "state/blocked_trades.jsonl",
        "logs/run.jsonl",
    ]
    for rel in optional_logs:
        if not (REPO / rel).exists():
            warnings.append(f"Capture file not present (expected after live runs): {rel}")

    # Report
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
    if warnings:
        for w in warnings:
            print("WARN:", w, file=sys.stderr)
    if not errors and not warnings:
        print("OK: Data capture and exit review wiring present.")
    elif not errors:
        print("OK: Exit review script and deps present; some capture paths optional until live.")
    else:
        print("FAIL: Fix errors above.", file=sys.stderr)
        return 1
    print("Exit review (on droplet): python scripts/run_exit_review_on_droplet.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
