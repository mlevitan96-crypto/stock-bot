#!/usr/bin/env python3
"""
Run WHY WE DIDN'T WIN forensic + shadow exit surgical ON DROPLET, then fetch all artifacts locally.
1) Forensic: trace/attribution join, lag, board packet, CSA verdict.
2) Surgical: lag distribution, first-firing condition, shadow exit-on-first-eligibility PnL.
Execute from repo root. Requires: droplet_client.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
AUDIT = REPO / "reports" / "audit"
BOARD = REPO / "reports" / "board"


def main() -> int:
    ap = argparse.ArgumentParser(description="Run why-we-didnt-win forensic on droplet and fetch 6 artifacts")
    ap.add_argument("--date", default="2026-03-09", help="YYYY-MM-DD")
    ap.add_argument("--skip-surgical", action="store_true", help="Skip shadow exit surgical (only run forensic)")
    args = ap.parse_args()
    date_str = args.date

    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1

    client = DropletClient()

    out_pull, err_pull, rc_pull = client._execute_with_cd("git pull origin main", timeout=30)
    print("git pull:", out_pull or err_pull or "ok")

    cmd = f"python3 scripts/audit/run_why_we_didnt_win_forensic.py --date {date_str} --fail-if-no-trace-above 0.20"
    out, err, rc = client._execute_with_cd(cmd, timeout=300)
    print("--- Why we didn't win forensic ---")
    print(out or "")
    if err:
        print(err, file=sys.stderr)
    if rc != 0:
        print("Forensic script exited", rc, file=sys.stderr)
        blocker_path = AUDIT / f"INTRADAY_FORENSIC_BLOCKERS_{date_str}.md"
        if blocker_path.exists():
            print("Blockers file written; check", blocker_path, file=sys.stderr)
        return rc

    if not args.skip_surgical:
        cmd_surg = f"python3 scripts/audit/run_intraday_shadow_exit_surgical.py --date {date_str}"
        out_surg, err_surg, rc_surg = client._execute_with_cd(cmd_surg, timeout=60)
        print("--- Shadow exit surgical ---")
        print(out_surg or "")
        if err_surg:
            print(err_surg, file=sys.stderr)
        if rc_surg != 0:
            print("Surgical script exited", rc_surg, file=sys.stderr)

    artifacts = [
        (AUDIT, f"INTRADAY_PORTFOLIO_UNREALIZED_CURVE_{date_str}.json"),
        (AUDIT, f"INTRADAY_EXIT_LAG_AND_GIVEBACK_{date_str}.json"),
        (AUDIT, f"INTRADAY_BLOCKED_COUNTERFACTUALS_{date_str}.json"),
        (AUDIT, f"INTRADAY_JOIN_DIAGNOSTICS_{date_str}.json"),
        (AUDIT, f"INTRADAY_FORENSIC_FULL_{date_str}.md"),
        (BOARD, f"INTRADAY_BOARD_PACKET_{date_str}.md"),
        (AUDIT, f"CSA_INTRADAY_VERDICT_{date_str}.json"),
        (AUDIT, f"INTRADAY_ELIGIBILITY_EXIT_LAG_DISTRIBUTION_{date_str}.json"),
        (AUDIT, f"INTRADAY_EXIT_CONDITION_FIRST_FIRE_{date_str}.json"),
        (AUDIT, f"INTRADAY_SHADOW_EXIT_ON_FIRST_ELIGIBILITY_{date_str}.json"),
        (AUDIT, f"INTRADAY_SHADOW_EXIT_SURGICAL_SUMMARY_{date_str}.md"),
    ]
    remote_audit = "reports/audit"
    remote_board = "reports/board"
    for dir_path, name in artifacts:
        remote = f"{remote_audit}/{name}" if dir_path == AUDIT else f"{remote_board}/{name}"
        cat_out, _, _ = client._execute_with_cd(f"cat {remote} 2>/dev/null || true", timeout=15)
        if not (cat_out or "").strip():
            print("Missing on droplet:", remote, file=sys.stderr)
            continue
        dir_path.mkdir(parents=True, exist_ok=True)
        out_path = dir_path / name
        if name.endswith(".json"):
            try:
                json.loads(cat_out)
            except json.JSONDecodeError:
                cat_out = cat_out.strip()
            out_path.write_text(cat_out, encoding="utf-8")
        else:
            out_path.write_text(cat_out, encoding="utf-8")
        print("Fetched", out_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
