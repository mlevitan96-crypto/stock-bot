#!/usr/bin/env python3
"""
Backup trigger for CSA every-100-trades.

Primary trigger: trading engine (main.py) via record_trade_event().
Backup trigger: this script. Run periodically on the droplet (e.g. cron every 5 min).
Backup only fires when primary missed updating state (e.g. process died after incrementing to 100
but before/during CSA run). Reconciles total_trade_events from trade_events.jsonl, then
if at a 100-event milestone with no CSA run recorded, runs the same CSA wrapper and updates state.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.infra.csa_trade_state import (
    load_state,
    save_state,
    should_run_csa_every_100,
    reconcile_state_from_log,
)


def main() -> int:
    # Reconcile: if event log has more events than state (e.g. after restart), update state
    state = reconcile_state_from_log()
    if not should_run_csa_every_100(state):
        return 0
    total = state["total_trade_events"]
    mission_id = "CSA_TRADE_100_" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    # Claim milestone so we don't double-run
    state["last_csa_trade_count"] = total
    state["last_csa_mission_id"] = mission_id
    save_state(state)
    script = REPO / "scripts" / "run_csa_every_100_trades.py"
    if not script.exists():
        return 0
    rc = subprocess.call(
        [os.environ.get("PYTHON", sys.executable), str(script), "--mission-id", mission_id, "--trade-count", str(total)],
        cwd=str(REPO),
    )
    return rc


if __name__ == "__main__":
    sys.exit(main())
