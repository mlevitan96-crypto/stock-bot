#!/usr/bin/env python3
"""
Upload and run verify_all_signals_on_droplet.py on the droplet; print full output.
Ensures daemon is running and all signal components are contributing.
Run from repo root: python scripts/run_verify_all_signals_via_droplet.py
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
        sftp = c._connect().open_sftp()
        try:
            local_script = REPO / "scripts" / "verify_all_signals_on_droplet.py"
            if not local_script.exists():
                print(f"Local script not found: {local_script}", file=sys.stderr)
                return 1
            sftp.put(str(local_script), f"{root}/scripts/verify_all_signals_on_droplet.py")
            print("Uploaded verify_all_signals_on_droplet.py")
        finally:
            sftp.close()
        cmd = f"{cd} && python3 scripts/verify_all_signals_on_droplet.py 2>&1"
        out, err, rc = c._execute(cmd, timeout=60)
        print("\n" + (out or "(no output)"))
        if err:
            print(err, file=sys.stderr)
        return rc


if __name__ == "__main__":
    sys.exit(main())
