#!/usr/bin/env python3
"""Run full cron flow on droplet for a specific date. Pulls latest, runs stockbot reports,
audit, board packager, then commits and pushes."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (e.g. 2026-02-06)")
    args = ap.parse_args()
    date = args.date

    from droplet_client import DropletClient

    cmd = (
        "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
        "cd $REPO && git fetch origin && git pull origin main && "
        f"export DATE={date} && "
        "export REPO_DIR=$REPO && "
        "mkdir -p reports/droplet_audit/$DATE && "
        "python3 scripts/run_stockbot_daily_reports.py --date $DATE --base-dir $REPO_DIR || true && "
        "python3 scripts/audit_stock_bot_readiness.py --date $DATE --verbose 2>&1 | tee reports/droplet_audit/$DATE/audit_summary.txt; "
        "AUDIT_EXIT=${PIPESTATUS[0]}; "
        'if [ $AUDIT_EXIT -eq 0 ]; then STATUS="pass"; else STATUS="fail"; fi; '
        "echo '{\"date\":\"'$DATE'\",\"exit_code\":'$AUDIT_EXIT',\"status\":\"'$STATUS'\"}' > reports/droplet_audit/$DATE/audit_result.json && "
        "python3 scripts/board_daily_packager.py --date $DATE && "
        "git add board/eod/out/*.md board/eod/out/*.json board/eod/out/$DATE/ 2>/dev/null || true && "
        "git add reports/stockbot/$DATE/ 2>/dev/null || true && "
        "git add reports/droplet_audit/ || true && "
        "git status --short && "
        "( git diff --staged --quiet || ( git commit -m \"Droplet audit + EOD sync $DATE (manual rerun)\" && git push origin main ) )"
    )

    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=300)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc


if __name__ == "__main__":
    sys.exit(main())
