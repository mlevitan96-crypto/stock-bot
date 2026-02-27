#!/usr/bin/env python3
"""
Phase 1: Deploy (git pull on droplet so main.py has SUBMIT_ORDER_CALLED), restart the bot,
then run order submission truth contract. Run from repo root.

Exact commands used on droplet:
  - git fetch origin && git reset --hard origin/main   (deploy)
  - systemctl restart stock-bot   (or pkill + manual start)
  - python3 scripts/order_submission_truth_contract_on_droplet.py

After deploy+restart, wait >= 30 minutes (market hours), then from local:
  python scripts/deploy_submit_proof_and_run_contract_on_droplet.py --proof-only
to capture real SUBMIT_ORDER_CALLED counts.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found; install paramiko and ensure droplet_config.json exists", file=sys.stderr)
    sys.exit(1)


def get_root(c: DropletClient) -> str:
    root_out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (root_out or "/root/stock-bot").strip().splitlines()[-1].strip()


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Deploy submit proof (main.py) + restart bot + run truth contract")
    ap.add_argument("--proof-only", action="store_true", help="Skip deploy/restart; only run truth contract and fetch")
    ap.add_argument("--no-restart", action="store_true", help="Upload main.py but do not restart bot")
    args = ap.parse_args()

    if args.proof_only:
        import subprocess
        return subprocess.run(
            [sys.executable, str(REPO / "scripts" / "run_order_submission_truth_contract_via_droplet.py")],
            cwd=str(REPO), timeout=120,
        ).returncode

    root = None
    # 1) Deploy via git pull on droplet (main.py with SUBMIT_ORDER_CALLED must be on origin/main)
    with DropletClient() as c:
        root = get_root(c)
        out, err, rc = c._execute(
            f"cd {root} && git fetch origin && git reset --hard origin/main 2>&1",
            timeout=90,
        )
        print("--- deploy (git pull on droplet) ---")
        print(out or err or "ok")
        c._execute(f"cd {root} && mkdir -p reports/order_review logs", timeout=5)

    if args.no_restart:
        print("Skipping restart (--no-restart). Run with no flags to deploy and restart.")
        return 0

    # 2) Restart the bot on droplet
    with DropletClient() as c:
        # Prefer systemd if available
        out, err, rc = c._execute("systemctl restart stock-bot 2>&1 || true", timeout=15)
        if "Active: active" in out or rc == 0:
            print("Restarted: systemctl restart stock-bot")
        else:
            # Fallback: pkill and note that user may need to start manually
            c._execute("pkill -f 'python.*main.py' 2>/dev/null || true", timeout=5)
            print("Killed main.py process (if any). Start the bot manually if it is not managed by systemd.")
        print("")
        print("Wait >= 30 minutes (market hours if applicable), then run:")
        print("  python scripts/run_order_submission_truth_contract_via_droplet.py")
        print("  or: python scripts/deploy_submit_proof_and_run_contract_on_droplet.py --proof-only")
        print("")
        print("Then confirm: logs/submit_order_called.jsonl exists and reports/order_review/submit_call_proof.md has real counts.")

    # 3) Run contract once immediately (may still be 0 until bot runs)
    time.sleep(2)
    import subprocess
    subprocess.run(
        [sys.executable, str(REPO / "scripts" / "run_order_submission_truth_contract_via_droplet.py")],
        cwd=str(REPO), timeout=90,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
