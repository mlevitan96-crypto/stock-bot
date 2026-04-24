#!/usr/bin/env python3
"""
Run the full weekly board audit ON the droplet (evidence is already there).
Steps: build ledger, CSA weekly review, persona memos, update cockpit.
Usage: python scripts/audit/run_weekly_board_audit_on_droplet.py [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-03-06", help="Date YYYY-MM-DD")
    args = ap.parse_args()
    date = args.date

    steps = [
        ("Build weekly trade decision ledger", f"python3 scripts/audit/build_weekly_trade_decision_ledger.py --date {date}"),
        ("Run CSA weekly review", f"python3 scripts/audit/run_csa_weekly_review.py --date {date}"),
        ("Write persona memos", f"python3 scripts/audit/write_weekly_persona_memos.py --date {date}"),
        ("Update profitability cockpit", "python3 scripts/update_profitability_cockpit.py"),
    ]

    client = DropletClient()
    for name, cmd in steps:
        print(f"Running on droplet: {name}...", flush=True)
        r = client.execute_command(cmd, timeout=120)
        ok = r.get("success", False)
        out = (r.get("stdout") or "").strip()
        err = (r.get("stderr") or "").strip()
        if out:
            print(out[:2000] + ("..." if len(out) > 2000 else ""))
        if err and not ok:
            print("stderr:", err[:1000], file=sys.stderr)
        if not ok:
            print(f"FAILED: {name} (exit_code={r.get('exit_code')})", file=sys.stderr)
            return 1
    print("Weekly board audit on droplet completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
