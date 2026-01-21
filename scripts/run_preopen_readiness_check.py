#!/usr/bin/env python3
"""
Pre-open readiness check (shadow trading readiness)
==================================================

Validates:
- Intel state presence + freshness
- Daemon health not critical
- Regression passes (unless PREOPEN_SKIP_REGRESSION=1)

Logs:
- logs/system_events.jsonl: preopen_readiness_ok|preopen_readiness_failed
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from utils.system_events import log_system_event
except Exception:  # pragma: no cover
    def log_system_event(*args: Any, **kwargs: Any) -> None:  # type: ignore
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _age_sec(path: Path) -> Optional[float]:
    try:
        return float(time.time() - path.stat().st_mtime)
    except Exception:
        return None


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        import json
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _check_fresh(path: Path, max_age_sec: int) -> Tuple[bool, str]:
    if not path.exists():
        return False, "missing"
    age = _age_sec(path)
    if age is None:
        return False, "stat_failed"
    return age <= float(max_age_sec), f"age_sec={round(age,1)}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-min", type=int, default=240, help="Freshness window for pre-open (default 4h)")
    ap.add_argument("--allow-mock", action="store_true", help="Allow UW_MOCK=1 without failing readiness")
    args = ap.parse_args()

    max_age_sec = int(args.max_age_min) * 60
    mock = str(os.getenv("UW_MOCK", "")).strip() in ("1", "true", "TRUE", "yes", "YES")

    checks: Dict[str, Any] = {}
    ok = True

    # Universe (v2 preferred, v1 acceptable)
    u2 = Path("state/daily_universe_v2.json")
    u1 = Path("state/daily_universe.json")
    if u2.exists():
        ok_u, det = _check_fresh(u2, max_age_sec)
        checks["daily_universe_v2"] = {"ok": ok_u, "detail": det}
        ok = ok and ok_u
    else:
        ok_u, det = _check_fresh(u1, max_age_sec)
        checks["daily_universe_v1"] = {"ok": ok_u, "detail": det}
        ok = ok and ok_u

    # Premarket intel
    pm = Path("state/premarket_intel.json")
    ok_pm, det_pm = _check_fresh(pm, max_age_sec)
    checks["premarket_intel"] = {"ok": ok_pm, "detail": det_pm}
    ok = ok and ok_pm

    # Regime state
    rs = Path("state/regime_state.json")
    ok_rs, det_rs = _check_fresh(rs, max_age_sec)
    checks["regime_state"] = {"ok": ok_rs, "detail": det_rs}
    ok = ok and ok_rs

    # Daemon health
    dhp = Path("state/uw_daemon_health_state.json")
    ok_dh, det_dh = _check_fresh(dhp, max_age_sec)
    dh = _read_json(dhp) if dhp.exists() else {}
    dh_status = str(dh.get("status", "missing"))
    checks["uw_daemon_health_state"] = {"ok": ok_dh and (dh_status != "critical"), "detail": det_dh, "status": dh_status}
    ok = ok and ok_dh and (dh_status != "critical")

    # Regression pass (unless skipped)
    skip_reg = str(os.getenv("PREOPEN_SKIP_REGRESSION", "")).strip() in ("1", "true", "TRUE", "yes", "YES")
    if not skip_reg:
        try:
            p = subprocess.run([sys.executable, "scripts/run_regression_checks.py"], capture_output=True, text=True)
            checks["regression"] = {"ok": p.returncode == 0, "stdout_tail": (p.stdout or "")[-200:], "stderr_tail": (p.stderr or "")[-200:]}
            ok = ok and (p.returncode == 0)
        except Exception as e:
            checks["regression"] = {"ok": False, "error": str(e)}
            ok = False
    else:
        checks["regression"] = {"ok": True, "skipped": True}

    # Mock safety gate
    if mock and not bool(args.allow_mock):
        checks["mock_mode"] = {"ok": False, "detail": "UW_MOCK=1 not allowed without --allow-mock"}
        ok = False
    else:
        checks["mock_mode"] = {"ok": True, "detail": f"UW_MOCK={mock}"}

    event_type = "preopen_readiness_ok" if ok else "preopen_readiness_failed"
    sev = "INFO" if ok else "ERROR"
    try:
        log_system_event(
            subsystem="shadow",
            event_type=event_type,
            severity=sev,
            details={"ts": _now_iso(), "checks": checks},
        )
    except Exception:
        pass

    if ok:
        print("PREOPEN_READY")
        return 0
    print("PREOPEN_NOT_READY")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

