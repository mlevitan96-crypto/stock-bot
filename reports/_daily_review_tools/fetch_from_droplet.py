#!/usr/bin/env python3
"""
Fetch a file from the droplet via base64 over SSH.

Usage:
  python reports/_daily_review_tools/fetch_from_droplet.py --remote /root/stock-bot/reports/X.md --local reports/X.md
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from droplet_client import DropletClient


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--remote", required=True, help="Absolute droplet path")
    ap.add_argument("--local", required=True, help="Local repo-relative path")
    args = ap.parse_args()

    remote_path = args.remote
    local_path = Path(args.local)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = (
        "/root/stock-bot/venv/bin/python -c "
        "\"import base64; "
        f"print(base64.b64encode(open('{remote_path}','rb').read()).decode('ascii'))\""
    )

    with DropletClient() as c:
        r = c.execute_command(cmd, timeout=60)
        if not r.get("success"):
            err = (r.get("stderr") or r.get("stdout") or "").strip()
            raise SystemExit(f"Fetch failed: {err}")
        b64 = (r.get("stdout") or "").strip()
        data = base64.b64decode(b64.encode("ascii"))
        local_path.write_bytes(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

