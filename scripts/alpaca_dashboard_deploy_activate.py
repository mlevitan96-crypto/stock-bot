#!/usr/bin/env python3
"""
Alpaca dashboard deploy + single systemd restart + verification.
Syncs only dashboard.py to the droplet; does not touch trading, learning, or telemetry jobs.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from droplet_client import DropletClient  # noqa: E402

REMOTE_DASH = "/root/stock-bot/dashboard.py"
VERIFY_LOCAL = Path(__file__).resolve().parent / "_alpaca_dashboard_verify_remote.py"
VERIFY_REMOTE = "/tmp/alpaca_dashboard_verify_remote.py"


def _git_head() -> str:
    r = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout.strip()


def main() -> int:
    commit = _git_head()
    dash_text = (REPO / "dashboard.py").read_text(encoding="utf-8", errors="replace")
    print("PHASE0_COMMIT", commit)
    print("PHASE0_HAS_data_integrity_route", "/api/dashboard/data_integrity" in dash_text)
    print("PHASE0_HAS_system_health_tab", 'data-tab="system_health"' in dash_text)
    print("PHASE0_HAS_strict_fields", "strict_alpaca_chain" in dash_text and "entry_reason_display" in dash_text)

    c = DropletClient()
    try:
        # Phase 1
        c.put_file(REPO / "dashboard.py", REMOTE_DASH)
        out, err, code = c._execute(
            f"chown root:root {REMOTE_DASH} && chmod 644 {REMOTE_DASH} && ls -la {REMOTE_DASH}",
            timeout=30,
        )
        print("PHASE1", out.strip())
        if code != 0:
            print("PHASE1_ERR", err, file=sys.stderr)
            return 1

        # Phase 2 — strays only (do not stop systemd before restart)
        out2, err2, _ = c._execute(
            "echo '--- dashboard processes before hygiene ---'; "
            "ps aux | grep '[d]ashboard.py' || true; "
            "pkill -f '/root/stock-bot/venv/bin/python.*dashboard.py' 2>/dev/null || true; "
            "pkill -f 'nohup python3 dashboard.py' 2>/dev/null || true; "
            "pkill -f 'nohup.*dashboard.py' 2>/dev/null || true; "
            "sleep 1; "
            "echo '--- after pkill strays ---'; "
            "ps aux | grep '[d]ashboard.py' || true",
            timeout=45,
        )
        print(out2)
        if err2.strip():
            print("PHASE2_STDERR", err2, file=sys.stderr)

        # Phase 3 — exactly one restart
        restart_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        out3, err3, code3 = c._execute(
            "systemctl restart stock-bot-dashboard && sleep 4 && "
            f"echo PHASE3_RESTART_UTC={restart_utc}",
            timeout=90,
        )
        print(out3)
        if code3 != 0:
            print("PHASE3_ERR", err3, file=sys.stderr)
            return 1
        print("PHASE3_RESTART_UTC", restart_utc)

        out4, _, _ = c._execute(
            "echo ACTIVE=$(systemctl is-active stock-bot-dashboard); "
            "echo TRADING=$(systemctl is-active stock-bot.service); "
            "ss -tlnp 2>/dev/null | grep 5000 || true; "
            "echo '--- ps dashboard ---'; "
            "ps aux | grep '[d]ashboard.py' || true",
            timeout=30,
        )
        print("PHASE3_STATUS\n", out4)

        # Phase 4
        if not VERIFY_LOCAL.is_file():
            print("MISSING", VERIFY_LOCAL, file=sys.stderr)
            return 1
        c.put_file(VERIFY_LOCAL, VERIFY_REMOTE)
        out5, err5, code5 = c._execute(f"python3 {VERIFY_REMOTE}", timeout=120)
        print(out5)
        if err5.strip():
            print("VERIFY_STDERR", err5, file=sys.stderr)
        if code5 != 0:
            return code5

    finally:
        c.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
