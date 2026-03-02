#!/usr/bin/env python3
"""Run live_trading_trace_on_droplet.py on the droplet and print output."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found", file=sys.stderr)
    sys.exit(1)


def get_root(c: DropletClient) -> str:
    out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (out or "/root/stock-bot").strip().splitlines()[-1].strip()


def main() -> int:
    with DropletClient() as c:
        root = get_root(c)
        sftp = c._connect().open_sftp()
        try:
            local_script = REPO / "scripts" / "live_trading_trace_on_droplet.py"
            sftp.put(str(local_script), f"{root}/scripts/live_trading_trace_on_droplet.py")
        finally:
            sftp.close()
        out, err, rc = c._execute(f"cd {root} && python3 scripts/live_trading_trace_on_droplet.py 2>&1", timeout=30)
        print(out or "")
        if err:
            print(err, file=sys.stderr)
        return rc


if __name__ == "__main__":
    sys.exit(main())
