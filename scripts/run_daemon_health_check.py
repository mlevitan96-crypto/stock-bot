#!/usr/bin/env python3
"""
UW Flow Daemon Health Sentinel (watchdog)
========================================

Contract:
- Additive, v1-safe (does not affect trading logic).
- Fully observable: writes state + logs structured system events.
- Supports mock mode for regression/local dev (no systemctl, no /proc required).

Outputs:
- state/uw_daemon_health_state.json
- logs/system_events.jsonl (event_type: uw_daemon_health_ok|warning|critical, plus detail events)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


SERVICE_NAME = "uw-flow-daemon.service"
LOCK_PATH = Path("state/uw_flow_daemon.lock")
OUT_STATE = Path("state/uw_daemon_health_state.json")
FLOW_CACHE = Path("data/uw_flow_cache.json")  # canonical v1 UW flow cache output


try:
    from utils.system_events import log_system_event
except Exception:  # pragma: no cover
    def log_system_event(*args: Any, **kwargs: Any) -> None:  # type: ignore
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path: Path, doc: Dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        return


def _run(cmd: list[str], *, timeout: int = 5) -> Tuple[bool, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "") + "\n" + (p.stderr or "")
        return p.returncode == 0, out.strip()
    except Exception as e:
        return False, str(e)


def _systemctl_show(service: str) -> Dict[str, str]:
    ok, out = _run(
        [
            "systemctl",
            "show",
            service,
            "--no-page",
            "-p",
            "ExecMainPID",
            "-p",
            "NRestarts",
            "-p",
            "ActiveState",
            "-p",
            "SubState",
            "-p",
            "Result",
        ],
        timeout=5,
    )
    if not ok:
        return {}
    d: Dict[str, str] = {}
    for ln in out.splitlines():
        if "=" in ln:
            k, v = ln.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def _pid_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    # Linux procfs
    if os.name == "posix":
        return Path("/proc") .joinpath(str(pid)).exists()
    return False


def _parse_lock_file(path: Path) -> Tuple[Optional[int], str]:
    """
    Best-effort: uw_flow_daemon writes `pid=<pid> ts=<iso>` lines.
    Returns (pid, last_line).
    """
    if not path.exists():
        return None, ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        last = ""
        for ln in reversed(lines):
            if ln.strip():
                last = ln.strip()
                break
        if not last:
            return None, ""
        pid = None
        for tok in last.split():
            if tok.startswith("pid="):
                try:
                    pid = int(tok.split("=", 1)[1])
                except Exception:
                    pid = None
        return pid, last
    except Exception:
        return None, ""


def _lock_is_held_by_other_process(path: Path) -> Optional[bool]:
    """
    Attempts to acquire the advisory lock.
    Returns:
    - True if lock appears held by another process
    - False if lock is free
    - None if not supported
    """
    if os.name != "posix":
        return None
    try:
        import fcntl  # type: ignore
    except Exception:
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fh = path.open("a+")
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            # We acquired it => not held.
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            return False
        except Exception:
            return True
        finally:
            try:
                fh.close()
            except Exception:
                pass
    except Exception:
        return None


def _file_age_sec(path: Path) -> Optional[float]:
    try:
        return float(time.time() - path.stat().st_mtime)
    except Exception:
        return None


def _count_endpoint_errors(window_sec: int) -> Dict[str, int]:
    """
    Scan logs/system_events.jsonl for recent endpoint/rate-limit issues.
    """
    p = Path("logs/system_events.jsonl")
    if not p.exists():
        return {"uw_rate_limit_block": 0, "uw_invalid_endpoint_attempt": 0}
    try:
        tail = p.read_text(encoding="utf-8", errors="replace")[-200000:]
    except Exception:
        return {"uw_rate_limit_block": 0, "uw_invalid_endpoint_attempt": 0}
    now = time.time()
    counts = {"uw_rate_limit_block": 0, "uw_invalid_endpoint_attempt": 0}
    for ln in tail.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
        except Exception:
            continue
        if not isinstance(rec, dict):
            continue
        et = str(rec.get("event_type", "") or "")
        if et not in counts:
            continue
        ts = str(rec.get("timestamp", "") or "")
        # timestamp is ISO; best-effort: if too hard to parse, just count (safe)
        if window_sec <= 0:
            counts[et] += 1
            continue
        try:
            # parse "2026-01-20T23:..." (UTC)
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            age = now - dt.timestamp()
            if age <= float(window_sec):
                counts[et] += 1
        except Exception:
            counts[et] += 1
    return counts


def _restart_storm_snapshot(*, service: str, max_lines: int = 2000) -> Dict[str, Any]:
    """
    Additive diagnostic only.

    Detects repeated 'Another instance is already running' patterns in journal output,
    which indicates a lock-contention restart storm.
    """
    if os.name != "posix":
        return {"available": False, "count": 0, "detected": False}
    ok, out = _run(
        ["journalctl", "-u", service, "--no-pager", "--output=short-iso", "-n", str(int(max_lines))],
        timeout=10,
    )
    if not ok or not out:
        return {"available": False, "count": 0, "detected": False}
    lines = out.splitlines()
    needle = "Another instance is already running"
    count = sum(1 for ln in lines if needle in ln)
    # threshold is intentionally conservative; this is only an observability flag.
    detected = bool(count > 50)
    return {"available": True, "count": int(count), "detected": bool(detected)}


def _mock_snapshot(scenario: str) -> Dict[str, Any]:
    # Deterministic snapshots for regression.
    base = {
        "exec_main_pid": 12345,
        "pid_exists": True,
        "active_state": "active",
        "sub_state": "running",
        "n_restarts": 0,
        "lock_file_exists": True,
        "lock_pid": 12345,
        "lock_held": True,
        "flow_cache_exists": True,
        "flow_cache_age_sec": 60.0,
        "endpoint_errors": {"uw_rate_limit_block": 0, "uw_invalid_endpoint_attempt": 0},
        "restart_storm": {"available": True, "count": 0, "detected": False},
    }
    s = (scenario or "healthy").strip().lower()
    if s == "missing_pid":
        base["exec_main_pid"] = 0
        base["pid_exists"] = False
    elif s == "stale_lock":
        base["lock_pid"] = 99999
        base["lock_held"] = False
    elif s == "stale_poll":
        base["flow_cache_age_sec"] = 3600.0
    elif s == "crash_loop":
        base["n_restarts"] = 25
        base["active_state"] = "activating"
        base["sub_state"] = "auto-restart"
    elif s == "endpoint_errors":
        base["endpoint_errors"] = {"uw_rate_limit_block": 50, "uw_invalid_endpoint_attempt": 5}
    elif s == "restart_storm":
        base["restart_storm"] = {"available": True, "count": 120, "detected": True}
    return base


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="Mock mode (no systemctl/proc inspection)")
    ap.add_argument("--heal", action="store_true", help="Attempt safe restart on critical failures")
    ap.add_argument("--max-poll-age-sec", type=int, default=600, help="Polling freshness threshold (default 10m)")
    ap.add_argument("--crash-loop-restarts", type=int, default=10, help="Restart count threshold for crash loop")
    ap.add_argument("--endpoint-error-window-sec", type=int, default=900, help="Window for endpoint error spike detection")
    ap.add_argument("--endpoint-error-threshold", type=int, default=20, help="Count threshold for endpoint error spike")
    ap.add_argument("--nonfatal", action="store_true", help="Always exit 0 (still writes state)")
    args = ap.parse_args()

    mock = bool(args.mock) or str(os.getenv("DAEMON_HEALTH_MOCK", "")).strip() in ("1", "true", "TRUE", "yes", "YES")
    scenario = str(os.getenv("DAEMON_HEALTH_SCENARIO", "")).strip()

    # Collect
    if mock:
        snap = _mock_snapshot(scenario or "healthy")
    else:
        show = _systemctl_show(SERVICE_NAME)
        pid = int(show.get("ExecMainPID", "0") or "0")
        n_restarts = int(show.get("NRestarts", "0") or "0")
        active_state = show.get("ActiveState", "")
        sub_state = show.get("SubState", "")
        result = show.get("Result", "")

        lock_pid, lock_line = _parse_lock_file(LOCK_PATH)
        lock_held = _lock_is_held_by_other_process(LOCK_PATH)
        flow_age = _file_age_sec(FLOW_CACHE)
        endpoint_errs = _count_endpoint_errors(int(args.endpoint_error_window_sec))
        restart_storm = _restart_storm_snapshot(service=SERVICE_NAME, max_lines=2000)

        snap = {
            "exec_main_pid": pid,
            "pid_exists": _pid_exists(pid),
            "active_state": active_state,
            "sub_state": sub_state,
            "result": result,
            "n_restarts": n_restarts,
            "lock_file_exists": LOCK_PATH.exists(),
            "lock_pid": lock_pid,
            "lock_line": lock_line,
            "lock_held": lock_held,
            "flow_cache_exists": FLOW_CACHE.exists(),
            "flow_cache_age_sec": flow_age,
            "endpoint_errors": endpoint_errs,
            "restart_storm": restart_storm,
        }

    # Evaluate
    pid_ok = bool(snap.get("exec_main_pid", 0)) and bool(snap.get("pid_exists", False))
    lock_ok = bool(snap.get("lock_file_exists", False)) and bool(snap.get("lock_held", True))
    if pid_ok and isinstance(snap.get("lock_pid"), int) and int(snap["lock_pid"]) > 0:
        lock_ok = lock_ok and (int(snap["lock_pid"]) == int(snap.get("exec_main_pid", 0)))
    poll_age = snap.get("flow_cache_age_sec")
    poll_fresh = (poll_age is not None) and (float(poll_age) <= float(args.max_poll_age_sec))
    # Crash loop detection:
    # - Treat "failed"/"auto-restart"/non-active as crash-loop (current condition).
    # - Do NOT treat lifetime NRestarts as crash-loop when service is stable/running;
    #   instead, surface it as a warning detail so preopen readiness doesn't get stuck "critical" forever.
    astate = str(snap.get("active_state", "") or "").lower()
    sstate = str(snap.get("sub_state", "") or "").lower()
    crash_loop_now = (astate != "active") or (sstate in ("failed", "auto-restart", "dead"))
    crash_loop = bool(crash_loop_now)
    high_restart_count = int(snap.get("n_restarts", 0) or 0) > int(args.crash_loop_restarts)
    endpoint_err = snap.get("endpoint_errors") if isinstance(snap.get("endpoint_errors"), dict) else {}
    endpoint_errors = (int(endpoint_err.get("uw_rate_limit_block", 0) or 0) + int(endpoint_err.get("uw_invalid_endpoint_attempt", 0) or 0)) >= int(args.endpoint_error_threshold)
    restart_storm_info = snap.get("restart_storm") if isinstance(snap.get("restart_storm"), dict) else {}
    restart_storm_detected = bool(restart_storm_info.get("detected", False))

    status = "healthy"
    details: Dict[str, Any] = {}

    # Detail events (fine-grained)
    if not pid_ok:
        details["pid_issue"] = True
        try:
            log_system_event(subsystem="uw_poll", event_type="uw_daemon_pid_missing", severity="ERROR", details={"exec_main_pid": snap.get("exec_main_pid"), "active_state": snap.get("active_state"), "sub_state": snap.get("sub_state")})
        except Exception:
            pass
        status = "critical"
    if not lock_ok:
        details["lock_issue"] = True
        try:
            log_system_event(subsystem="uw_poll", event_type="uw_daemon_lock_stale", severity="ERROR", details={"lock_pid": snap.get("lock_pid"), "exec_main_pid": snap.get("exec_main_pid"), "lock_held": snap.get("lock_held")})
        except Exception:
            pass
        status = "critical"
    if not poll_fresh:
        details["poll_issue"] = True
        try:
            log_system_event(subsystem="uw_poll", event_type="uw_daemon_poll_stale", severity="WARN", details={"flow_cache_age_sec": snap.get("flow_cache_age_sec"), "max_poll_age_sec": int(args.max_poll_age_sec)})
        except Exception:
            pass
        if status != "critical":
            status = "warning"
    if crash_loop:
        details["crash_loop"] = True
        try:
            log_system_event(subsystem="uw_poll", event_type="uw_daemon_crash_loop", severity="ERROR", details={"n_restarts": int(snap.get("n_restarts", 0) or 0), "threshold": int(args.crash_loop_restarts), "active_state": snap.get("active_state"), "sub_state": snap.get("sub_state")})
        except Exception:
            pass
        status = "critical"
    elif high_restart_count:
        details["high_restart_count"] = True
        try:
            log_system_event(
                subsystem="uw_poll",
                event_type="uw_daemon_high_restart_count",
                severity="WARN",
                details={"n_restarts": int(snap.get("n_restarts", 0) or 0), "threshold": int(args.crash_loop_restarts), "active_state": snap.get("active_state"), "sub_state": snap.get("sub_state")},
            )
        except Exception:
            pass
        if status == "healthy":
            status = "warning"
    if endpoint_errors:
        details["endpoint_errors"] = True
        try:
            log_system_event(subsystem="uw_poll", event_type="uw_daemon_endpoint_errors", severity="WARN", details={"counts": endpoint_err, "window_sec": int(args.endpoint_error_window_sec)})
        except Exception:
            pass
        if status == "healthy":
            status = "warning"
    if restart_storm_detected:
        details["restart_storm"] = True
        try:
            log_system_event(
                subsystem="uw_poll",
                event_type="uw_daemon_restart_storm",
                severity="WARN",
                details={"count": int(restart_storm_info.get("count", 0) or 0)},
            )
        except Exception:
            pass
        if status == "healthy":
            status = "warning"

    # Optional self-heal (safe restart)
    self_heal: Dict[str, Any] = {"attempted": False}
    if bool(args.heal) and status == "critical" and not mock and os.name == "posix":
        self_heal["attempted"] = True
        try:
            log_system_event(subsystem="uw_poll", event_type="uw_daemon_self_heal_attempt", severity="WARN", details={"service": SERVICE_NAME})
        except Exception:
            pass
        ok, out = _run(["systemctl", "restart", SERVICE_NAME], timeout=10)
        self_heal["success"] = bool(ok)
        self_heal["output"] = (out or "")[-800:]
        try:
            log_system_event(
                subsystem="uw_poll",
                event_type=("uw_daemon_self_heal_success" if ok else "uw_daemon_self_heal_failed"),
                severity=("INFO" if ok else "ERROR"),
                details={"service": SERVICE_NAME, "output": self_heal["output"]},
            )
        except Exception:
            pass

    # Summary event
    try:
        if status == "healthy":
            log_system_event(subsystem="uw_poll", event_type="uw_daemon_health_ok", severity="INFO", details={"service": SERVICE_NAME})
        elif status == "warning":
            log_system_event(subsystem="uw_poll", event_type="uw_daemon_health_warning", severity="WARN", details={"service": SERVICE_NAME, "details": details})
        else:
            log_system_event(subsystem="uw_poll", event_type="uw_daemon_health_critical", severity="ERROR", details={"service": SERVICE_NAME, "details": details})
    except Exception:
        pass

    doc = {
        "timestamp": _now_iso(),
        "pid_ok": bool(pid_ok),
        "lock_ok": bool(lock_ok),
        "poll_fresh": bool(poll_fresh),
        "crash_loop": bool(crash_loop),
        "endpoint_errors": bool(endpoint_errors),
        "restart_storm_detected": bool(restart_storm_detected),
        "status": str(status),
        "details": {
            "service": SERVICE_NAME,
            "exec_main_pid": snap.get("exec_main_pid"),
            "active_state": snap.get("active_state"),
            "sub_state": snap.get("sub_state"),
            "n_restarts": snap.get("n_restarts"),
            "lock_file": str(LOCK_PATH),
            "lock_pid": snap.get("lock_pid"),
            "lock_held": snap.get("lock_held"),
            "flow_cache": str(FLOW_CACHE),
            "flow_cache_age_sec": snap.get("flow_cache_age_sec"),
            "endpoint_error_counts": snap.get("endpoint_errors"),
            "restart_storm": snap.get("restart_storm"),
            "self_heal": self_heal,
            "mock": bool(mock),
            "mock_scenario": str(scenario or ""),
        },
    }

    _atomic_write(OUT_STATE, doc)
    print(str(OUT_STATE))

    if bool(args.nonfatal):
        return 0
    # default: do not fail execution pipelines; this is a sentinel.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

