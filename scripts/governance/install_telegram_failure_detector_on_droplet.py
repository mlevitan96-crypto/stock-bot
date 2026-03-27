#!/usr/bin/env python3
"""Copy systemd units for telegram failure detector to /etc/systemd/system and enable timer."""
from __future__ import annotations

import sys
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    units = [
        "deploy/systemd/telegram-failure-detector.service",
        "deploy/systemd/telegram-failure-detector.timer",
    ]
    remote = "/etc/systemd/system"
    with DropletClient() as c:
        for rel in units:
            local = REPO / rel
            if not local.is_file():
                print(f"Missing {local}", file=sys.stderr)
                return 1
            name = local.name
            c.put_file(str(local), f"{remote}/{name}")
        cmds = [
            "systemctl daemon-reload",
            "systemctl enable telegram-failure-detector.timer",
            "systemctl restart telegram-failure-detector.timer",
            "systemctl is-active telegram-failure-detector.timer",
            "systemctl list-timers --all | grep telegram-failure || true",
        ]
        for cmd in cmds:
            out, err, rc = c._execute(cmd, timeout=60)
            print(f"$ {cmd}\n{out}")
            if err:
                print(err, file=sys.stderr)
            if rc != 0 and "is-active" in cmd:
                print(f"warning rc={rc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
