#!/usr/bin/env python3
"""
Run Alpaca DATA_READY finalization on the droplet.
- Runs full pipeline with join and sample gates.
- On Step 1 failure: reads ALPACA_JOIN_INTEGRITY_BLOCKER_<TS>.md, classifies blocker,
  retries once; hard stop after 2 attempts with FAILURE REPORT.
- On success: --data-ready writes final board + CSA + SRE and sends Telegram.
No strategy or execution logic changes. Telemetry, dataset, and analysis only.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPORTS_AUDIT = REPO / "reports" / "audit"
PIPELINE = REPO / "scripts" / "alpaca_edge_2000_pipeline.py"

BLOCKER_CLASSES = ("JOIN_INTEGRITY", "SAMPLE_SIZE", "ATTRIBUTION_MISSING")


def _latest_blocker() -> Path | None:
    """Return path to most recent ALPACA_JOIN_INTEGRITY_BLOCKER_<TS>.md, or None."""
    if not REPORTS_AUDIT.exists():
        return None
    candidates = list(REPORTS_AUDIT.glob("ALPACA_JOIN_INTEGRITY_BLOCKER_*.md"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def classify_blocker(blocker_path: Path) -> str:
    """Read blocker file and return JOIN_INTEGRITY | SAMPLE_SIZE | ATTRIBUTION_MISSING."""
    text = blocker_path.read_text(encoding="utf-8", errors="replace")
    for c in BLOCKER_CLASSES:
        if f"**{c}**" in text or c in text:
            return c
    if "Sample size" in text or "SAMPLE_SIZE" in text:
        return "SAMPLE_SIZE"
    if "Join coverage" in text or "join coverage" in text:
        return "JOIN_INTEGRITY"
    return "JOIN_INTEGRITY"  # default


def run_pipeline(
    max_trades: int = 2000,
    min_join_coverage_pct: float = 98.0,
    min_trades: int = 200,
    min_final_exits: int = 200,
    data_ready: bool = True,
    allow_missing_attribution: bool = False,
) -> int:
    """Run alpaca_edge_2000_pipeline.py; return exit code."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO)
    cmd = [
        sys.executable,
        str(PIPELINE),
        "--max-trades", str(max_trades),
        "--min-join-coverage-pct", str(min_join_coverage_pct),
        "--min-trades", str(min_trades),
        "--min-final-exits", str(min_final_exits),
    ]
    if data_ready:
        cmd.append("--data-ready")
    if allow_missing_attribution:
        cmd.append("--allow-missing-attribution")
    r = subprocess.run(cmd, cwd=str(REPO), env=env)
    return r.returncode


def write_failure_report(attempt: int, blocker_path: Path | None, classification: str, blocker_preview: str) -> Path:
    """Emit FAILURE REPORT with evidence. Returns path to report."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORTS_AUDIT / f"ALPACA_DATA_READY_FAILURE_REPORT_{ts}.md"
    REPORTS_AUDIT.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Alpaca DATA_READY failure report\n\n")
        f.write(f"- **Timestamp:** {ts}\n")
        f.write(f"- **Attempts:** {attempt}\n")
        f.write(f"- **Blocker file:** `{blocker_path}`\n")
        f.write(f"- **Classification:** {classification}\n\n")
        f.write("## Evidence (blocker preview)\n\n```\n")
        f.write(blocker_preview[:2000] if blocker_preview else "(none)")
        f.write("\n```\n")
        f.write("\n## Resolution\n\n")
        if classification == "SAMPLE_SIZE":
            f.write("Wait for more trades. No code change.\n")
        elif classification == "JOIN_INTEGRITY":
            f.write("Normalize trade_key derivation or attribution emission; re-run pipeline.\n")
        else:
            f.write("Add missing telemetry emission (no behavior change); re-run pipeline.\n")
    return path


def main() -> int:
    max_trades = int(os.environ.get("MAX_TRADES", "2000"))
    min_join = float(os.environ.get("MIN_JOIN_COVERAGE_PCT", "98"))
    min_trades = int(os.environ.get("MIN_TRADES", "200"))
    min_final_exits = int(os.environ.get("MIN_FINAL_EXITS", "200"))

    for attempt in range(1, 3):
        exit_code = run_pipeline(
            max_trades=max_trades,
            min_join_coverage_pct=min_join,
            min_trades=min_trades,
            min_final_exits=min_final_exits,
            data_ready=True,
            allow_missing_attribution=False,
        )
        if exit_code == 0:
            print("DATA_READY achieved. Final artifacts and Telegram sent.")
            return 0

        blocker_path = _latest_blocker()
        classification = "JOIN_INTEGRITY"
        blocker_preview = ""
        if blocker_path:
            classification = classify_blocker(blocker_path)
            blocker_preview = blocker_path.read_text(encoding="utf-8", errors="replace")

        print(f"Attempt {attempt} failed. Blocker: {blocker_path}; classification: {classification}", file=sys.stderr)

        if classification == "SAMPLE_SIZE":
            report = write_failure_report(attempt, blocker_path, classification, blocker_preview)
            print(f"SAMPLE_SIZE: wait for more trades. Failure report: {report}", file=sys.stderr)
            return 1

        if attempt == 2:
            report = write_failure_report(attempt, blocker_path, classification, blocker_preview)
            print(f"Same blocker persisted after 2 attempts. Failure report: {report}", file=sys.stderr)
            return 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
