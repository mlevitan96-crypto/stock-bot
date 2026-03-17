#!/usr/bin/env python3
"""
Run Alpaca Fast-Lane multi-cycle deep review on the droplet (real data).
Pulls latest, runs alpaca_fastlane_deep_review.py, fetches report and CSV to local reports/.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pull", action="store_true", help="Skip git pull on droplet")
    ap.add_argument("--no-telegram", action="store_true", help="Pass --no-telegram to review script")
    ap.add_argument("--no-fetch", action="store_true", help="Do not fetch report/CSV back")
    args = ap.parse_args()
    c = DropletClient()
    proj = c.project_dir.replace("~", "/root")
    if not args.no_pull:
        out, err, rc = c._execute_with_cd("git fetch origin && git pull origin main", timeout=60)
        print("git pull:", (out or err or "")[:300])
    cmd = f". /root/.alpaca_env 2>/dev/null; cd {proj} && python3 scripts/alpaca_fastlane_deep_review.py"
    if args.no_telegram:
        cmd += " --no-telegram"
    out, err, rc = c._execute(cmd, timeout=120)
    print("--- deep review stdout ---")
    print(out or "")
    if err:
        print("stderr:", err[:800])
    if rc != 0:
        print("Review script exit code:", rc, file=sys.stderr)
        return rc
    if args.no_fetch:
        return 0
    out2, _, _ = c._execute_with_cd("ls -t reports/ALPACA_FASTLANE_25_BOARD_REVIEW_*.md 2>/dev/null | head -1")
    out3, _, _ = c._execute_with_cd("ls -t reports/alpaca_fastlane_25_cycle_aggregate_*.csv 2>/dev/null | head -1")
    md_path = (out2 or "").strip().split()[-1] if out2 else None
    csv_path = (out3 or "").strip().split()[-1] if out3 else None
    if md_path:
        full_md = f"{proj}/{md_path}" if not md_path.startswith("/") else md_path
        c.get_file(md_path, REPO / "reports" / Path(md_path).name)
        print("Fetched:", Path(md_path).name)
    if csv_path:
        c.get_file(csv_path, REPO / "reports" / Path(csv_path).name)
        print("Fetched:", Path(csv_path).name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
