#!/usr/bin/env python3
"""
Run intel producers on droplet via DropletClient (droplet_config.json).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/root/stock-bot"


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    client = DropletClient()
    try:
        ssh = client._connect()
    except Exception as e:
        print(f"[FAIL] Cannot connect: {e}", file=sys.stderr)
        return 1

    cmd = f"cd {REMOTE_ROOT} && git pull origin main && REPO_DIR={REMOTE_ROOT} bash scripts/run_intel_producers_on_droplet.sh"
    print(f"[RUN] {cmd}")
    out, err, rc = client._execute(cmd, timeout=120)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    client.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
