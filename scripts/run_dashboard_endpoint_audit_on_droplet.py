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


def _safe_print(text: str, file=None) -> None:
    """Print remote output without UnicodeEncodeError on Windows (e.g. systemctl bullet)."""
    if not text:
        return
    try:
        print(text, file=file)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8"), file=file)


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

    # Optional: deploy latest main on droplet + install/restart dashboard only (no trading service)
    if os.getenv("DROPLET_DEPLOY_BEFORE_AUDIT", "").strip() in ("1", "true", "yes"):
        cmd_deploy = f"cd {REMOTE_ROOT} && git fetch origin main && git reset --hard origin/main"
        print(f"[RUN] Deploy: {cmd_deploy}")
        out, err, rc = client._execute(cmd_deploy, timeout=60)
        if out:
            _safe_print(out)
        if err:
            _safe_print(err, file=sys.stderr)
        if rc != 0:
            print("[WARN] Deploy had non-zero exit; continuing with audit.")
        # Get deployed commit so dashboard reports it via GIT_COMMIT (avoids PROCESS_DRIFT)
        out, err, rc_commit = client._execute(f"cd {REMOTE_ROOT} && git rev-parse HEAD", timeout=5)
        deploy_commit = (out or "").strip().splitlines()[-1].strip() if out else ""
        # Upload dashboard and deploy service file so droplet has latest code + unit
        local_dashboard = REPO / "dashboard.py"
        if local_dashboard.exists():
            try:
                sftp.put(str(local_dashboard), f"{REMOTE_ROOT}/dashboard.py")
                print("[OK] Uploaded dashboard.py")
            except Exception as e:
                print(f"[WARN] dashboard.py upload: {e}")
        local_service = REPO / "deploy" / "stock-bot-dashboard.service"
        if local_service.exists():
            try:
                content = local_service.read_text(encoding="utf-8")
                if deploy_commit and "Environment=PORT=5000" in content and "GIT_COMMIT" not in content:
                    content = content.replace(
                        "Environment=PORT=5000\n",
                        f"Environment=PORT=5000\nEnvironment=GIT_COMMIT={deploy_commit}\n",
                    )
                import tempfile
                with tempfile.NamedTemporaryFile(mode="w", suffix=".service", delete=False, encoding="utf-8") as f:
                    f.write(content)
                    tmp = f.name
                try:
                    sftp.put(tmp, f"{REMOTE_ROOT}/deploy/stock-bot-dashboard.service")
                    print("[OK] Uploaded deploy/stock-bot-dashboard.service (GIT_COMMIT=%s)" % (deploy_commit[:7] if deploy_commit else "none"))
                finally:
                    os.unlink(tmp)
            except Exception as e:
                print(f"[WARN] service file upload: {e}")
        # Install/update dashboard unit and restart ONLY dashboard (never trading)
        svc = os.getenv("DROPLET_DASHBOARD_SERVICE", "").strip()
        if svc:
            client._execute("sudo pkill -f 'python.*dashboard.py' || true", timeout=5)
            time.sleep(2)
            for cmd in [
                f"sudo cp {REMOTE_ROOT}/deploy/stock-bot-dashboard.service /etc/systemd/system/",
                "sudo systemctl daemon-reload",
                f"sudo systemctl enable {svc}",
                f"sudo systemctl restart {svc}",
            ]:
                print(f"[RUN] {cmd}")
                out, err, rc = client._execute(cmd, timeout=15)
                if out:
                    _safe_print(out)
                if err:
                    _safe_print(err, file=sys.stderr)
                if rc != 0 and "enable" in cmd:
                    pass  # enable often no-op if already enabled
                elif rc != 0:
                    print(f"[WARN] Exit {rc} for: {cmd}")
            time.sleep(5)
            out, err, rc = client._execute(f"sudo systemctl status {svc} --no-pager -l", timeout=10)
            if out:
                _safe_print(out)
            if err:
                _safe_print(err, file=sys.stderr)

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
        _safe_print(out)
    if err:
        _safe_print(err, file=sys.stderr)

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
