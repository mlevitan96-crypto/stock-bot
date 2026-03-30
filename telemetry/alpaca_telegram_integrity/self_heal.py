"""Safe, reversible droplet self-heal hooks (no trading engine restart)."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List


def ensure_directories(root: Path) -> List[str]:
    paths = [
        root / "logs",
        root / "state",
        root / "reports",
        root / "reports" / "daily",
    ]
    done: List[str] = []
    for p in paths:
        try:
            p.mkdir(parents=True, exist_ok=True)
            done.append(str(p.relative_to(root)))
        except OSError as e:
            done.append(f"{p}:mkdir_failed:{e}")
    return done


def _systemctl(*args: str, timeout: int = 60) -> str:
    try:
        r = subprocess.run(
            ["systemctl", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (r.stdout or "") + (r.stderr or "")
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        return f"systemctl_error:{e}"


def restart_if_failed_postclose() -> str:
    """Read-only post-close job only; safe to try-restart when failed."""
    out = _systemctl("is-failed", "alpaca-postclose-deepdive.service")
    if "failed" not in out and "active" not in out:
        return "postclose_status_unknown"
    if "failed" in out:
        return _systemctl("try-restart", "alpaca-postclose-deepdive.service") or "postclose_try_restart_sent"
    return "postclose_not_failed"


def run_self_heal(cfg: Dict[str, Any], root: Path) -> Dict[str, Any]:
    sh = cfg.get("self_heal") or {}
    report: Dict[str, Any] = {}
    if sh.get("ensure_log_dirs", True):
        report["mkdirs"] = ensure_directories(root)
    if sh.get("restart_failed_postclose_service", True) and Path("/proc").is_dir():
        report["postclose"] = restart_if_failed_postclose()
    return report
