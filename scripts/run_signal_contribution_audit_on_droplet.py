#!/usr/bin/env python3
"""
Run signal contribution & intelligence gap audit on droplet and pull report to local.
Uses DropletClient (droplet_config.json) — correct IP 104.236.102.57 only.
Usage: python scripts/run_signal_contribution_audit_on_droplet.py [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/root/stock-bot"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Target date YYYY-MM-DD")
    args = parser.parse_args()
    date_arg = f" {args.date}" if args.date else ""

    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    client = DropletClient()
    try:
        ssh = client._connect()
        sftp = ssh.open_sftp()
    except Exception as e:
        print(f"[FAIL] Cannot connect to droplet: {e}", file=sys.stderr)
        return 1

    cmd = f"cd {REMOTE_ROOT} && git pull origin main && REPO_DIR={REMOTE_ROOT} bash scripts/run_signal_contribution_audit_on_droplet.sh{date_arg}"
    print(f"[RUN] {cmd}")
    out, err, rc = client._execute(cmd, timeout=120)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)

    # Fetch report to local
    from datetime import datetime, timezone
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_name = f"STOCK_SIGNAL_CONTRIBUTION_AND_GAPS_{date_str}.md"
    remote = f"{REMOTE_ROOT}/reports/{report_name}"
    local = REPO / "reports" / report_name
    local.parent.mkdir(parents=True, exist_ok=True)
    try:
        sftp.get(remote, str(local))
        print(f"[OK] Fetched {report_name}")
    except FileNotFoundError:
        print(f"[WARN] Missing {report_name} on droplet")

    client.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
