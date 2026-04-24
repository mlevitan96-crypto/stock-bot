#!/usr/bin/env python3
"""Run direction replay pipeline on droplet via SSH and update direction_replay_status.json."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient

def main() -> int:
    end_date = (datetime.now(timezone.utc).date() - timedelta(days=1)).strftime("%Y-%m-%d")
    base = "/root/stock-bot"
    now_iso = datetime.now(timezone.utc).isoformat()

    def run(cmd: str, timeout: int = 300):
        return client.execute_command(f"cd {base} && {cmd}", timeout=timeout)

    with DropletClient() as client:
        status_path = f"{base}/state/direction_replay_status.json"
        # Write RUNNING
        run(f"python3 -c \"import json; open('state/direction_replay_status.json','w').write(json.dumps({{'last_run_ts':'{now_iso}','status':'RUNNING','reason':None}}))\"")

        steps = [
            ("load_30d_backtest_cohort", f"python3 scripts/replay/load_30d_backtest_cohort.py --base-dir {base} --end-date {end_date} --days 30"),
            ("reconstruct_direction_30d", f"python3 scripts/replay/reconstruct_direction_30d.py --base-dir {base} --end-date {end_date} --days 30"),
            ("run_direction_replay_30d", f"DROPLET_RUN=1 python3 scripts/replay/run_direction_replay_30d.py --base-dir {base} --end-date {end_date} --days 30 --droplet-run --deployed-commit cron"),
        ]
        for name, cmd in steps:
            r = run(cmd)
            ec = r.get("exit_code", 1)
            stdout = (r.get("stdout") or "")[-800:]
            stderr = (r.get("stderr") or "")[-500:]
            print(f"--- {name} exit {ec} ---")
            print(stdout)
            if stderr:
                print("stderr:", stderr)
            if ec != 0:
                reason = (stderr.strip() or stdout.strip() or f"Exit code {ec}").replace('\"', "'")[:500]
                run(f"python3 -c \"import json; open('state/direction_replay_status.json','w').write(json.dumps({{'last_run_ts':'{now_iso}','status':'FAILED','reason':'{reason}'}}))\"")
                return 1

        # SUCCESS
        run(f"python3 -c \"import json; open('state/direction_replay_status.json','w').write(json.dumps({{'last_run_ts':'{now_iso}','status':'SUCCESS','reason':'Replay pipeline completed.'}}))\"")
        print("Replay pipeline completed. Status set to SUCCESS.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
