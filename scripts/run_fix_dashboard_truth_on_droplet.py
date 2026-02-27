#!/usr/bin/env python3
"""Run CURSOR_FIX_DASHBOARD_TRUTH_AND_VERIFY.sh on droplet: upload script, then execute. Droplet only."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
SCRIPT_PATH = REPO / "scripts" / "CURSOR_FIX_DASHBOARD_TRUTH_AND_VERIFY.sh"


def main() -> int:
    from droplet_client import DropletClient

    with DropletClient() as c:
        if SCRIPT_PATH.exists():
            remote_script = f"{c.project_dir.rstrip('/')}/scripts/CURSOR_FIX_DASHBOARD_TRUTH_AND_VERIFY.sh"
            c.put_file(SCRIPT_PATH, remote_script)
        cmd_run = (
            "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
            "export REPO; cd $REPO && chmod +x scripts/CURSOR_FIX_DASHBOARD_TRUTH_AND_VERIFY.sh && "
            "bash scripts/CURSOR_FIX_DASHBOARD_TRUTH_AND_VERIFY.sh"
        )
        out, err, rc = c._execute(cmd_run, timeout=180)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc


if __name__ == "__main__":
    sys.exit(main())
