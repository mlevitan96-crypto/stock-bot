#!/usr/bin/env python3
"""Upload and run alpaca_runtime_visibility_probe.py on the Alpaca droplet."""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    local = REPO / "scripts" / "alpaca_runtime_visibility_probe.py"
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
        remote = f"{remote_root}/scripts/alpaca_runtime_visibility_probe.py"
        c._execute(f"mkdir -p {remote_root}/scripts {remote_root}/reports", timeout=10)
        c.put_file(str(local), remote)
        cmd = (
            f"cd {remote_root} && "
            "[ -f .env ] && set -a && source .env && set +a; "
            "PY=python3; [ -x venv/bin/python3 ] && PY=venv/bin/python3; "
            "[ -x venv/bin/python ] && PY=venv/bin/python; "
            f"TRADING_BOT_ROOT={remote_root} \"$PY\" scripts/alpaca_runtime_visibility_probe.py"
        )
        out, err, rc = c._execute(cmd, timeout=180)
        print(out or "")
        if err:
            print("stderr:", err[:2500])
        print("exit:", rc)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
