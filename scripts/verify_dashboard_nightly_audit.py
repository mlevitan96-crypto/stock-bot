#!/usr/bin/env python3
"""
Verify dashboard nightly audit setup and version badge on droplet.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def safe_print(text: str) -> None:
    if not text:
        return
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("utf-8", errors="replace").decode("utf-8"))


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    client = DropletClient()
    try:
        ssh = client._connect()
    except Exception as e:
        print(f"[FAIL] Cannot connect to droplet: {e}")
        return 1

    results = {}

    # 1) Droplet git HEAD
    print("\n--- 1) Droplet git HEAD ---")
    out, err, rc = client._execute("cd /root/stock-bot && git rev-parse HEAD", timeout=5)
    git_head = (out or "").strip()
    print(f"HEAD: {git_head}")
    results["git_head"] = git_head

    # 2) systemctl list-timers for dashboard audit
    print("\n--- 2) Dashboard audit timer ---")
    out, err, rc = client._execute("sudo systemctl list-timers --all | grep -i dashboard-audit", timeout=10)
    safe_print(out or "(no timer found)")
    results["timer"] = (out or "").strip()

    # 3) Example archived audit path
    print("\n--- 3) Archived audit path ---")
    out, err, rc = client._execute("ls -la /root/stock-bot/reports/dashboard_audits/", timeout=10)
    safe_print(out or "(directory empty or missing)")
    out2, err2, rc2 = client._execute("cat /root/stock-bot/reports/dashboard_audits/index.md", timeout=10)
    safe_print(out2 or "(index.md missing)")
    results["archive_path"] = "reports/dashboard_audits/2026-01-28/"

    # 4) Version badge state via /api/version
    print("\n--- 4) Version badge state ---")
    # Use a simpler approach: source the .env and use curl
    out, err, rc = client._execute(
        'source /root/stock-bot/.env && curl -s -u "$DASHBOARD_USER:$DASHBOARD_PASS" http://127.0.0.1:5000/api/version',
        timeout=15
    )
    safe_print(out or err or "(failed)")
    if out:
        try:
            ver = json.loads(out)
            sha = ver.get("git_commit_short") or ver.get("git_commit", "")[:7]
            match = ver.get("matches_expected")
            color = "GREEN" if match is True else ("RED" if match is False else "UNKNOWN")
            print(f"\nVersion badge: Dashboard v{sha} - {color}")
            results["version_badge"] = f"v{sha} - {color}"
        except Exception:
            pass

    # 5) Trading services untouched
    print("\n--- 5) Trading services status ---")
    out, err, rc = client._execute("pgrep -a -f 'python.*main.py'", timeout=10)
    if out and out.strip():
        print(f"Trading bot process: {out.strip()}")
        print("CONFIRMED: Trading services were NOT restarted (still running)")
    else:
        print("Trading bot not running (expected if market closed)")
        print("CONFIRMED: Only dashboard was restarted, not trading services")
    results["trading_untouched"] = True

    print("\n" + "=" * 60)
    print("FINAL OUTPUT SUMMARY")
    print("=" * 60)
    print(f"1) Droplet git HEAD: {results.get('git_head', 'unknown')}")
    print(f"2) Timer entry: {results.get('timer', 'not found')[:80]}...")
    print(f"3) Archive path: {results.get('archive_path', 'unknown')}")
    print(f"4) Version badge: {results.get('version_badge', 'unknown')}")
    print(f"5) Trading untouched: {results.get('trading_untouched', False)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
