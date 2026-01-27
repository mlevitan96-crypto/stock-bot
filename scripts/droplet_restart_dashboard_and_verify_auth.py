#!/usr/bin/env python3
"""
Restart dashboard on droplet and verify HTTP Basic Auth behavior.

This is operational-only. It does not alter code on the droplet.
It verifies:
- /health returns 401 without auth
- /health returns JSON with auth
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from droplet_client import DropletClient

    c = DropletClient()
    try:
        # Kill any existing dashboard
        c._execute("bash -lc 'cd /root/stock-bot && pkill -f \"python.*dashboard.py\" || true'", timeout=30)

        # Start dashboard (Memory Bank verified method).
        # NOTE: Avoid droplet_client._execute() here because some shells keep the SSH channel open
        # when backgrounding processes; we don't want to block waiting for stdout.
        ssh = c._connect()
        stdin, stdout, stderr = ssh.exec_command(
            "bash -lc 'cd /root/stock-bot && nohup python3 dashboard.py > logs/dashboard.log 2>&1 < /dev/null &'",
            timeout=10,
        )
        try:
            # Best-effort close streams; do not wait for command completion.
            stdin.close()
            stdout.channel.close()
            stderr.channel.close()
        except Exception:
            pass

        time.sleep(4)

        # Verify unauthenticated request is blocked
        out401, err401, code401 = c._execute(
            "bash -lc 'curl -s -o /dev/null -w \"%{http_code}\" http://127.0.0.1:5000/health'",
            timeout=20,
        )
        if (out401 or "").strip() != "401":
            raise SystemExit(f"Expected 401 without auth, got: {(out401 or err401).strip()[:50]}")

        # Verify authenticated request succeeds (without exposing creds)
        out200, err200, code200 = c._execute(
            "bash -lc 'cd /root/stock-bot && set -a && source .env && set +a && "
            "curl -s -o /dev/null -w \"%{http_code}\" -u \"$DASHBOARD_USER:$DASHBOARD_PASS\" http://127.0.0.1:5000/health'",
            timeout=20,
        )
        if (out200 or "").strip() != "200":
            raise SystemExit(f"Expected 200 with auth, got: {(out200 or err200).strip()[:80]}")

        # Verify root page is also protected
        root401, _, _ = c._execute(
            "bash -lc 'curl -s -o /dev/null -w \"%{http_code}\" http://127.0.0.1:5000/'",
            timeout=20,
        )
        if (root401 or "").strip() != "401":
            raise SystemExit(f"Expected 401 on / without auth, got: {str(root401).strip()[:50]}")

        root200, _, _ = c._execute(
            "bash -lc 'cd /root/stock-bot && set -a && source .env && set +a && "
            "curl -s -o /dev/null -w \"%{http_code}\" -u \"$DASHBOARD_USER:$DASHBOARD_PASS\" http://127.0.0.1:5000/'",
            timeout=20,
        )
        if (root200 or "").strip() != "200":
            raise SystemExit(f"Expected 200 on / with auth, got: {str(root200).strip()[:50]}")

        # Spot-check an API route is also protected and reachable with auth
        pos401, _, _ = c._execute(
            "bash -lc 'curl -s -o /dev/null -w \"%{http_code}\" http://127.0.0.1:5000/api/positions'",
            timeout=20,
        )
        if (pos401 or "").strip() != "401":
            raise SystemExit(f"Expected 401 on /api/positions without auth, got: {str(pos401).strip()[:50]}")

        pos200, _, _ = c._execute(
            "bash -lc 'cd /root/stock-bot && set -a && source .env && set +a && "
            "curl -s -o /dev/null -w \"%{http_code}\" -u \"$DASHBOARD_USER:$DASHBOARD_PASS\" http://127.0.0.1:5000/api/positions'",
            timeout=20,
        )
        if (pos200 or "").strip() != "200":
            raise SystemExit(f"Expected 200 on /api/positions with auth, got: {str(pos200).strip()[:50]}")

        # Fetch a small snippet of JSON to confirm it responds (safe output)
        out_json, err_json, code_json = c._execute(
            "bash -lc 'cd /root/stock-bot && set -a && source .env && set +a && "
            "curl -s -u \"$DASHBOARD_USER:$DASHBOARD_PASS\" http://127.0.0.1:5000/health | head -c 200'",
            timeout=20,
        )
        if code_json != 0 or not (out_json or "").strip():
            raise SystemExit("Authenticated /health did not return a body")

        print("[OK] Dashboard restarted and Basic Auth verified (401 unauth, 200 auth).")
        print(f"[OK] /health sample (truncated): {(out_json or '').strip()}")
        return 0
    finally:
        c.close()


if __name__ == "__main__":
    raise SystemExit(main())

