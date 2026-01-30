#!/usr/bin/env python3
"""Run snapshot harness on droplet via DropletClient."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/root/stock-bot"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None)
    args = parser.parse_args()

    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    date_arg = f" {args.date}" if args.date else ""
    client = DropletClient()
    try:
        ssh = client._connect()
        sftp = ssh.open_sftp()
    except Exception as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1

    cmd = f"cd {REMOTE_ROOT} && git pull origin main && REPO_DIR={REMOTE_ROOT} bash scripts/run_snapshot_harness_on_droplet.sh{date_arg}"
    print(f"[RUN] {cmd}")
    out, err, rc = client._execute(cmd, timeout=180)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)

    from datetime import datetime, timezone
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for name in [
        f"signal_snapshots_harness_{date_str}.jsonl",
        f"SNAPSHOT_HARNESS_VERIFICATION_{date_str}.md",
        f"SIGNAL_MAP_{date_str}.md",
    ]:
        if "jsonl" in name:
            remote = f"{REMOTE_ROOT}/logs/{name}"
            local = REPO / "logs" / name
        else:
            remote = f"{REMOTE_ROOT}/reports/{name}"
            local = REPO / "reports" / name
        local.parent.mkdir(parents=True, exist_ok=True)
        try:
            sftp.get(remote, str(local))
            print(f"[OK] Fetched {name}")
        except FileNotFoundError:
            print(f"[WARN] {name} not found on droplet")

    client.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
