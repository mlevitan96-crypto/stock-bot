#!/usr/bin/env python3
"""Upload connectivity + mission + uw_flow_daemon patches; run connectivity mission on droplet."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FILES = [
    "scripts/alpaca_uw_execution_connectivity_mission.py",
    "scripts/alpaca_truth_unblock_and_full_pnl_audit_mission.py",
    "uw_flow_daemon.py",
    "telemetry/signal_context_logger.py",
    "deploy/systemd/uw-flow-daemon.service",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    with DropletClient() as c:
        proj = c.project_dir.replace("~", "/root").rstrip("/")
        forced = os.environ.get("DROPLET_TRADING_ROOT", "").strip()
        remote_root = forced.rstrip("/") if forced else proj
        for rel in FILES:
            lp = REPO / rel
            if not lp.is_file():
                print("skip missing", rel, file=sys.stderr)
                continue
            rr = f"{remote_root}/{rel}".replace("\\", "/")
            c._execute(f"mkdir -p '{remote_root}/{'/'.join(rel.split('/')[:-1])}'", timeout=10)
            c.put_file(str(lp), rr)
            print("uploaded", rel)
        cmd = (
            f"cd {remote_root} && "
            f"TRADING_BOT_ROOT={remote_root} {remote_root}/venv/bin/python3 "
            f"scripts/alpaca_uw_execution_connectivity_mission.py"
        )
        out, err, rc = c._execute(cmd, timeout=7200000)
        combined = (out or "") + (err or "")
        print(combined[-120000:] if len(combined) > 120000 else combined)
        if not combined.strip():
            print("(no remote stdout/stderr — see droplet reports/ALPACA_CONNECTIVITY_AUDIT_*.md)")
        print("exit:", rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
