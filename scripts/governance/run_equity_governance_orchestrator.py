#!/usr/bin/env python3
"""
Multi-model governance orchestrator — coordination entry point.

ONLINE (Part A): Start equity governance autopilot on droplet (100-trade gate, stopping condition).
OFFLINE (Part B): Run equity data discovery + replay campaign locally or on droplet (proposes levers only).

Usage:
  python scripts/governance/run_equity_governance_orchestrator.py online   # start autopilot on droplet
  python scripts/governance/run_equity_governance_orchestrator.py offline  # run replay campaign
  python scripts/governance/run_equity_governance_orchestrator.py status   # check autopilot status
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _run_online(loop: bool = False) -> int:
    """Deploy and start equity governance autopilot on droplet (background). If loop=True, run until stopping condition."""
    from droplet_client import DropletClient
    log_path = "/tmp/equity_governance_autopilot.log"
    script = "scripts/run_equity_governance_loop_on_droplet.sh" if loop else "scripts/CURSOR_DROPLET_EQUITY_GOVERNANCE_AUTOPILOT.sh"
    cmd = (
        "cd /root/stock-bot && git fetch origin && git reset --hard origin/main && "
        f"[ -f {script} ] || {{ echo 'Script missing'; exit 1; }} && "
        f"nohup bash -c 'bash {script}' "
        f"</dev/null >> {log_path} 2>&1 & sleep 5 && tail -20 {log_path}"
    )
    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=90)
        print((out or "").encode("ascii", errors="replace").decode("ascii"))
        if err:
            print("stderr:", err[:800])
    print("\nONLINE autopilot started. Log:", log_path)
    return 0


def _run_offline() -> int:
    """Run equity data discovery + replay campaign (OFFLINE, no live changes)."""
    import subprocess
    # Discover data manifest
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "replay" / "discover_equity_data_manifest.py")],
        cwd=str(REPO), check=True,
    )
    # Run replay campaign
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "replay" / "run_equity_replay_campaign.py")],
        cwd=str(REPO), check=True,
    )
    print("OFFLINE replay campaign done. See reports/replay/equity_replay_campaign_*")
    return 0


def _status() -> int:
    """Check equity governance autopilot status on droplet."""
    from droplet_client import DropletClient
    with DropletClient() as c:
        out, _, _ = c._execute("tail -50 /tmp/equity_governance_autopilot.log 2>/dev/null || echo '(no log)'", timeout=15)
        print((out or "").encode("ascii", errors="replace").decode("ascii"))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: online [--loop] | offline | status")
        return 1
    mode = sys.argv[1].lower()
    loop = "--loop" in sys.argv
    if mode == "online":
        return _run_online(loop=loop)
    if mode == "offline":
        return _run_offline()
    if mode == "status":
        return _status()
    print("Unknown mode. Use: online | offline | status")
    return 1


if __name__ == "__main__":
    sys.exit(main())
