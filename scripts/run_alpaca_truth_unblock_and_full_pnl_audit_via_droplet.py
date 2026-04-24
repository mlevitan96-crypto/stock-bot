#!/usr/bin/env python3
"""Upload consolidated mission and run on Alpaca droplet."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    local = REPO / "scripts" / "alpaca_truth_unblock_and_full_pnl_audit_mission.py"
    if not local.is_file():
        print("Missing", local, file=sys.stderr)
        return 1

    with DropletClient() as c:
        proj = c.project_dir.replace("~", "/root").rstrip("/")
        forced = os.environ.get("DROPLET_TRADING_ROOT", "").strip()
        if forced:
            remote_root = forced.rstrip("/")
        else:
            chk, _, _ = c._execute("test -d /root/trading-bot-current && echo yes || echo no", timeout=10)
            remote_root = "/root/trading-bot-current" if (chk or "").strip() == "yes" else proj
        remote = f"{remote_root}/scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py"
        c._execute(f"mkdir -p {remote_root}/scripts", timeout=10)
        c.put_file(str(local), remote)
        siglog = REPO / "telemetry" / "signal_context_logger.py"
        if siglog.is_file():
            c._execute(f"mkdir -p {remote_root}/telemetry", timeout=10)
            c.put_file(str(siglog), f"{remote_root}/telemetry/signal_context_logger.py")
        print("Uploaded to", remote)
        cmd = (
            f"cd {remote_root} && "
            "[ -f .env ] && set -a && source .env && set +a; "
            "python3 scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py --days 180 --max-compute"
        )
        out, err, rc = c._execute(cmd, timeout=3600)
        print(out or "")
        if err:
            print("stderr:", err[:3000])
        print("exit:", rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
