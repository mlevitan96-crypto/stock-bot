#!/usr/bin/env python3
"""Run diagnose_cron_and_git on droplet: pull latest, then execute. Path-agnostic."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

def main() -> int:
    from droplet_client import DropletClient

    # Detect repo path, pull latest, run diagnostic
    cmd = (
        "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
        "echo 'REPO='$REPO; "
        "cd $REPO && git fetch origin && git pull origin main && "
        "python3 scripts/diagnose_cron_and_git.py"
    )
    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=180)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc

if __name__ == "__main__":
    sys.exit(main())
