#!/usr/bin/env python3
"""
Use existing trade data (weekly evidence stage) to run forensic → surgical → replay for every
date in the pulled window, then multi-day validation. No need to wait for new days.

1. Pull data: python scripts/audit/collect_weekly_droplet_evidence.py
2. Run this script: python scripts/experiments/run_exit_lag_from_staged_evidence.py

Output: EXIT_LAG_SHADOW_RESULTS_<date>.json per date, then EXIT_LAG_MULTI_DAY_* and CSA verdict.
Paper = paper; promote to paper when CSA/adversarial/customer advocate say so.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STAGE_DEFAULT = REPO / "reports" / "audit" / "weekly_evidence_stage"


def _dates_with_data(stage_dir: Path) -> list[str]:
    """Return sorted list of YYYY-MM-DD that have at least one exit_attribution record in stage."""
    attr_path = stage_dir / "logs" / "exit_attribution.jsonl"
    if not attr_path.exists():
        return []
    seen: set[str] = set()
    with attr_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ts = rec.get("timestamp") or rec.get("entry_timestamp") or rec.get("ts") or ""
                prefix = str(ts)[:10]
                if len(prefix) == 10 and prefix[4] == "-":
                    seen.add(prefix)
            except json.JSONDecodeError:
                continue
    return sorted(seen)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Run exit-lag pipeline from staged evidence (previous days/weeks)")
    ap.add_argument("--stage-dir", default=None, help=f"Staged evidence dir (default: {STAGE_DEFAULT})")
    ap.add_argument("--max-dates", type=int, default=20, help="Max dates to process (default 20)")
    args = ap.parse_args()
    stage = Path(args.stage_dir) if args.stage_dir else STAGE_DEFAULT
    if not stage.is_dir():
        print(f"Stage dir not found: {stage}", file=sys.stderr)
        print("Run first: python scripts/audit/collect_weekly_droplet_evidence.py", file=sys.stderr)
        return 1
    if not (stage / "logs" / "exit_attribution.jsonl").exists():
        print("exit_attribution.jsonl not in stage. Run collect_weekly_droplet_evidence.py.", file=sys.stderr)
        return 1
    if not (stage / "reports" / "state" / "exit_decision_trace.jsonl").exists():
        print("exit_decision_trace.jsonl not in stage. Run collect_weekly_droplet_evidence.py.", file=sys.stderr)
        return 1

    dates = _dates_with_data(stage)[-args.max_dates:]
    if not dates:
        print("No dates with exit_attribution data in stage.", file=sys.stderr)
        return 1
    print(f"Found {len(dates)} date(s) with data: {dates[0]} .. {dates[-1]}", file=sys.stderr)

    for date_str in dates:
        print(f"  Forensic {date_str} ...", file=sys.stderr)
        r1 = subprocess.run(
            [sys.executable, "scripts/audit/run_why_we_didnt_win_forensic.py", "--date", date_str, "--fail-if-no-trace-above", "0.20", "--base-dir", str(stage)],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if r1.returncode != 0:
            print(f"    forensic failed (rc {r1.returncode}), skip", file=sys.stderr)
            continue
        print(f"  Surgical {date_str} ...", file=sys.stderr)
        r2 = subprocess.run(
            [sys.executable, "scripts/audit/run_intraday_shadow_exit_surgical.py", "--date", date_str],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r2.returncode != 0:
            print(f"    surgical failed (rc {r2.returncode}), skip", file=sys.stderr)
            continue
        print(f"  Replay {date_str} ...", file=sys.stderr)
        r3 = subprocess.run(
            [sys.executable, "scripts/experiments/run_exit_lag_shadow_replay.py", "--date", date_str, "--base-dir", str(stage)],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r3.returncode != 0:
            print(f"    replay failed (rc {r3.returncode}), skip", file=sys.stderr)

    exp_dir = REPO / "reports" / "experiments"
    results = list(exp_dir.glob("EXIT_LAG_SHADOW_RESULTS_*.json"))
    if not results:
        print("No EXIT_LAG_SHADOW_RESULTS_*.json produced. Check forensic/surgical/replay for errors.", file=sys.stderr)
        return 1
    print(f"Multi-day validation ({len(results)} day(s)) ...", file=sys.stderr)
    r4 = subprocess.run(
        [sys.executable, "scripts/experiments/run_exit_lag_multi_day_validation.py", "--days", "30"],
        cwd=REPO,
        timeout=90,
    )
    if r4.returncode != 0:
        print("Multi-day validation failed.", file=sys.stderr)
        return r4.returncode
    print("Done. Check reports/experiments/EXIT_LAG_MULTI_DAY_*.md and reports/audit/CSA_EXIT_LAG_MULTI_DAY_VERDICT.json for promote-or-not.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
