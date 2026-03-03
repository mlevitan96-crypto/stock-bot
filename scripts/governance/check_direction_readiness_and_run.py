#!/usr/bin/env python3
"""
Check direction readiness (100 telemetry-backed trades, 90%+ telemetry).
If ready just flipped TRUE, run direction replay 30d on droplet and persist replay status.
Idempotent: safe to run repeatedly (e.g. on each exit event or cron 15–30 min).

Scheduling (choose one or both):
- Cron during market hours: */15 * * * 1-5 (every 15 min) or */30 * * * 1-5 (every 30 min).
  Example: 0,30 9-16 * * 1-5 cd /root/stock-bot && python3 scripts/governance/check_direction_readiness_and_run.py
- On exit: call this script after append_exit_attribution (e.g. from a small hook or cron every minute).
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.governance.direction_readiness import (
    load_direction_readiness_state,
    update_and_persist_direction_readiness,
)


def main() -> int:
    base = REPO
    prev = load_direction_readiness_state(base)
    state = update_and_persist_direction_readiness(base)

    if not state.get("ready"):
        # Counts updated; no replay to run
        return 0

    # Ready is True. Run replay only if it just flipped (first time we're ready)
    if prev.get("ready"):
        # Already ran replay in a prior invocation
        return 0

    # Just flipped to ready: run replay on droplet and write status
    status_path = base / "state" / "direction_replay_status.json"
    status_dir = status_path.parent
    status_dir.mkdir(parents=True, exist_ok=True)
    now_iso = datetime.now(timezone.utc).isoformat()

    def write_status(status: str, reason: str = "") -> None:
        payload = {
            "last_run_ts": now_iso,
            "status": status,
            "reason": reason or None,
        }
        status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    write_status("RUNNING", "100 telemetry-backed trades reached; replay triggered")
    cmd = [sys.executable, str(REPO / "scripts" / "replay" / "run_direction_replay_30d_on_droplet.py")]
    try:
        result = subprocess.run(cmd, cwd=str(REPO), timeout=600, capture_output=True, text=True)
        if result.returncode == 0:
            write_status("SUCCESS", "Replay completed; artifacts fetched")
            return 0
        # Check for BLOCKED (synthetic > 10%)
        blocked_md = REPO / "reports" / "board" / "DIRECTION_REPLAY_BLOCKED_SYNTHETIC.md"
        if blocked_md.exists():
            write_status("BLOCKED", "Insufficient telemetry coverage (synthetic > 10%)")
            return 0  # Script exits 1 for blocked; we record and exit 0 so cron doesn't alert
        write_status("FAILED", result.stderr or f"Exit code {result.returncode}")
        return result.returncode
    except subprocess.TimeoutExpired:
        write_status("FAILED", "Replay timed out (600s)")
        return 1
    except Exception as e:
        write_status("FAILED", str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
