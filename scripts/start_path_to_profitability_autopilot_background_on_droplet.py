#!/usr/bin/env python3
"""
Start the full PATH_TO_PROFITABILITY autopilot on the droplet in the background.
Uses nohup so it keeps running after SSH disconnects. Log: /tmp/path_to_profitability_autopilot.log
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    log_path = "/tmp/path_to_profitability_autopilot.log"
    # Start autopilot in background; nohup so it survives SSH disconnect
    cmd = (
        f"cd /root/stock-bot && "
        f"nohup bash -c 'STOP_AFTER_APPLY=0 bash scripts/CURSOR_DROPLET_PATH_TO_PROFITABILITY_AUTOPILOT.sh' "
        f"</dev/null >> {log_path} 2>&1 & "
        f"sleep 4 && "
        f"echo '--- Autopilot background start ---' && "
        f"(pgrep -af PATH_TO_PROFITABILITY_AUTOPILOT || echo 'No matching process') && "
        f"echo '--- Last 25 lines of log ---' && "
        f"tail -25 {log_path} 2>/dev/null || echo '(log empty or missing)'"
    )

    with DropletClient() as c:
        print("Starting PATH_TO_PROFITABILITY autopilot in background (nohup)...")
        out, err, rc = c._execute(cmd, timeout=30)
        print(out or "")
        if err:
            print("stderr:", err[:1500])
        if rc != 0:
            print("Warning: command returned", rc, file=sys.stderr)
        print("\nDone. Autopilot runs until 50 trades then compare. Log:", log_path)
        print("To watch: ssh droplet 'tail -f", log_path + "'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
