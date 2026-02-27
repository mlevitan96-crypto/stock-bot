#!/usr/bin/env python3
"""Run CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh on droplet: pull latest, or upload local script and execute. Path-agnostic."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
SCRIPT_PATH = REPO / "scripts" / "CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh"


def main() -> int:
    from droplet_client import DropletClient

    with DropletClient() as c:
        # Ensure droplet has the script (upload local copy so LF line endings and latest content)
        if SCRIPT_PATH.exists():
            remote_script = f"{c.project_dir.rstrip('/')}/scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh"
            c.put_file(SCRIPT_PATH, remote_script)
        cmd_run = (
            "REPO=$( [ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current || echo /root/stock-bot ); "
            "export REPO; echo 'REPO='$REPO; "
            "cd $REPO && git fetch origin && git pull origin main 2>/dev/null || true; "
            "chmod +x scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh 2>/dev/null || true; "
            "bash scripts/CURSOR_DASHBOARD_TRUTH_AUDIT_AND_EOD_WIRING.sh"
        )
        out, err, rc = c._execute(cmd_run, timeout=120)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc


if __name__ == "__main__":
    sys.exit(main())
