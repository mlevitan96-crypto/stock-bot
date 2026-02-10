#!/usr/bin/env python3
"""
Full EOD rerun on droplet with real data, then sync report outputs to GitHub.
1. On droplet: detect repo root, git pull, run wheel daily review + EOD board, then git add/push results.
2. Use CLAWDBOT_SESSION_ID=stock_quant_eod_<date> for the run.
Run from repo root. Requires droplet_config.json / DROPLET_* env and GitHub push access from droplet.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    from droplet_client import DropletClient

    # Same repo detection as run_cron_for_date_on_droplet / deploy_sync_cron
    cmd = (
        "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
        "cd $REPO && git fetch origin && git pull --rebase origin main && "
        f"export DATE={today} && "
        "export CLAWDBOT_SESSION_ID=\"stock_quant_eod_$DATE\" && "
        "python3 scripts/generate_wheel_daily_review.py --date $DATE 2>/dev/null || true && "
        "python3 scripts/run_multi_day_analysis.py --date $DATE 2>/dev/null || true && "
        "python3 board/eod/run_stock_quant_officer_eod.py && "
        "EOD_RC=$?; "
        "git add board/eod/out/$DATE/ 2>/dev/null || true && "
        "git add board/eod/out/*.json board/eod/out/*.md 2>/dev/null || true && "
        "git add reports/wheel_actions_$DATE.json reports/wheel_watchlists_$DATE.json 2>/dev/null || true && "
        "git add reports/wheel_governance_badge_$DATE.json reports/wheel_daily_review_$DATE.md 2>/dev/null || true && "
        "git status --short && "
        "( git diff --staged --quiet && echo 'No report changes to push' || "
        "( git commit -m \"EOD report $DATE (droplet rerun)\" && git push origin main ) ); "
        "exit $EOD_RC"
    )

    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=400)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc


if __name__ == "__main__":
    sys.exit(main())
