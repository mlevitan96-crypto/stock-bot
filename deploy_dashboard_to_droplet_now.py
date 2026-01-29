#!/usr/bin/env python3
"""
Deploy local dashboard.py to droplet via SFTP and restart the dashboard.
Use this when you've fixed dashboard locally and want the droplet to serve it
without pushing to GitHub first.

Steps:
  1. Upload dashboard.py to /root/stock-bot/dashboard.py
  2. Restart stock-bot-dashboard service (and pkill fallback)
  3. Verify the served HTML contains expanded minimal loaders (granularity fix)

Requires: droplet_config.json (or DROPLET_* env) and paramiko.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent
REMOTE_ROOT = "/root/stock-bot"
# Marker in our expanded minimal loaders (so we know new code is live)
GRANULARITY_MARKER = "Signal Funnel (30m)"


def main() -> int:
    sys.path.insert(0, str(REPO))
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Install: pip install paramiko", file=sys.stderr)
        return 1

    local_dashboard = REPO / "dashboard.py"
    if not local_dashboard.exists():
        print(f"ERROR: Missing {local_dashboard}", file=sys.stderr)
        return 1

    print("=" * 60)
    print("DEPLOY DASHBOARD TO DROPLET (upload + restart)")
    print("=" * 60)

    client = DropletClient()
    try:
        ssh = client._connect()
        sftp = ssh.open_sftp()
    except Exception as e:
        print(f"ERROR: Cannot connect to droplet: {e}", file=sys.stderr)
        return 1

    # 1. Upload dashboard.py
    print("\n[1/4] Uploading dashboard.py ...")
    try:
        sftp.put(str(local_dashboard), f"{REMOTE_ROOT}/dashboard.py")
        print("      OK  dashboard.py uploaded")
    except Exception as e:
        print(f"      ERROR: {e}", file=sys.stderr)
        sftp.close()
        return 1
    sftp.close()

    # 2. Restart dashboard
    print("\n[2/4] Restarting dashboard ...")
    client._execute("pkill -f 'python.*dashboard.py' || true", timeout=5)
    time.sleep(2)
    out, err, rc = client._execute("sudo systemctl restart stock-bot-dashboard", timeout=15)
    if rc != 0:
        print("      systemctl restart failed, trying nohup fallback ...")
        client._execute(
            f"bash -lc 'cd {REMOTE_ROOT} && nohup python3 dashboard.py > logs/dashboard.log 2>&1 &'",
            timeout=10,
        )
    else:
        print("      OK  stock-bot-dashboard restarted")
    time.sleep(5)

    # 3. Verify process
    print("\n[3/4] Checking dashboard process ...")
    out, _, _ = client._execute(
        "ps aux | grep -E 'dashboard\\.py' | grep -v grep | head -1",
        timeout=5,
    )
    if out.strip():
        print(f"      OK  {out.strip()[:80]}")
    else:
        print("      WARN No dashboard process found (may still be starting)")

    # 4. Verify HTML contains granularity fix (fetch page with auth from droplet)
    print("\n[4/4] Verifying granular content in served HTML ...")
    cmd = (
        f"bash -lc 'cd {REMOTE_ROOT} && set -a && source .env 2>/dev/null && set +a && "
        "if [ -z \"$DASHBOARD_USER\" ] || [ -z \"$DASHBOARD_PASS\" ]; then "
        "echo \"SKIP_NO_AUTH\"; exit 0; fi && "
        f"curl -s -u \"$DASHBOARD_USER:$DASHBOARD_PASS\" http://127.0.0.1:5000/ 2>/dev/null | head -c 120000'"
    )
    out, err, rc = client._execute(cmd, timeout=15)
    if "SKIP_NO_AUTH" in (out or ""):
        print("      SKIP (no DASHBOARD_USER/PASS in .env)")
    elif rc != 0 or not out:
        print("      WARN Could not fetch dashboard HTML")
    elif GRANULARITY_MARKER in (out or ""):
        print(f"      OK  HTML contains \"{GRANULARITY_MARKER}\" (expanded loaders deployed)")
    else:
        print(f"      WARN HTML does not contain \"{GRANULARITY_MARKER}\" — hard refresh browser (Ctrl+F5) or clear cache")

    client.close()
    print("\n" + "=" * 60)
    print("Done. Open the dashboard and do a hard refresh (Ctrl+F5) to see granular tabs.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
