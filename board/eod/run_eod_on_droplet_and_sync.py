#!/usr/bin/env python3
"""
Full EOD on droplet with real data, then sync to GitHub.
1. On droplet: detect repo root, git pull, run EOD confirmation (verify → re-run if needed → push).
2. Uses CLAWDBOT_SESSION_ID=stock_quant_eod_<date> for the run.
Run from repo root. Requires droplet_config.json / DROPLET_* env and GitHub push access from droplet.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    # Same repo detection as run_cron_for_date_on_droplet / deploy_sync_cron.
    # EOD confirmation: verify today's EOD, re-run full pipeline if missing/invalid, then push.
    cmd = (
        "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
        "cd $REPO && git fetch origin && git pull --rebase --autostash origin main && "
        "export CLAWDBOT_SESSION_ID=stock_quant_eod_$(date -u +%Y-%m-%d) && "
        "python3 board/eod/eod_confirmation.py"
    )

    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=600)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc


if __name__ == "__main__":
    sys.exit(main())
