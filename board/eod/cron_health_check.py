#!/usr/bin/env python3
"""
Cron health check: runs daily BEFORE EOD confirmation (e.g. 21:25 UTC).
Verifies cron entry exists, last-run timestamp within 24h, eod_confirmation.py
executable, Python path valid. If any check fails, auto-repair cron and log
to state/cron_health_failures.json.

Cron entry (runs 10 min before EOD at 21:20 UTC):
    20 21 * * 1-5 /usr/bin/python3 /root/stock-bot/board/eod/cron_health_check.py

Run from repo root on droplet.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CANDIDATE_ROOTS = ["/root/stock-bot-current", "/root/stock-bot"]


def _detect_root() -> str:
    for root in CANDIDATE_ROOTS:
        p = Path(root)
        if (p / "scripts").is_dir() and (p / "board" / "eod" / "eod_confirmation.py").exists():
            return root
    if (REPO_ROOT / "scripts").is_dir():
        return str(REPO_ROOT)
    return "/root/stock-bot"


def check_cron_entry_exists() -> tuple[bool, str]:
    """Verify EOD cron entry exists in crontab."""
    try:
        r = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        crontab = r.stdout or ""
        has_eod = "eod_confirmation" in crontab or "run_stock_quant_officer_eod" in crontab
        return has_eod, crontab if not has_eod else "OK"
    except FileNotFoundError:
        return False, "crontab not found (Windows?)"
    except Exception as e:
        return False, str(e)


def check_last_run_within_24h(root: str) -> tuple[bool, str]:
    """Check last EOD run timestamp is within 24 hours."""
    log_path = Path(root) / "logs" / "cron_eod.log"
    if not log_path.exists():
        return False, f"Log not found: {log_path}"

    try:
        mtime = log_path.stat().st_mtime
        age_sec = (datetime.now(timezone.utc).timestamp() - mtime)
        within_24h = age_sec < 24 * 3600
        return within_24h, f"last_modified={age_sec:.0f}s ago" if not within_24h else "OK"
    except Exception as e:
        return False, str(e)


def check_eod_executable(root: str) -> tuple[bool, str]:
    """Confirm eod_confirmation.py is executable."""
    p = Path(root) / "board" / "eod" / "eod_confirmation.py"
    if not p.exists():
        return False, f"missing: {p}"
    if platform.system() != "Windows":
        import stat
        if not (p.stat().st_mode & stat.S_IXUSR):
            return False, "not executable"
    return True, "OK"


def check_python_path() -> tuple[bool, str]:
    """Python3 is available."""
    try:
        r = subprocess.run(
            ["/usr/bin/python3", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return r.returncode == 0, "OK" if r.returncode == 0 else (r.stderr or r.stdout or "fail")
    except FileNotFoundError:
        try:
            r = subprocess.run(["python3", "--version"], capture_output=True, text=True, timeout=5)
            return r.returncode == 0, "OK" if r.returncode == 0 else "python3 not found"
        except Exception:
            return False, "python3 not found"
    except Exception as e:
        return False, str(e)


def repair_cron(root: str) -> tuple[bool, str]:
    """Reinstall EOD cron entry."""
    cron_line = (
        f"30 21 * * 1-5 cd {root} && "
        "CLAWDBOT_SESSION_ID=\"stock_quant_eod_$(date -u +%Y-%m-%d)\" "
        f"/usr/bin/python3 {root}/board/eod/eod_confirmation.py >> {root}/logs/cron_eod.log 2>&1"
    )
    install = (
        f"(crontab -l 2>/dev/null | grep -v eod_confirmation | grep -v run_stock_quant_officer_eod || true; "
        f"echo '{cron_line}') | crontab -"
    )
    try:
        Path(root).joinpath("logs").mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["sh", "-c", install], capture_output=True, text=True, timeout=10)
        return r.returncode == 0, r.stderr or r.stdout or ("OK" if r.returncode == 0 else "failed")
    except Exception as e:
        return False, str(e)


def main() -> int:
    if platform.system() == "Windows":
        print("cron_health_check: skipped (Windows)")
        return 0

    root = _detect_root()
    state_dir = Path(root) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    failures_path = state_dir / "cron_health_failures.json"

    results: list[dict] = []
    all_ok = True

    ok, msg = check_cron_entry_exists()
    results.append({"check": "cron_entry", "ok": ok, "message": msg})
    if not ok:
        all_ok = False

    ok2, msg2 = check_last_run_within_24h(root)
    results.append({"check": "last_run_24h", "ok": ok2, "message": msg2})
    if not ok2:
        all_ok = False

    ok3, msg3 = check_eod_executable(root)
    results.append({"check": "eod_executable", "ok": ok3, "message": msg3})
    if not ok3:
        all_ok = False

    ok4, msg4 = check_python_path()
    results.append({"check": "python_path", "ok": ok4, "message": msg4})
    if not ok4:
        all_ok = False

    repair_applied = False
    if not all_ok:
        repaired, repair_msg = repair_cron(root)
        repair_applied = repaired
        results.append({"check": "repair", "ok": repaired, "message": repair_msg})

    failure_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "root": root,
        "all_ok": all_ok,
        "repair_applied": repair_applied,
        "results": results,
    }

    if not all_ok:
        try:
            existing: list = []
            if failures_path.exists():
                try:
                    existing = json.loads(failures_path.read_text(encoding="utf-8"))
                    if not isinstance(existing, list):
                        existing = [existing]
                except Exception:
                    existing = []
            existing.append(failure_record)
            failures_path.write_text(json.dumps(existing[-50:], indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Could not write {failures_path}: {e}", file=sys.stderr)

    return 0 if all_ok else 0  # Always exit 0 so cron health check doesn't break the chain


if __name__ == "__main__":
    sys.exit(main())
