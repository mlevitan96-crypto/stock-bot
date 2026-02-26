#!/usr/bin/env python3
"""
Start the EXIT path-to-profitability autopilot on the droplet in the background.
Uses nohup so it keeps running after SSH disconnects.
Log: /tmp/path_to_profitability_exit_autopilot.log
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    log_path = "/tmp/path_to_profitability_exit_autopilot.log"
    # Pull latest so EXIT autopilot script is present, then start in background
    cmd = (
        "cd /root/stock-bot && "
        "git fetch origin && git reset --hard origin/main && "
        "[ -f scripts/CURSOR_DROPLET_PATH_TO_PROFITABILITY_EXIT_AUTOPILOT.sh ] || { echo 'ERROR: EXIT autopilot script missing'; exit 1; } && "
        f"nohup bash -c 'bash scripts/CURSOR_DROPLET_PATH_TO_PROFITABILITY_EXIT_AUTOPILOT.sh' "
        f"</dev/null >> {log_path} 2>&1 & "
        "sleep 5 && "
        "echo '--- EXIT autopilot background start ---' && "
        "(pgrep -af PATH_TO_PROFITABILITY_EXIT || pgrep -af exit_autopilot || echo 'Process check done') && "
        f"echo '--- Last 30 lines of log ---' && "
        f"tail -30 {log_path} 2>/dev/null || echo '(log empty or missing)'"
    )

    with DropletClient() as c:
        print("Deploying (git pull) and starting EXIT path-to-profitability autopilot in background (nohup)...")
        out, err, rc = c._execute(cmd, timeout=60)
        try:
            print((out or "").encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            print(out or "")
        if err and "ERROR" in err:
            print("stderr:", err[:1500])
        if rc != 0:
            print("Warning: command returned", rc, file=sys.stderr)
        print("\nDone. EXIT autopilot runs until 50 trades then compare. Log:", log_path)
        print("To watch: ssh droplet 'tail -f", log_path + "'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
