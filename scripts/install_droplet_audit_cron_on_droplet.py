#!/usr/bin/env python3
"""
Install the droplet audit + sync cron on the droplet (21:32 UTC weekdays).

Run after pushing run_droplet_audit_and_sync.sh and reports/droplet_audit/ to GitHub
and pulling on the droplet. Adds cron to run the audit and push results to GitHub.

Usage (from repo root, with droplet access):
    python scripts/install_droplet_audit_cron_on_droplet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def detect_stockbot_root(client) -> str:
    cmd = (
        "ROOT=/root/stock-bot; "
        "[ -d /root/stock-bot-current/scripts ] && [ -f /root/stock-bot-current/scripts/run_droplet_audit_and_sync.sh ] "
        "&& ROOT=/root/stock-bot-current; echo $ROOT"
    )
    out, _, _ = client._execute(cmd, timeout=5)
    return (out or "").strip() or "/root/stock-bot"


def main() -> int:
    from droplet_client import DropletClient

    c = DropletClient()
    root = detect_stockbot_root(c)

    # Ensure script exists on droplet (should be there after git pull)
    out, err, rc = c._execute(f"test -f {root}/scripts/run_droplet_audit_and_sync.sh && echo ok", timeout=5)
    if "ok" not in (out or ""):
        print("run_droplet_audit_and_sync.sh not found on droplet. Pull latest from GitHub first.", file=sys.stderr)
        c.close()
        return 1

    c._execute(f"chmod +x {root}/scripts/run_droplet_audit_and_sync.sh", timeout=5)
    print("chmod +x run_droplet_audit_and_sync.sh")

    # Remove old sync-only line; add audit+sync line
    cron_line = (
        f"32 21 * * 1-5 cd {root} && bash scripts/run_droplet_audit_and_sync.sh >> {root}/logs/cron_sync.log 2>&1"
    )
    install = (
        "(crontab -l 2>/dev/null | grep -v 'droplet_sync_to_github.sh' | grep -v 'run_droplet_audit_and_sync.sh' || true; "
        f"printf '%s\\n' '{cron_line}') | crontab -"
    )
    out, err, rc = c._execute(install, timeout=10)
    if rc != 0:
        print("crontab install failed:", out or err, file=sys.stderr)
        c.close()
        return rc

    print("Cron installed: 21:32 UTC weekdays -> run_droplet_audit_and_sync.sh (audit + push to GitHub)")
    out2, _, _ = c._execute("crontab -l", timeout=5)
    print("crontab -l:\n", out2 or "")
    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
