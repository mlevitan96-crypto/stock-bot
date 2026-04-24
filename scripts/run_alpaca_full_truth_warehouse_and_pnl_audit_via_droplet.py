#!/usr/bin/env python3
"""Upload mission script and run on Alpaca droplet (SSH). Targets DROPLET_TRADING_ROOT or /root/trading-bot-current if present."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    local = REPO / "scripts" / "alpaca_full_truth_warehouse_and_pnl_audit_mission.py"
    if not local.is_file():
        print("Missing", local, file=sys.stderr)
        return 1

    with DropletClient() as c:
        proj = c.project_dir.replace("~", "/root").rstrip("/")
        # Prefer explicit Alpaca deploy root when it exists on host.
        forced = os.environ.get("DROPLET_TRADING_ROOT", "").strip()
        if forced:
            remote_root = forced.rstrip("/")
        else:
            chk, _, _ = c._execute("test -d /root/trading-bot-current && echo yes || echo no", timeout=10)
            remote_root = "/root/trading-bot-current" if (chk or "").strip() == "yes" else proj
        remote_script = f"{remote_root}/scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py"
        c._execute(f"mkdir -p {remote_root}/scripts", timeout=10)
        c.put_file(str(local), remote_script)
        print("Uploaded mission to", remote_script)
        cmd = (
            f"cd {remote_root} && "
            "[ -f .env ] && set -a && source .env && set +a; "
            "python3 scripts/alpaca_full_truth_warehouse_and_pnl_audit_mission.py --days 180 --max-compute"
        )
        out, err, rc = c._execute(cmd, timeout=3600)
        print(out or "(no stdout)")
        if err:
            print("stderr:", err[:4000])
        print("exit:", rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
