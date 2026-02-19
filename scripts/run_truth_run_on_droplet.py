#!/usr/bin/env python3
"""
Run the Droplet Truth Run (run_droplet_truth_run.py) on the droplet via SSH.
Uses DropletClient; prints full console output. Exit code = script exit code from droplet.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    from droplet_client import DropletClient

    root = "/root/stock-bot"
    # Fetch and reset to origin/main so truth run scripts exist (droplet may have unstaged changes)
    cmd = (
        f"cd {root} && "
        "git fetch origin && git reset --hard origin/main && "
        "[ -f .env ] && set -a && source .env && set +a; "
        "python3 scripts/run_droplet_truth_run.py"
    )
    with DropletClient() as c:
        out, err, rc = c._execute(cmd, timeout=600)
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        return rc


if __name__ == "__main__":
    sys.exit(main())
