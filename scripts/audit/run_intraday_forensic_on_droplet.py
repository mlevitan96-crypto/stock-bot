#!/usr/bin/env python3
"""
Run full one-day intraday forensic ON DROPLET, then fetch all artifacts to local.
Uses droplet logs/state/reports/state for accurate Phase 0 and trade data.
Execute from repo root. Requires: droplet_client, paramiko.
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
    ap = argparse.ArgumentParser(description="Run intraday forensic on droplet and fetch artifacts")
    ap.add_argument("--date", default="2026-03-09", help="YYYY-MM-DD")
    ap.add_argument("--skip-promotion", action="store_true", help="Skip promotion/exit capture (use existing TRADE_SHAPE_TABLE)")
    args = ap.parse_args()
    date_str = args.date

    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"DropletClient not available: {e}", file=sys.stderr)
        return 1

    client = DropletClient()

    # 0) Pull latest so droplet has forensic scripts
    out_pull, err_pull, rc_pull = client._execute_with_cd("git pull origin main", timeout=30)
    print("git pull:", out_pull or err_pull or "ok")

    # 1) Ensure TRADE_SHAPE_TABLE exists (promotion + exit capture review)
    if not args.skip_promotion:
        cmd1 = f"DROPLET_RUN=1 python3 scripts/audit/run_promotion_and_exit_capture_review.py"
        out1, err1, rc1 = client._execute_with_cd(cmd1, timeout=300)
        print(out1 or "")
        if err1:
            print(err1, file=sys.stderr)
        if rc1 != 0:
            print("Promotion/exit capture exited", rc1, file=sys.stderr)

    # 2) Phase 0 data integrity
    cmd0 = f"python3 scripts/audit/run_phase0_data_integrity_droplet.py --date {date_str}"
    out0, err0, rc0 = client._execute_with_cd(cmd0, timeout=60)
    print("--- Phase 0 ---")
    print(out0 or "")
    if err0:
        print(err0, file=sys.stderr)
    phase0_result = {}
    try:
        for line in (out0 or "").splitlines():
            if line.strip().startswith("{"):
                phase0_result = json.loads(line.strip())
                break
    except json.JSONDecodeError:
        pass
    phase0_path = AUDIT / f"INTRADAY_PHASE0_DATA_INTEGRITY_{date_str}.json"
    phase0_path.parent.mkdir(parents=True, exist_ok=True)
    phase0_path.write_text(json.dumps(phase0_result, indent=2), encoding="utf-8")
    print("Wrote", phase0_path)

    # 3) Intraday forensic (uses TRADE_SHAPE_TABLE + logs/state on droplet)
    cmd2 = f"python3 scripts/audit/run_intraday_forensic_review.py --date {date_str}"
    out2, err2, rc2 = client._execute_with_cd(cmd2, timeout=120)
    print("--- Intraday forensic ---")
    print(out2 or "")
    if err2:
        print(err2, file=sys.stderr)

    # 4) Fetch artifacts
    artifacts = [
        (AUDIT, f"INTRADAY_PROFITABILITY_FORENSIC_{date_str}.md"),
        (AUDIT, f"INTRADAY_EXIT_WINDOW_ANALYSIS_{date_str}.json"),
        (AUDIT, f"INTRADAY_BLOCKED_AND_COUNTER_INTEL_{date_str}.md"),
        (BOARD, f"INTRADAY_BOARD_VERDICT_{date_str}.md"),
    ]
    remote_dir = "reports/audit"
    for dir_path, name in artifacts:
        remote = f"{remote_dir}/{name}" if dir_path == AUDIT else f"reports/board/{name}"
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

    return rc0 if phase0_result.get("fail_closed") else rc2


if __name__ == "__main__":
    sys.exit(main())
