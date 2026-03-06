#!/usr/bin/env python3
"""
Reset CSA trade count to market open today and refresh the profitability cockpit.
Use after deploy or when the 100-trade CSA window should start fresh from today.
Safe to run locally or on the droplet; uses production state path (reports/state/TRADE_CSA_STATE.json).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# Use production state (default); do not use test_csa_100
os.environ.pop("TRADE_CSA_STATE_DIR", None)

from src.infra.csa_trade_state import reset_state_for_today, STATE_FILE, EVENT_LOG


def main() -> int:
    state = reset_state_for_today()
    print("CSA trade state reset for today (market open).")
    print(f"  State file: {STATE_FILE}")
    print(f"  total_trade_events: {state['total_trade_events']}, last_csa_trade_count: {state['last_csa_trade_count']}")
    print(f"  Event log cleared: {not EVENT_LOG.exists()}")
    print()

    # Refresh profitability cockpit
    cockpit_script = REPO / "scripts" / "update_profitability_cockpit.py"
    if cockpit_script.exists():
        rc = subprocess.call([sys.executable, str(cockpit_script)], cwd=str(REPO))
        if rc != 0:
            print("Warning: cockpit update returned", rc, file=sys.stderr)
    else:
        print("Note: update_profitability_cockpit.py not found; dashboard not refreshed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
