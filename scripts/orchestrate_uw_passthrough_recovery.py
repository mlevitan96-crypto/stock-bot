#!/usr/bin/env python3
"""
Orchestrate UW passthrough recovery: set .env on droplet, deploy, restart daemon, verify.
Run from repo root. Requires droplet_config.json and droplet connectivity.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found", file=sys.stderr)
    sys.exit(1)


def get_root(c: DropletClient) -> str:
    out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (out or "/root/stock-bot").strip().splitlines()[-1].strip()


def _env_cmd() -> str:
    return (
        "touch .env && (grep -q '^UW_MISSING_INPUT_MODE=' .env && "
        "sed -i 's/^UW_MISSING_INPUT_MODE=.*/UW_MISSING_INPUT_MODE=passthrough/' .env || "
        "echo 'UW_MISSING_INPUT_MODE=passthrough' >> .env); "
        "echo '--- .env UW_MISSING_INPUT_MODE ---'; grep 'UW_MISSING_INPUT_MODE' .env || true"
    )


def phase2_set_env(client: DropletClient) -> bool:
    """Set UW_MISSING_INPUT_MODE=passthrough in droplet .env (project_dir and get_root so live process and trace see it)."""
    # project_dir: where stock-bot service runs
    out1, err1, rc1 = client._execute_with_cd(_env_cmd(), timeout=15)
    print(out1 or "")
    if err1:
        print(err1, file=sys.stderr)
    root = get_root(client)
    # get_root: where trace script runs (may differ if symlink/current)
    out2, _, rc2 = client._execute(f"cd {root} && {_env_cmd()}", timeout=15)
    if out2 and out2 != (out1 or ""):
        print(out2)
    return rc1 == 0 or rc2 == 0


def phase3_deploy(client: DropletClient) -> dict:
    """Deploy latest code: fetch + reset --hard origin/main, then full deploy."""
    root = get_root(client)
    # Ensure exact origin/main (as specified)
    fetch_reset = client._execute_with_cd(
        "git fetch origin main && git reset --hard origin/main",
        timeout=30,
    )
    stdout, stderr, rc = fetch_reset
    if rc != 0:
        print("git fetch/reset failed:", stdout, stderr, file=sys.stderr)
        return {"success": False, "error": "git fetch/reset failed"}
    print("git fetch + reset --hard origin/main: OK")
    return client.deploy()


def phase4_restart_daemon(client: DropletClient) -> bool:
    """Restart live/paper daemon so it picks up new code and .env."""
    # stock-bot runs deploy_supervisor + main.py; uw-flow-daemon keeps cache fresh
    out1, _, rc1 = client._execute("sudo systemctl restart stock-bot", timeout=30)
    out2, _, rc2 = client._execute(
        "sudo systemctl start uw-flow-daemon.service 2>/dev/null; sudo systemctl restart uw-flow-daemon.service",
        timeout=30,
    )
    print("stock-bot restart:", "OK" if rc1 == 0 else out1)
    print("uw-flow-daemon restart: OK")
    return rc1 == 0


def phase5_verify(client: DropletClient) -> tuple[bool, str]:
    """Run trace and check run.jsonl / blocked_trades. Return (success, summary)."""
    root = get_root(client)
    # Upload and run trace script
    sftp = client._connect().open_sftp()
    try:
        local_script = REPO / "scripts" / "live_trading_trace_on_droplet.py"
        sftp.put(str(local_script), f"{root}/scripts/live_trading_trace_on_droplet.py")
    finally:
        sftp.close()
    out, err, rc = client._execute(
        f"cd {root} && python3 scripts/live_trading_trace_on_droplet.py 2>&1",
        timeout=30,
    )
    print(out or "")
    if err:
        print(err, file=sys.stderr)
    if rc != 0:
        return False, "Trace script failed"

    # Check run.jsonl last line
    run_out, _, _ = client._execute(f"tail -1 {root}/logs/run.jsonl 2>/dev/null || echo '{{}}'", timeout=5)
    # Check blocked_trades last lines
    block_out, _, _ = client._execute(
        f"tail -3 {root}/state/blocked_trades.jsonl 2>/dev/null || echo ''",
        timeout=5,
    )
    summary = f"run.jsonl last: {run_out.strip()}\nblocked_trades (last 3):\n{block_out}"
    return True, summary


def main() -> int:
    print("=" * 60)
    print("UW PASSTHROUGH RECOVERY ORCHESTRATOR")
    print("=" * 60)
    with DropletClient() as client:
        # Phase 2
        print("\n--- Phase 2: Set .env UW_MISSING_INPUT_MODE=passthrough ---")
        if not phase2_set_env(client):
            print("Phase 2 failed", file=sys.stderr)
            return 1
        # Phase 3
        print("\n--- Phase 3: Deploy latest code ---")
        deploy_result = phase3_deploy(client)
        if not deploy_result.get("success"):
            print("Phase 3 failed", deploy_result, file=sys.stderr)
            return 1
        # Phase 4
        print("\n--- Phase 4: Restart live/paper daemon ---")
        if not phase4_restart_daemon(client):
            print("Phase 4 warning (check stock-bot status)", file=sys.stderr)
        # Phase 5
        print("\n--- Phase 5: Verify trace and logs ---")
        ok, summary = phase5_verify(client)
        print(summary)
        if not ok:
            return 1
    print("\nOrchestration complete. See Phase 5 output and run.jsonl/blocked_trades after one full cycle.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
