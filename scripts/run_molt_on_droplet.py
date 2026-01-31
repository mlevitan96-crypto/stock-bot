#!/usr/bin/env python3
"""Run Molt workflow on droplet via DropletClient."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/root/stock-bot"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None)
    args = parser.parse_args()

    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cmd = f"cd {REMOTE_ROOT} && REPO_DIR={REMOTE_ROOT} bash scripts/run_molt_on_droplet.sh {date_str}"

    client = DropletClient()
    try:
        ssh = client._connect()
        sftp = ssh.open_sftp()
    except Exception as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1

    print(f"[RUN] {cmd}")
    out, err, rc = client._execute(cmd, timeout=300)
    if out:
        safe = out.encode("ascii", errors="replace").decode("ascii")
        print(safe)
    if err:
        safe_err = err.encode("ascii", errors="replace").decode("ascii")
        print(safe_err, file=sys.stderr)

    for name in [
        f"LEARNING_STATUS_{date_str}.md",
        f"ENGINEERING_HEALTH_{date_str}.md",
        f"PROMOTION_DISCIPLINE_{date_str}.md",
        f"MEMORY_BANK_CHANGE_PROPOSAL_{date_str}.md",
        f"PROMOTION_PROPOSAL_{date_str}.md",
        f"REJECTION_WITH_REASON_{date_str}.md",
    ]:
        remote = f"{REMOTE_ROOT}/reports/{name}"
        local = REPO / "reports" / name
        local.parent.mkdir(parents=True, exist_ok=True)
        try:
            sftp.get(remote, str(local))
            print(f"[OK] Fetched {name}")
        except FileNotFoundError:
            pass

    client.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
