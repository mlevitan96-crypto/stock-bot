#!/usr/bin/env python3
"""
Fetch droplet dashboard debug info (no secrets).
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from droplet_client import DropletClient

    c = DropletClient()
    try:
        cmds = {
            "ps": "ps aux | grep -E 'dashboard.py|dashboard_proxy.py' | grep -v grep | head -5 || true",
            "ports": "ss -tlnp 2>/dev/null | grep -E ':5000\\b|:5001\\b|:5002\\b|:5003\\b' || netstat -tlnp 2>/dev/null | grep -E ':5000\\b|:5001\\b|:5002\\b|:5003\\b' || true",
            "log_tail": "cd /root/stock-bot && (test -f logs/dashboard.log && tail -50 logs/dashboard.log) || echo 'no logs/dashboard.log' ",
        }
        for name, cmd in cmds.items():
            out, err, code = c._execute(f"bash -lc '{cmd}'", timeout=30)
            print("=" * 80)
            print(name)
            print("=" * 80)
            print((out or err or "").strip())
        return 0
    finally:
        c.close()


if __name__ == "__main__":
    raise SystemExit(main())

