#!/usr/bin/env python3
"""
Install Alpaca fast-lane shadow cron jobs on the droplet.
Reads existing crontab, appends cycle (every 15 min) and supervisor (every 4h) if missing,
writes back and confirms. Ensures /root/.alpaca_env and scripts exist.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

# Exact cron lines to add (must match exactly for idempotent check)
CRON_CYCLE = "*/15 * * * * . /root/.alpaca_env && cd /root/stock-bot && python3 scripts/run_fast_lane_shadow_cycle.py >> /root/fast_lane_shadow.log 2>&1"
CRON_SUPERVISOR = "0 */4 * * * . /root/.alpaca_env && cd /root/stock-bot && python3 scripts/run_fast_lane_supervisor.py >> /root/fast_lane_supervisor.log 2>&1"


def main() -> int:
    from droplet_client import DropletClient

    with DropletClient() as c:
        proj = c.project_dir.replace("~", "/root")
        # 1) Ensure env and scripts exist
        out, err, rc = c._execute(f"test -r /root/.alpaca_env && echo OK || echo MISSING", timeout=5)
        if "OK" not in out:
            print("WARNING: /root/.alpaca_env not readable. Cron will still be installed; fix env on droplet.", file=sys.stderr)
        out2, _, _ = c._execute(f"test -f {proj}/scripts/run_fast_lane_shadow_cycle.py && test -f {proj}/scripts/run_fast_lane_supervisor.py && echo OK || echo MISSING", timeout=5)
        if "OK" not in out2:
            print("ERROR: Fast-lane scripts not found on droplet. Push code and pull on droplet first.", file=sys.stderr)
            return 1

        # 2) Read current crontab (exit 1 when no crontab is normal)
        out, err, rc = c._execute("crontab -l 2>/dev/null || true", timeout=5)
        lines = [s.strip() for s in (out or "").splitlines() if s.strip() and not s.strip().startswith("#")]

        # 3) Append if missing
        added = []
        if CRON_CYCLE not in lines:
            lines.append(CRON_CYCLE)
            added.append("cycle (every 15 min)")
        if CRON_SUPERVISOR not in lines:
            lines.append(CRON_SUPERVISOR)
            added.append("supervisor (every 4h)")

        if not added:
            print("Fast-lane cron entries already present. No change.")
            out, _, _ = c._execute("crontab -l 2>/dev/null || true", timeout=5)
            print(out or "(empty)")
            return 0

        # 4) Write new crontab (use Python on droplet to avoid escaping)
        new_crontab = "\n".join(lines) + "\n"
        import base64
        b64 = base64.b64encode(new_crontab.encode("utf-8")).decode("ascii")
        cmd = f"python3 -c \"import base64,sys; open('/tmp/fl_cron.txt','wb').write(base64.b64decode('{b64}')); sys.exit(0)\" && crontab /tmp/fl_cron.txt && rm -f /tmp/fl_cron.txt"
        out, err, rc = c._execute(cmd, timeout=10)
        if rc != 0:
            print("Failed to install crontab:", out, err, file=sys.stderr)
            return 1

        # 5) Confirm
        out, _, _ = c._execute("crontab -l 2>/dev/null || true", timeout=5)
        print("Installed:", ", ".join(added))
        print("Current crontab:")
        print(out or "(empty)")
        if CRON_CYCLE in (out or "") and CRON_SUPERVISOR in (out or ""):
            print("Verification: both fast-lane entries present.")
        else:
            print("WARNING: Verification failed; check crontab -l on droplet.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
