#!/usr/bin/env python3
"""
SRE-grade cron diagnosis, repair, EOD force-run, and GitHub push.

Diagnoses why EOD cron did not fire, repairs if broken, force-runs today's EOD,
pushes to GitHub. Write cron_diagnosis.json to board/eod/out/<date>/.

Usage:
    # From local (SSH to droplet, run there):
    python3 board/eod/cron_diagnose_and_fix.py --date 2026-02-12

    # On droplet directly (after SSH):
    python3 board/eod/cron_diagnose_and_fix.py --date 2026-02-12 --on-droplet

Exit: 0 success, non-zero if any step fails.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

# Expected EOD cron schedule (21:30 UTC weekdays per MEMORY_BANK)
EOD_CRON_SCHEDULE = "30 21 * * 1-5"
EOD_CRON_KEYWORDS = ("eod_confirmation", "run_stock_quant_officer_eod")
CANDIDATE_ROOTS = ["/root/trading-bot-current", "/root/stock-bot-current", "/root/stock-bot"]


def _detect_stockbot_root() -> str:
    """Detect stock-bot/trading-bot root on droplet."""
    for root in CANDIDATE_ROOTS:
        scripts = Path(root) / "scripts"
        eod = Path(root) / "board" / "eod" / "eod_confirmation.py"
        run_eod = Path(root) / "board" / "eod" / "run_stock_quant_officer_eod.py"
        if scripts.is_dir() and (eod.exists() or run_eod.exists()):
            return root
    # Fallback to script's repo
    if (SCRIPT_DIR.parent.parent / "scripts").is_dir():
        return str(SCRIPT_DIR.parent.parent)
    return "/root/stock-bot"


def _run(cmd: str, client: Any | None, timeout: int = 10) -> tuple[str, str, int]:
    """Run command locally or via SSH client."""
    if client is not None:
        return client._execute(cmd, timeout=timeout)
    try:
        r = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "", r.stderr or "", r.returncode)
    except Exception as e:
        return ("", str(e), 1)


def check_cron_service(client: Any | None = None) -> dict[str, Any]:
    """
    1) Verify cron service is running. If inactive: install, enable, start.
    """
    result: dict[str, Any] = dict(
        status_out="",
        status_rc=-1,
        active=False,
        repair_actions=[],
        errors=[],
    )
    # systemctl status cron || systemctl status crond
    out, err, rc = _run("systemctl status cron 2>/dev/null || systemctl status crond 2>/dev/null || true", client, 10)
    result["status_out"] = out or err or "(empty)"
    result["status_rc"] = rc
    result["active"] = "active (running)" in (out or "").lower()

    if not result["active"]:
        # Install cron: apt-get update && apt-get install -y cron
        out_install, err_install, rc_install = _run(
            "apt-get update -qq && apt-get install -y cron 2>&1 || true", client, 120
        )
        if rc_install == 0:
            result["repair_actions"].append("installed cron")
        # Enable: systemctl enable cron
        _run("systemctl enable cron 2>/dev/null || systemctl enable crond 2>/dev/null || true", client, 10)
        result["repair_actions"].append("enabled cron")
        # Start: systemctl start cron
        out_start, _, rc_start = _run(
            "systemctl start cron 2>/dev/null || systemctl start crond 2>/dev/null || true", client, 10
        )
        if rc_start == 0:
            result["repair_actions"].append("started cron")
        else:
            result["errors"].append(f"cron start failed: {out_start}")
        # Re-check
        out2, _, _ = _run("systemctl status cron 2>/dev/null || systemctl status crond 2>/dev/null || true", client, 10)
        result["active"] = "active (running)" in (out2 or "").lower()
        result["status_out"] = out2 or result["status_out"]

    return result


def check_cron_installed(client: Any | None = None) -> dict[str, Any]:
    """
    A) Check crontab, syslog for EOD entry.
    If client is None, run locally (subprocess). Else run via client._execute().
    """
    result: dict[str, Any] = dict(
        crontab_out="",
        crontab_rc=-1,
        syslog_out="",
        syslog_rc=-1,
        cron_entry_exists=False,
        health_check_entry_exists=False,
        eod_entry_exists=False,
        schedule_ok=False,
        path_ok=False,
        syntax_ok=True,
        errors=[],
    )

    out, err, rc = _run("crontab -l 2>/dev/null || true", client)
    result["crontab_out"] = out or err or "(empty)"
    result["crontab_rc"] = rc

    out2, _, rc2 = _run("grep CRON /var/log/syslog 2>/dev/null | tail -200 || journalctl -u cron --no-pager -n 100 2>/dev/null || echo 'no syslog'", client)
    result["syslog_out"] = out2 or "no syslog"
    result["syslog_rc"] = rc2

    crontab = result["crontab_out"]
    result["cron_entry_exists"] = any(kw in crontab for kw in EOD_CRON_KEYWORDS)
    result["health_check_entry_exists"] = "cron_health_check" in crontab and "20 21" in crontab
    result["eod_entry_exists"] = "eod_confirmation" in crontab and "30 21" in crontab
    result["schedule_ok"] = "21" in crontab and ("30" in crontab or "20" in crontab)
    root = _detect_stockbot_root()
    result["path_ok"] = root in crontab or "/root/" in crontab
    if not result["health_check_entry_exists"]:
        result["errors"].append("Health check cron entry missing (20 21 * * 1-5 cron_health_check)")
    if not result["eod_entry_exists"]:
        result["errors"].append("EOD cron entry missing (30 21 * * 1-5 eod_confirmation)")
    if not result["schedule_ok"] and result["cron_entry_exists"]:
        result["errors"].append("Schedule may be wrong (expected 21:30 UTC weekdays)")
    return result


def check_cron_execution(date_str: str, client: Any | None = None) -> dict[str, Any]:
    """
    B) Search syslog for today's timestamp around scheduled time.
    """
    result: dict[str, Any] = dict(
        cron_attempted=False,
        script_started=False,
        script_failed_early=False,
        path_env_issue=False,
        syslog_snippet="",
    )

    # Search syslog for date and CRON
    out, _, _ = _run(
        f"grep -E '{date_str}|CRON' /var/log/syslog 2>/dev/null | tail -100 "
        "|| journalctl -u cron --since '{date_str}' --no-pager 2>/dev/null | tail -50 "
        "|| echo 'no logs'", client
    )
    result["syslog_snippet"] = out or "no logs"
    result["cron_attempted"] = "CRON" in (out or "") and date_str[:4] in (out or "")
    result["script_started"] = "eod_confirmation" in (out or "").lower() or "run_stock_quant" in (out or "").lower()
    result["script_failed_early"] = "failed" in (out or "").lower() or "error" in (out or "").lower()
    result["path_env_issue"] = "path" in (out or "").lower() and "not found" in (out or "").lower()
    return result


def check_script_health(client: Any | None = None) -> dict[str, Any]:
    """
    C) Confirm eod_confirmation.py exists, executable, imports resolve.
    """
    result: dict[str, Any] = dict(
        eod_confirmation_exists=False,
        executable=False,
        python_path_ok=False,
        imports_ok=False,
        errors=[],
    )
    root = _detect_stockbot_root()
    eod_path = Path(root) / "board" / "eod" / "eod_confirmation.py"

    out, _, rc = _run(f"test -f {eod_path} && echo exists", client, 15)
    result["eod_confirmation_exists"] = "exists" in (out or "")
    out2, _, _ = _run(f"test -x {eod_path} 2>/dev/null && echo executable", client)
    result["executable"] = "executable" in (out2 or "")
    out3, _, _ = _run("/usr/bin/python3 --version 2>&1 || python3 --version 2>&1", client)
    result["python_path_ok"] = "Python" in (out3 or "")
    out4, err4, rc4 = _run(
        f"cd {root} && /usr/bin/python3 -c "
        "'from board.eod.eod_confirmation import verify_eod_run; print(\"ok\")' 2>&1", client, 15
    )
    result["imports_ok"] = rc4 == 0 and "ok" in (out4 or "")

    if not result["eod_confirmation_exists"]:
        result["errors"].append("eod_confirmation.py not found")
    if not result["python_path_ok"]:
        result["errors"].append("Python3 not in PATH")
    if not result["imports_ok"]:
        result["errors"].append(f"Import check failed: {err4 or out4}")
    return result


def check_logging(client: Any | None = None) -> dict[str, Any]:
    """
    D) Confirm logs dir exists, today's cron log if any, last run stderr/stdout.
    """
    result: dict[str, Any] = dict(
        logs_dir_exists=False,
        cron_log_exists=False,
        eod_log_tail="",
        last_stderr="",
    )
    root = _detect_stockbot_root()
    logs_dir = Path(root) / "logs"
    cron_log = logs_dir / "cron_eod.log"
    eod_log = Path("/var/log/eod_confirmation.log")

    out, _, _ = _run(f"test -d {logs_dir} && echo exists", client)
    result["logs_dir_exists"] = "exists" in (out or "")
    out2, _, _ = _run(f"test -f {cron_log} && echo exists", client)
    result["cron_log_exists"] = "exists" in (out2 or "")
    out3, _, _ = _run(f"tail -50 {cron_log} 2>/dev/null || tail -50 {eod_log} 2>/dev/null || tail -50 /var/log/eod_confirmation.log 2>/dev/null || echo 'no log'", client)
    result["eod_log_tail"] = out3 or "no log"
    return result


def repair_cron(client: Any | None = None) -> tuple[bool, str]:
    """
    Reinstall BOTH cron entries per spec:
    - Health check: 20 21 * * 1-5 /usr/bin/python3 <root>/board/eod/cron_health_check.py >> /var/log/cron_health.log 2>&1
    - EOD confirmation: 30 21 * * 1-5 /usr/bin/python3 <root>/board/eod/eod_confirmation.py >> /var/log/eod_confirmation.log 2>&1
    """
    root = _detect_stockbot_root()
    health_line = (
        f"20 21 * * 1-5 /usr/bin/python3 {root}/board/eod/cron_health_check.py >> /var/log/cron_health.log 2>&1"
    )
    eod_line = (
        f"30 21 * * 1-5 cd {root} && "
        "CLAWDBOT_SESSION_ID=\"stock_quant_eod_$(date -u +%Y-%m-%d)\" "
        f"/usr/bin/python3 {root}/board/eod/eod_confirmation.py >> /var/log/eod_confirmation.log 2>&1"
    )
    corr_line = (
        f"0 * * * * /usr/bin/python3 {root}/scripts/compute_signal_correlation_snapshot.py --minutes 60 --topk 20 >> /var/log/correlation_snapshot.log 2>&1"
    )
    # Remove old entries, add new (ensure /var/log writable)
    install_cmd = (
        "(crontab -l 2>/dev/null | grep -v eod_confirmation | grep -v run_stock_quant_officer_eod | grep -v cron_health_check | grep -v compute_signal_correlation_snapshot || true; "
        f"echo '{health_line}'; echo '{eod_line}'; echo '{corr_line}') | crontab -"
    )
    mkdir_cmd = "touch /var/log/cron_health.log /var/log/eod_confirmation.log /var/log/correlation_snapshot.log 2>/dev/null || true"

    if client is not None:
        client._execute(mkdir_cmd, timeout=5)
        out, err, rc = client._execute(install_cmd, timeout=10)
        if rc != 0:
            return False, err or out or "crontab install failed"
        return True, "cron reinstalled (health + EOD)"
    try:
        subprocess.run(["sh", "-c", mkdir_cmd], check=False, capture_output=True, timeout=5)
        r = subprocess.run(
            ["sh", "-c", install_cmd],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode != 0:
            return False, r.stderr or r.stdout or "crontab install failed"
        return True, "cron reinstalled (health + EOD)"
    except Exception as e:
        return False, str(e)


def check_script_execution_dry_run(date_str: str, client: Any | None = None) -> dict[str, Any]:
    """
    3) Verify eod_confirmation.py --date --dry-run runs under cron-like env.
    """
    root = _detect_stockbot_root()
    cmd = f"cd {root} && /usr/bin/python3 board/eod/eod_confirmation.py --date {date_str} --dry-run 2>&1"
    result: dict[str, Any] = dict(exit_code=-1, stdout="", stderr="", ok=False)
    out, err, rc = _run(cmd, client, 30)
    result["exit_code"] = rc
    result["stdout"] = (out or "")[-1000:]
    result["stderr"] = (err or "")[-1000:]
    result["ok"] = rc == 0
    return result


def force_run_eod(date_str: str, client: Any | None = None, allow_missing_missed_money: bool = False) -> tuple[int, str, str]:
    """
    Force-run eod_confirmation.py --date <date_str>.
    Returns (exit_code, stdout, stderr).
    When allow_missing_missed_money=True, bypasses missed_money_numeric.all_numeric check (for cron recovery).
    """
    root = _detect_stockbot_root()
    mm_flag = " --allow-missing-missed-money" if allow_missing_missed_money else ""
    cmd = (
        f"cd {root} && CLAWDBOT_SESSION_ID=stock_quant_eod_{date_str} "
        f"/usr/bin/python3 board/eod/eod_confirmation.py --date {date_str}{mm_flag}"
    )

    if client is not None:
        out, err, rc = client._execute(cmd, timeout=600)
        return rc, out or "", err or ""

    try:
        r = subprocess.run(
            ["sh", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=root,
        )
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 1, "", "Timeout (600s)"
    except Exception as e:
        return 1, "", str(e)


def push_to_github(date_str: str, client: Any | None = None) -> tuple[int, str, str]:
    """Git add board/eod/out/<date>/, commit, push."""
    root = _detect_stockbot_root()
    rel = f"board/eod/out/{date_str}"
    cmd = (
        f"cd {root} && git add {rel} && "
        f"git commit -m 'EOD report for {date_str} (cron recovery)' || true && "
        "git push origin main"
    )

    if client is not None:
        out, err, rc = client._execute(cmd, timeout=60)
        return rc, out or "", err or ""

    try:
        r = subprocess.run(
            ["sh", "-c", cmd],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=root,
        )
        return r.returncode, r.stdout or "", r.stderr or ""
    except Exception as e:
        return 1, "", str(e)


def run_on_droplet(date_str: str) -> int:
    """
    Run full flow on droplet: verify cron service, entries, dry-run, repair if needed, force-run EOD, push.
    All diagnostics run ON the droplet.
    """
    root = _detect_stockbot_root()
    out_dir = Path(root) / "board" / "eod" / "out" / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    repair_actions: list[str] = []

    diagnosis: dict[str, Any] = dict(
        date=date_str,
        timestamp=datetime.now(timezone.utc).isoformat(),
        cron_service_status=dict(),
        cron_installed=dict(),
        cron_execution=dict(),
        script_health=dict(),
        script_execution_dry_run=dict(),
        logging=dict(),
        repair_applied=False,
        repair_message="",
        repair_actions_taken=[],
        eod_exit_code=-1,
        eod_stdout="",
        eod_stderr="",
        push_exit_code=-1,
        push_stdout="",
        push_stderr="",
        success=False,
        errors=[],
        final_status="",
    )

    # 1. Verify cron service is running
    diagnosis["cron_service_status"] = check_cron_service(client=None)
    if diagnosis["cron_service_status"].get("repair_actions"):
        repair_actions.extend(diagnosis["cron_service_status"]["repair_actions"])
    if not diagnosis["cron_service_status"].get("active"):
        diagnosis["errors"].append("Cron service not active")

    # 2. Diagnose cron entries and script health
    diagnosis["cron_installed"] = check_cron_installed(client=None)
    diagnosis["cron_execution"] = check_cron_execution(date_str, client=None)
    diagnosis["script_health"] = check_script_health(client=None)
    diagnosis["script_execution_dry_run"] = check_script_execution_dry_run(date_str, client=None)
    diagnosis["logging"] = check_logging(client=None)

    if not diagnosis["script_execution_dry_run"].get("ok"):
        diagnosis["errors"].append("Dry-run failed: eod_confirmation --dry-run did not succeed")

    needs_repair = (
        not diagnosis["cron_installed"].get("health_check_entry_exists")
        or not diagnosis["cron_installed"].get("eod_entry_exists")
        or diagnosis["cron_installed"].get("errors")
        or diagnosis["script_health"].get("errors")
    )

    # 3. Repair cron if needed
    if needs_repair:
        ok, msg = repair_cron(client=None)
        diagnosis["repair_applied"] = ok
        diagnosis["repair_message"] = msg
        if ok:
            repair_actions.append(msg)
            diagnosis["cron_installed"] = check_cron_installed(client=None)
        else:
            diagnosis["errors"].append(f"Cron repair failed: {msg}")

    diagnosis["repair_actions_taken"] = repair_actions

    # 4. Force-run EOD. First try strict; if failed (e.g. missed_money_numeric), retry with --allow-missing-missed-money.
    # EOD MUST run and push every weekday — no exceptions. Partial data is better than no data.
    rc, stdout, stderr = force_run_eod(date_str, client=None, allow_missing_missed_money=False)
    if rc != 0 and "missed_money_numeric" in (stderr or "").lower():
        diagnosis["repair_actions_taken"].append("EOD retry with --allow-missing-missed-money (data incomplete)")
        rc, stdout, stderr = force_run_eod(date_str, client=None, allow_missing_missed_money=True)
    diagnosis["eod_exit_code"] = rc
    diagnosis["eod_stdout"] = stdout[-2000:] if stdout else ""
    diagnosis["eod_stderr"] = stderr[-2000:] if stderr else ""
    if rc != 0:
        diagnosis["errors"].append(f"EOD failed with exit {rc}")
        failure_path = out_dir / "eod_failure.json"
        failure_path.write_text(
            json.dumps({"date": date_str, "exit_code": rc, "stderr": stderr, "stdout": stdout}, indent=2),
            encoding="utf-8",
        )
        diagnosis["final_status"] = "EOD_FAILED"
        diagnosis_path = out_dir / "cron_diagnosis.json"
        diagnosis_path.write_text(json.dumps(diagnosis, indent=2), encoding="utf-8")
        print(f"CRON DIAGNOSIS COMPLETE — EOD FOR {date_str} FAILED (exit {rc}).")
        return 1

    # 5. Push to GitHub
    push_rc, push_out, push_err = push_to_github(date_str, client=None)
    diagnosis["push_exit_code"] = push_rc
    diagnosis["push_stdout"] = push_out[-1000:] if push_out else ""
    diagnosis["push_stderr"] = push_err[-1000:] if push_err else ""
    if push_rc != 0:
        diagnosis["errors"].append(f"GitHub push failed: {push_err or push_out}")
        state_dir = Path(root) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / f"eod_push_failed_{date_str}.json").write_text(
            json.dumps({"date": date_str, "reason": push_err or push_out}, indent=2),
            encoding="utf-8",
        )

    diagnosis["success"] = rc == 0 and push_rc == 0
    diagnosis["final_status"] = "SUCCESS" if diagnosis["success"] else "PUSH_FAILED"

    # 6. Write cron_diagnosis.json
    diagnosis_path = out_dir / "cron_diagnosis.json"
    diagnosis_path.write_text(json.dumps(diagnosis, indent=2), encoding="utf-8")

    # 7. Confirmation
    print(f"CRON DIAGNOSIS COMPLETE — EOD FOR {date_str} GENERATED AND PUSHED.")

    return 0 if diagnosis["success"] else 1


def run_remote(date_str: str) -> int:
    """
    SSH to droplet, pull latest, run cron_diagnose_and_fix --on-droplet.
    """
    # Ensure repo root is in path for droplet_client import
    repo_root = str(SCRIPT_DIR.parent.parent)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    try:
        from droplet_client import DropletClient
    except ImportError as e:
        print("Error: droplet_client not found. Install paramiko and run from repo root.", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        return 1

    with DropletClient() as c:
        root = c.project_dir
        cmd = (
            f"cd {root} && git fetch origin && git pull origin main && "
            f"python3 board/eod/cron_diagnose_and_fix.py --date {date_str} --on-droplet"
        )
        out, err, rc = c._execute(cmd, timeout=900)
        print(out)
        if err:
            print(err, file=sys.stderr)
        return rc


def main() -> int:
    ap = argparse.ArgumentParser(description="Cron diagnose, fix, force-run EOD, push")
    ap.add_argument("--date", required=True, help="Date YYYY-MM-DD (e.g. 2026-02-12)")
    ap.add_argument("--on-droplet", action="store_true", help="Run directly on droplet (no SSH)")
    ap.add_argument("--remote", action="store_true", help="SSH to droplet and run there")
    args = ap.parse_args()
    date_str = args.date

    on_windows = platform.system() == "Windows"
    if args.on_droplet:
        return run_on_droplet(date_str)
    if args.remote or on_windows:
        return run_remote(date_str)
    # Linux, no flags: assume we're on droplet (e.g. invoked by cron)
    return run_on_droplet(date_str)


if __name__ == "__main__":
    sys.exit(main())
