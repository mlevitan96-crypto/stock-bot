#!/usr/bin/env python3
"""
Run Alpaca DATA_READY pipeline ON THE DROPLET via SSH.
Sources /root/.alpaca_env so TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are set (see MEMORY_BANK_ALPACA.md).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    client = DropletClient()
    # Ensure droplet matches GitHub (avoid merge conflicts from local untracked/divergent files)
    rp = client.execute_command("git fetch origin main && git reset --hard origin/main", timeout=30)
    if rp.get("exit_code", 1) != 0:
        print("Git fetch/reset failed:", rp.get("stderr", ""), rp.get("stdout", ""), file=sys.stderr)
        return 1
    print("Droplet: synced to origin/main")

    # Per MEMORY_BANK: Telegram vars on droplet are in /root/.alpaca_env; source before running
    env_prefix = "source /root/.alpaca_env 2>/dev/null; "
    cmd = env_prefix + "export PYTHONPATH=" + client.project_dir + " && python3 scripts/run_alpaca_data_ready_on_droplet.py"
    r = client.execute_command(cmd, timeout=300)
    print(r.get("stdout") or "")
    if r.get("stderr"):
        print("stderr:", r["stderr"], file=sys.stderr)
    return r.get("exit_code", 1)


if __name__ == "__main__":
    sys.exit(main())
