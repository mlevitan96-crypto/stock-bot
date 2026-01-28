#!/usr/bin/env python3
"""
Deploy dashboard_endpoint_audit.py + inventory to droplet, run audit, pull reports.
Prints verdict: count PASS/WARN/FAIL and list of FAIL endpoints with reason_code.

Optional: set DROPLET_DEPLOY_BEFORE_AUDIT=1 to run git fetch + reset on droplet before audit.
Optional: set DROPLET_DASHBOARD_SERVICE=<name> to restart only the dashboard service (e.g. stock-bot-dashboard) after deploy.

Usage: python scripts/run_dashboard_endpoint_audit_on_droplet.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/root/stock-bot"

REPORT_NAMES = [
    "DASHBOARD_ENDPOINT_AUDIT.md",
    "DASHBOARD_TELEMETRY_DIAGNOSIS.md",
    "DASHBOARD_PANEL_INVENTORY.md",
]


def main() -> int:
    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    client = DropletClient()
    try:
        ssh = client._connect()
        sftp = ssh.open_sftp()
    except Exception as e:
        print(f"[FAIL] Cannot connect to droplet: {e}", file=sys.stderr)
        return 1

    # Optional: deploy latest main on droplet
    if os.getenv("DROPLET_DEPLOY_BEFORE_AUDIT", "").strip() in ("1", "true", "yes"):
        cmd_deploy = f"cd {REMOTE_ROOT} && git fetch origin main && git reset --hard origin/main"
        print(f"[RUN] Deploy: {cmd_deploy}")
        out, err, rc = client._execute(cmd_deploy, timeout=60)
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            print("[WARN] Deploy had non-zero exit; continuing with audit.")
        # Upload local dashboard.py so droplet has /api/sre/self_heal_events (may not be on origin/main yet)
        local_dashboard = REPO / "dashboard.py"
        if local_dashboard.exists():
            try:
                sftp.put(str(local_dashboard), f"{REMOTE_ROOT}/dashboard.py")
                print("[OK] Uploaded dashboard.py (local copy for route parity)")
            except Exception as e:
                print(f"[WARN] dashboard.py upload: {e}")
        # Optional: restart dashboard service only (ensure single process on :5000)
        svc = os.getenv("DROPLET_DASHBOARD_SERVICE", "").strip()
        if svc:
            # Stop any non-systemd dashboard so our restarted service owns :5000
            client._execute("sudo pkill -f 'python.*dashboard.py' || true", timeout=5)
            time.sleep(2)
            cmd_restart = f"sudo systemctl start {svc}"
            print(f"[RUN] Restart dashboard: {cmd_restart}")
            out, err, rc = client._execute(cmd_restart, timeout=15)
            if out:
                print(out)
            if err:
                print(err, file=sys.stderr)
            time.sleep(5)

    # Upload audit script
    local_script = REPO / "scripts" / "dashboard_endpoint_audit.py"
    remote_script = f"{REMOTE_ROOT}/scripts/dashboard_endpoint_audit.py"
    if not local_script.exists():
        print(f"[FAIL] Missing {local_script}", file=sys.stderr)
        return 1
    sftp.put(str(local_script), remote_script)
    print("[OK] Uploaded dashboard_endpoint_audit.py")

    # Upload inventory so audit has canonical list (optional; audit creates if missing)
    inv_local = REPO / "data" / "dashboard_panel_inventory.json"
    inv_remote = f"{REMOTE_ROOT}/data/dashboard_panel_inventory.json"
    if inv_local.exists():
        try:
            sftp.put(str(inv_local), inv_remote)
            print("[OK] Uploaded dashboard_panel_inventory.json")
        except Exception as e:
            print(f"[WARN] Inventory upload: {e}")

    # Run audit on droplet (dashboard must be up on 5000; auth from droplet .env).
    # EXPECTED_GIT_COMMIT = droplet HEAD so audit can detect PROCESS_DRIFT if running dashboard != deployed commit.
    cmd = f"cd {REMOTE_ROOT} && export EXPECTED_GIT_COMMIT=$(git rev-parse HEAD) && python3 scripts/dashboard_endpoint_audit.py"
    print(f"[RUN] {cmd}")
    out, err, rc = client._execute(cmd, timeout=120)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)

    # Pull reports
    reports_local = REPO / "reports"
    reports_local.mkdir(parents=True, exist_ok=True)
    for name in REPORT_NAMES:
        remote = f"{REMOTE_ROOT}/reports/{name}"
        local = reports_local / name
        try:
            sftp.get(remote, str(local))
            print(f"[OK] Fetched {name}")
        except FileNotFoundError:
            print(f"[WARN] Missing {name}")

    # Verdict from DASHBOARD_ENDPOINT_AUDIT.md
    audit_md = reports_local / "DASHBOARD_ENDPOINT_AUDIT.md"
    if audit_md.exists():
        text = audit_md.read_text(encoding="utf-8")
        lines = text.splitlines()
        pass_count = warn_count = fail_count = 0
        fail_endpoints = []
        for line in lines:
            parts = [p.strip() for p in line.split("|")]
            # Summary count row: | PASS | 5 |
            if len(parts) >= 3 and parts[1] in ("PASS", "WARN", "FAIL") and parts[2].isdigit():
                n = int(parts[2])
                if parts[1] == "PASS":
                    pass_count = n
                elif parts[1] == "WARN":
                    warn_count = n
                else:
                    fail_count = n
            # Detail table row: | panel/endpoint | PASS/FAIL | reason_code | ...
            if len(parts) >= 4 and parts[2] == "FAIL" and "Panel" not in line and "---" not in line and not parts[1].isdigit():
                fail_endpoints.append((parts[1], parts[3] if len(parts) > 3 else ""))
        print("")
        print("--- Verdict ---")
        print(f"PASS: {pass_count}  WARN: {warn_count}  FAIL: {fail_count}")
        if fail_endpoints:
            print("FAIL endpoints:")
            for ep, reason in fail_endpoints[:30]:
                print(f"  - {ep}  {reason}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
