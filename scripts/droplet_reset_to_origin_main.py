#!/usr/bin/env python3
"""
Force droplet repo to match origin/main (tracked files only).

Why:
- Deployment can fail if the droplet has local edits to tracked files.
Contract:
- This is operational only; it does not modify trading logic.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    # Ensure repo root import path
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from droplet_client import DropletClient

    client = DropletClient()
    try:
        cmd = "cd /root/stock-bot && git fetch origin main && git reset --hard origin/main"
        out, err, code = client._execute(f"bash -lc \"{cmd}\"", timeout=180)
        if code != 0:
            raise SystemExit(f"Reset failed: {(err or out)[:300]}")
        print("[OK] Droplet repo reset to origin/main.")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())

