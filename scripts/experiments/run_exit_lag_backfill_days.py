#!/usr/bin/env python3
"""
Exit-lag backfill: produce EXIT_LAG_SHADOW_RESULTS_<date>.json for the last N trading days.
Run ON DROPLET. SRE: no live writes; phase0 (data integrity) per date; skip existing results.
CSA: backfill only produces evidence; no promotion. PAPER ONLY.

Failed reasons: no_data_for_date (no exit_attribution records for that date on droplet),
phase0_fail, forensic_fail, surgical_fail, replay_fail. See docs/BACKFILL_DATA_REQUIREMENTS.md.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXPERIMENTS = REPO / "reports" / "experiments"
AUDIT = REPO / "reports" / "audit"


def _last_n_trading_days(anchor_date: str, n: int) -> list[str]:
    """Return up to N US trading days (weekdays) ending on anchor_date, newest first."""
    try:
        anchor = datetime.strptime(anchor_date, "%Y-%m-%d")
    except ValueError:
        return []
    out = []
    d = anchor
    while len(out) < n and d.year >= 2020:
        if d.weekday() < 5:
            out.append(d.strftime("%Y-%m-%d"))
        d -= timedelta(days=1)
    return out


def _has_data_for_date(base: Path, date_str: str) -> bool:
    """
    Return True if there is at least one exit_attribution record for date_str.
    Forensic needs attribution (closed trades) for the date; no point running if none.
    Streams the file and returns as soon as one matching record is found.
    """
    attr_path = base / "logs" / "exit_attribution.jsonl"
    if not attr_path.exists():
        return False
    date_prefix = date_str[:10]
    with attr_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ts = (rec.get("timestamp") or rec.get("entry_timestamp") or rec.get("ts") or "")
                if str(ts)[:10] == date_prefix:
                    return True
            except json.JSONDecodeError:
                continue
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill exit-lag shadow results for last N trading days (run on droplet)")
    ap.add_argument("--days", type=int, default=5, help="Number of trading days to backfill")
    ap.add_argument("--anchor-date", default=None, help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--base-dir", default=None)
    ap.add_argument("--skip-phase0-check", action="store_true", help="Do not run phase0 before forensic (faster, less SRE)")
    args = ap.parse_args()
    base = Path(args.base_dir) if args.base_dir else REPO
    exp_dir = base / "reports" / "experiments"
    audit_dir = base / "reports" / "audit"
    anchor = args.anchor_date or datetime.utcnow().strftime("%Y-%m-%d")
    dates = _last_n_trading_days(anchor, args.days)
    if not dates:
        print("No dates to backfill.", file=sys.stderr)
        return 0

    backfilled = []
    skipped_existing = []
    failed = []

    for date_str in dates:
        result_path = exp_dir / f"EXIT_LAG_SHADOW_RESULTS_{date_str}.json"
        if result_path.exists():
            skipped_existing.append(date_str)
            continue

        if not args.skip_phase0_check:
            rc0 = subprocess.run(
                [sys.executable, "scripts/audit/run_phase0_data_integrity_droplet.py", "--date", date_str],
                cwd=base,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if rc0.returncode != 0:
                failed.append((date_str, "phase0_fail"))
                continue
            try:
                for line in (rc0.stdout or "").splitlines():
                    line = line.strip()
                    if line.startswith("{"):
                        data = json.loads(line)
                        if data.get("fail_closed"):
                            failed.append((date_str, "phase0_fail_closed"))
                            break
                        break
            except json.JSONDecodeError:
                pass

        # Skip forensic if droplet has no attribution records for this date (avoids forensic_fail)
        if not _has_data_for_date(base, date_str):
            failed.append((date_str, "no_data_for_date"))
            continue

        rc1 = subprocess.run(
            [sys.executable, "scripts/audit/run_why_we_didnt_win_forensic.py", "--date", date_str, "--fail-if-no-trace-above", "0.20"],
            cwd=base,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if rc1.returncode != 0:
            failed.append((date_str, "forensic_fail"))
            continue

        rc2 = subprocess.run(
            [sys.executable, "scripts/audit/run_intraday_shadow_exit_surgical.py", "--date", date_str],
            cwd=base,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if rc2.returncode != 0:
            failed.append((date_str, "surgical_fail"))
            continue

        rc3 = subprocess.run(
            [sys.executable, "scripts/experiments/run_exit_lag_shadow_replay.py", "--date", date_str],
            cwd=base,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if rc3.returncode != 0 or not result_path.exists():
            failed.append((date_str, "replay_fail"))
            continue

        backfilled.append(date_str)

    manifest = {
        "anchor_date": anchor,
        "days_requested": args.days,
        "backfilled": backfilled,
        "skipped_existing": skipped_existing,
        "failed": [{"date": d, "reason": r} for d, r in failed],
        "sre_note": "No live exit logic or config modified; shadow-only.",
        "csa_note": "Backfill produces evidence only; no promotion.",
        "data_requirements_doc": "docs/BACKFILL_DATA_REQUIREMENTS.md",
    }
    manifest_path = exp_dir / "EXIT_LAG_BACKFILL_MANIFEST.json"
    exp_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Backfill manifest:", json.dumps(manifest, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
