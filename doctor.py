#!/usr/bin/env python3
"""
Doctor - Self-healing operations loop (one-shot, systemd-timer friendly)

Design goals:
- Stdlib-only (works even if venv is broken)
- Fast: run every 60s via systemd timer
- Safe: in LIVE mode, prefer freezing over risky auto-fixes
- Actionable: logs every remediation to data/doctor_actions.jsonl

What it does:
- Checks systemd service status
- Calls /health and evaluates critical checks
- Performs safe remediations (restart service, rebuild venv, truncate huge logs)
"""

from __future__ import annotations

import json
import os
import sys
import time
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


REPO_DIR = Path(os.getenv("REPO_DIR", Path(__file__).resolve().parent))
DATA_DIR = REPO_DIR / "data"
LOGS_DIR = REPO_DIR / "logs"
STATE_DIR = REPO_DIR / "state"

SERVICE_NAME = os.getenv("BOT_SERVICE_NAME", "trading-bot")
HEALTH_URL = os.getenv("BOT_HEALTH_URL", "http://127.0.0.1:8080/health")
TRADING_MODE = (os.getenv("TRADING_MODE", "PAPER") or "PAPER").upper()

# Frequencies/thresholds (conservative defaults)
MAX_LOG_FILE_MB = float(os.getenv("DOCTOR_MAX_LOG_MB", "25"))
TRUNCATE_TO_LINES = int(os.getenv("DOCTOR_TRUNCATE_TO_LINES", "3000"))
VENV_HEALTH_IMPORTS = os.getenv("DOCTOR_VENV_IMPORTS", "requests,flask,alpaca_trade_api").split(",")
MAX_CONSEC_FAILS_BEFORE_FREEZE = int(os.getenv("DOCTOR_MAX_FAILS_BEFORE_FREEZE", "5"))

STATE_FILE = STATE_DIR / "doctor_state.json"
AUDIT_FILE = DATA_DIR / "doctor_actions.jsonl"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record["_ts"] = int(time.time())
    record["_dt"] = _utc_iso()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _run(cmd: list[str], timeout: int = 30) -> Tuple[int, str]:
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return int(p.returncode), (p.stdout or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"
    except Exception as e:
        return 127, str(e)


def _load_state() -> Dict[str, Any]:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
    except Exception:
        pass
    return {"consecutive_failures": 0, "last_action": None, "last_ok_ts": None}


def _save_state(state: Dict[str, Any]) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception:
        pass


def _systemctl(*args: str, timeout: int = 30) -> Tuple[int, str]:
    return _run(["systemctl", *args], timeout=timeout)


def _service_active() -> bool:
    code, _ = _systemctl("is-active", "--quiet", SERVICE_NAME)
    return code == 0


def _restart_service(reason: str) -> bool:
    _append_jsonl(AUDIT_FILE, {"event": "RESTART_SERVICE", "service": SERVICE_NAME, "reason": reason})
    _systemctl("restart", SERVICE_NAME, timeout=60)
    return _service_active()


def _freeze_trading(reason: str) -> None:
    """
    Write a freeze file that main.py's monitoring guards will respect.
    """
    freeze_path = STATE_DIR / "governor_freezes.json"
    freezes = {}
    if freeze_path.exists():
        try:
            freezes = json.loads(freeze_path.read_text())
        except Exception:
            freezes = {}
    freezes["production_freeze"] = True
    freezes["doctor_freeze"] = True
    freeze_path.write_text(json.dumps(freezes, indent=2))
    _append_jsonl(AUDIT_FILE, {"event": "FREEZE_SET", "reason": reason, "path": str(freeze_path)})


def _fetch_health() -> Tuple[bool, Optional[Dict[str, Any]], str]:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=10) as resp:
            raw = resp.read().decode("utf-8", "ignore")
            return True, json.loads(raw), ""
    except urllib.error.URLError as e:
        return False, None, f"url_error:{e}"
    except Exception as e:
        return False, None, f"error:{e}"


def _truncate_large_logs() -> int:
    """
    Prevent disk fill by truncating huge log/jsonl files.
    """
    patterns = [
        LOGS_DIR,
        DATA_DIR,
        STATE_DIR,
    ]
    truncated = 0
    for base in patterns:
        if not base.exists():
            continue
        for p in base.rglob("*.jsonl"):
            try:
                size_mb = p.stat().st_size / (1024 * 1024)
                if size_mb <= MAX_LOG_FILE_MB:
                    continue
                lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                p.write_text("\n".join(lines[-TRUNCATE_TO_LINES:]) + "\n", encoding="utf-8")
                truncated += 1
            except Exception:
                continue
    if truncated:
        _append_jsonl(AUDIT_FILE, {"event": "LOG_TRUNCATE", "count": truncated, "max_mb": MAX_LOG_FILE_MB})
    return truncated


def _venv_import_check() -> bool:
    vpy = REPO_DIR / "venv" / "bin" / "python"
    if not vpy.exists():
        return False
    imports = ",".join([x.strip() for x in VENV_HEALTH_IMPORTS if x.strip()])
    code, out = _run([str(vpy), "-c", f"import {imports}"], timeout=15)
    if code == 0:
        return True
    _append_jsonl(AUDIT_FILE, {"event": "VENV_IMPORT_FAIL", "code": code, "out": out[:500]})
    return False


def _rebuild_venv() -> bool:
    script = REPO_DIR / "scripts" / "bootstrap_venv.sh"
    if not script.exists():
        _append_jsonl(AUDIT_FILE, {"event": "VENV_REBUILD_FAIL", "reason": "bootstrap_script_missing"})
        return False
    _append_jsonl(AUDIT_FILE, {"event": "VENV_REBUILD_START"})
    code, out = _run([str(script), str(REPO_DIR)], timeout=600)
    _append_jsonl(AUDIT_FILE, {"event": "VENV_REBUILD_DONE", "code": code, "out": out[:500]})
    return code == 0


def run_once() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    state = _load_state()

    # Always do log hygiene first (safe)
    _truncate_large_logs()

    # Ensure service is running
    if not _service_active():
        ok = _restart_service("service_inactive")
        state["last_action"] = "restart_service_inactive"
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + (0 if ok else 1)
        _save_state(state)
        return 0 if ok else 2

    ok, payload, err = _fetch_health()
    if not ok or not payload:
        # If health endpoint is unreachable, restart.
        rst_ok = _restart_service(f"health_unreachable:{err}")
        state["last_action"] = "restart_health_unreachable"
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + (0 if rst_ok else 1)
        _save_state(state)
        return 0 if rst_ok else 2

    health = payload.get("health_checks") or {}
    overall = bool(health.get("overall_healthy", True))
    checks = health.get("checks") or []

    if overall:
        state["consecutive_failures"] = 0
        state["last_ok_ts"] = int(time.time())
        state["last_action"] = "ok"
        _save_state(state)
        return 0

    # Not overall healthy: decide remediation.
    state["consecutive_failures"] = int(state.get("consecutive_failures", 0)) + 1

    # Extract critical failing checks
    critical_bad = [c for c in checks if str(c.get("severity")).upper() == "CRITICAL" and str(c.get("status")) != "HEALTHY"]

    _append_jsonl(AUDIT_FILE, {
        "event": "HEALTH_DEGRADED",
        "overall_healthy": overall,
        "critical_bad": [c.get("name") for c in critical_bad],
        "consecutive_failures": state["consecutive_failures"],
        "trading_mode": TRADING_MODE,
    })

    # LIVE mode safety: after repeated critical failures, freeze rather than churn.
    if TRADING_MODE == "LIVE" and state["consecutive_failures"] >= MAX_CONSEC_FAILS_BEFORE_FREEZE and critical_bad:
        _freeze_trading("doctor_critical_failures_live")
        state["last_action"] = "freeze_live"
        _save_state(state)
        return 3

    # PAPER mode (or mild LIVE failures): attempt safe remediation
    # 1) Ensure venv is sane; rebuild if not.
    if not _venv_import_check():
        rebuilt = _rebuild_venv()
        if rebuilt:
            _restart_service("venv_rebuilt")
        state["last_action"] = "venv_rebuild" if rebuilt else "venv_rebuild_failed"
        _save_state(state)
        return 0 if rebuilt else 2

    # 2) Restart service if critical checks are bad (cache/broker/position tracking)
    if critical_bad:
        rst_ok = _restart_service("critical_checks_unhealthy")
        state["last_action"] = "restart_critical_unhealthy"
        _save_state(state)
        return 0 if rst_ok else 2

    # 3) Non-critical issues: do nothing (avoid churn)
    state["last_action"] = "degraded_noop"
    _save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(run_once())

