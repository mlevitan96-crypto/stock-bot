#!/usr/bin/env python3
"""
Install/enable uw-flow-daemon systemd service on droplet.

NOTE: Intended to be run on the droplet as root.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


UNIT_SRC = Path("deploy/systemd/uw-flow-daemon.service")
UNIT_DST = Path("/etc/systemd/system/uw-flow-daemon.service")


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    if os.name != "posix":
        raise SystemExit("This installer must be run on the droplet (Linux).")
    if os.geteuid() != 0:
        raise SystemExit("This installer must be run as root.")
    if not UNIT_SRC.exists():
        raise SystemExit(f"Missing unit file in repo: {UNIT_SRC}")

    UNIT_DST.write_text(UNIT_SRC.read_text(encoding="utf-8"), encoding="utf-8")
    _run(["systemctl", "daemon-reload"])
    _run(["systemctl", "enable", "--now", "uw-flow-daemon.service"])
    _run(["systemctl", "restart", "uw-flow-daemon.service"])
    _run(["systemctl", "is-active", "uw-flow-daemon.service"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

