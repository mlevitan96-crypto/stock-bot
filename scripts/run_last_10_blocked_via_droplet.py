#!/usr/bin/env python3
"""
Run the last-10-blocked-trades diagnostic ON THE DROPLET via SSH and print output here.
Run from repo root: python scripts/run_last_10_blocked_via_droplet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

try:
    from droplet_client import DropletClient
except ImportError:
    print("droplet_client not found; ensure droplet_config.json and paramiko available", file=sys.stderr)
    sys.exit(1)


def get_root(c: DropletClient) -> str:
    root_out, _, _ = c._execute(
        "([ -d /root/stock-bot-current/scripts ] && echo /root/stock-bot-current) || echo /root/stock-bot",
        timeout=10,
    )
    return (root_out or "/root/stock-bot").strip().splitlines()[-1].strip()


def main() -> int:
    with DropletClient() as c:
        root = get_root(c)
        cd = f"cd {root}"
        # Upload diagnostic script
        sftp = c._connect().open_sftp()
        try:
            local_script = REPO / "scripts" / "run_last_10_blocked_diagnostic_on_droplet.py"
            if not local_script.exists():
                print(f"Local script not found: {local_script}", file=sys.stderr)
                return 1
            sftp.put(str(local_script), f"{root}/scripts/run_last_10_blocked_diagnostic_on_droplet.py")
            print("Uploaded run_last_10_blocked_diagnostic_on_droplet.py")
        finally:
            sftp.close()
        cmd = f"{cd} && python3 scripts/run_last_10_blocked_diagnostic_on_droplet.py 2>&1"
        out, err, rc = c._execute(cmd, timeout=30)
        print("\n--- Last 10 blocked trades (diagnostic from droplet) ---\n")
        print(out or "(no output)")
        if err:
            print(err, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
