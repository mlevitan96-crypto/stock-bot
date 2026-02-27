#!/usr/bin/env python3
"""Kill old governance loop, pull latest, reset state, start new loop on droplet. MEMORY_BANK: push then deploy."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    with DropletClient() as c:
        # Kill old loop (not stock-bot)
        c._execute("pkill -f run_equity_governance_loop_on_droplet || true; pkill -f CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT || true; sleep 2; echo done", timeout=15)
        # Pull
        out, err, rc = c._execute("cd /root/stock-bot && git fetch origin && git reset --hard origin/main && ls scripts/run_equity_governance_loop_on_droplet.sh", timeout=45)
        if rc != 0:
            print("Pull failed:", out, err)
            return 1
        print("Pull OK")
        # Restart stock-bot so it runs new code (e.g. attribution_components in composite)
        c._execute("sudo systemctl restart stock-bot.service || true", timeout=15)
        print("stock-bot.service restarted")
        # Reset state (write JSON; include multi-cycle fields for loop)
        c._execute("mkdir -p /root/stock-bot/state", timeout=5)
        c._execute(
            "cd /root/stock-bot && python3 -c \"import json; open('state/equity_governance_loop_state.json','w').write(json.dumps({'last_lever':'','last_candidate_expectancy':None,'prev_candidate_expectancy':None,'last_decision':'','expectancy_history':[],'last_replay_jump_cycle':0,'tried_entry_thresholds':[],'tried_exit_strengths':[]}))\"",
            timeout=10,
        )
        # Start loop
        out2, err2, rc2 = c._execute(
            "cd /root/stock-bot && nohup bash -c 'bash scripts/run_equity_governance_loop_on_droplet.sh' </dev/null >> /tmp/equity_governance_autopilot.log 2>&1 & sleep 5 && pgrep -af run_equity_governance_loop && tail -20 /tmp/equity_governance_autopilot.log",
            timeout=20,
        )
        print((out2 or "").encode("ascii", errors="replace").decode("ascii"))
        if err2:
            print("stderr:", err2[:400])
    print("\nGovernance loop started. Log: /tmp/equity_governance_autopilot.log")
    return 0


if __name__ == "__main__":
    sys.exit(main())
