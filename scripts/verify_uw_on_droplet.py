#!/usr/bin/env python3
"""Verify on droplet: UW daemon running, cache present, and API calls per day. Use MEMORY_BANK_ALPACA.md context."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    try:
        from droplet_client import DropletClient
    except ImportError:
        print("droplet_client not found; run from repo root", file=sys.stderr)
        return 1

    proj = "/root/stock-bot"  # droplet default
    with DropletClient() as c:
        proj = getattr(c, "project_dir", proj).rstrip("/")
        print("=== UW verification on droplet ===\n")
        # 1) Daemon
        out, err, rc = c._execute("systemctl is-active uw-flow-daemon.service 2>/dev/null || echo inactive")
        daemon_status = (out or "").strip()
        print(f"1. UW flow daemon: {daemon_status}")
        if err and "inactive" not in daemon_status:
            print(err, file=sys.stderr)
        # 2) Cache file
        out2, _, _ = c._execute_with_cd(
            f"ls -la data/uw_flow_cache.json 2>/dev/null && stat -c 'Modified: %y' data/uw_flow_cache.json 2>/dev/null || echo 'Cache file missing'",
            timeout=10,
        )
        print(f"\n2. UW flow cache (data/uw_flow_cache.json):\n{out2 or ' (no output)'}")
        # 3) Quota log and API calls per day
        out3, err3, rc3 = c._execute_with_cd(
            "python3 analyze_uw_usage.py --hours 24 --path data/uw_api_quota.jsonl --daily-limit 15000 2>&1",
            timeout=30,
        )
        print("3. UW API usage (last 24h, daily limit 15000):\n")
        print(out3 or "(no output)")
        if err3:
            print(err3, file=sys.stderr)
        if rc3 != 0 and "No UW calls found" not in (out3 or ""):
            print("(analyze_uw_usage exited with", rc3, ")", file=sys.stderr)
    print("\n=== end ===\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
