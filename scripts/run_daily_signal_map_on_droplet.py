#!/usr/bin/env python3
"""Run daily SIGNAL_MAP on droplet via DropletClient."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/root/stock-bot"


def main() -> int:
    parser = __import__("argparse").ArgumentParser()
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

    cmd = f"cd {REMOTE_ROOT} && git pull origin main && REPO_DIR={REMOTE_ROOT} bash scripts/run_daily_signal_map_on_droplet.sh{date_arg}"
    print(f"[RUN] {cmd}")
    out, err, rc = client._execute(cmd, timeout=60)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)

    from datetime import datetime, timezone
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_name = f"SIGNAL_MAP_{date_str}.md"
    remote = f"{REMOTE_ROOT}/reports/{report_name}"
    local = REPO / "reports" / report_name
    local.parent.mkdir(parents=True, exist_ok=True)
    try:
        sftp.get(remote, str(local))
        print(f"[OK] Fetched {report_name}")
    except FileNotFoundError:
        print(f"[WARN] {report_name} not found on droplet")

    client.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
