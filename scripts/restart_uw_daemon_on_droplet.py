#!/usr/bin/env python3
"""Restart UW flow daemon on droplet and verify it is active. Use when dashboard shows 'UW Daemon not running'."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; run from repo root", file=sys.stderr)
        return 1

    with DropletClient() as c:
        proj = c.project_dir if hasattr(c, "project_dir") else "/root/stock-bot"
        # Ensure unit is installed (deploy copies it)
        c._execute(
            f"if [ -f {proj}/deploy/systemd/uw-flow-daemon.service ]; then "
            f"sudo cp {proj}/deploy/systemd/uw-flow-daemon.service /etc/systemd/system/uw-flow-daemon.service && sudo systemctl daemon-reload; fi",
            timeout=10,
        )
        out, err, rc = c._execute("sudo systemctl restart uw-flow-daemon.service", timeout=15)
        print("Restart:", out or "(ok)")
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("Restart failed", file=sys.stderr)
            return 1
        out2, _, _ = c._execute("systemctl is-active uw-flow-daemon.service", timeout=5)
        active = (out2 or "").strip() == "active"
        print("uw-flow-daemon.service:", out2.strip() if out2 else "unknown")
        return 0 if active else 1


if __name__ == "__main__":
    sys.exit(main())
