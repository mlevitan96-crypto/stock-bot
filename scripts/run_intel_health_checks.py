#!/usr/bin/env python3
"""
Intel health checks + self-healing (additive)
============================================

Outputs:
- state/intel_health_state.json

Checks:
- state freshness
- UW usage (from state/uw_usage_state.json)
- schema validity for key intel artifacts
- droplet sync completeness (local `droplet_sync/` folders)

Self-healing:
- Optional (`--heal`): re-run safe generators when missing/stale.
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
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.uw_intel_schema import (
    validate_core_universe,
    validate_daily_universe,
    validate_daily_universe_v2,
    validate_intel_health_state,
    validate_postmarket_intel,
    validate_premarket_intel,
    validate_regime_state,
    validate_uw_intel_pnl_summary,
    validate_uw_usage_state,
)


OUT = Path("state/intel_health_state.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _is_fresh(path: Path, max_age_sec: int) -> Tuple[bool, float]:
    try:
        age = time.time() - path.stat().st_mtime
        return age <= float(max_age_sec), float(age)
    except Exception:
        return False, 1e18


def _tail_lines(path: Path, n: int) -> List[str]:
    try:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-int(n) :] if lines else []
    except Exception:
        return []


def _parse_iso(ts: Any) -> Optional[datetime]:
    try:
        if ts is None:
            return None
        s = str(ts).strip().replace("Z", "+00:00")
        if not s:
            return None
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _check_schema(name: str, path: Path, fn) -> Dict[str, Any]:
    if not path.exists():
        return {"name": name, "status": "missing", "path": str(path)}
    doc = _read_json(path)
    ok, msg = fn(doc)
    return {"name": name, "status": "ok" if ok else "bad_schema", "path": str(path), "detail": msg}


def _heal_if_needed(*, heal: bool, mock: bool, check_name: str, script: List[str]) -> Dict[str, Any]:
    if not heal:
        return {"name": check_name, "healed": False}
    env = dict(os.environ)
    if mock:
        env["UW_MOCK"] = "1"
    try:
        p = subprocess.run([sys.executable] + script, cwd=str(ROOT), env=env, capture_output=True, text=True)
        return {"name": check_name, "healed": p.returncode == 0, "rc": int(p.returncode), "stderr": (p.stderr or "")[-500:]}
    except Exception as e:
        return {"name": check_name, "healed": False, "error": str(e)}


def _latest_droplet_sync_dir() -> Optional[Path]:
    root = Path("droplet_sync")
    if not root.exists():
        return None
    try:
        dirs = [p for p in root.iterdir() if p.is_dir()]
        if not dirs:
            return None
        return sorted(dirs, key=lambda p: p.name)[-1]
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-age-hours", type=float, default=24.0, help="Freshness threshold for intel state")
    ap.add_argument("--heal", action="store_true", help="Attempt safe self-healing when missing/stale")
    ap.add_argument("--mock", action="store_true", help="Use UW_MOCK=1 for heal actions")
    ap.add_argument("--nonfatal", action="store_true", help="Always exit 0 (still writes state with ok=true/false)")
    args = ap.parse_args()

    max_age_sec = int(float(args.max_age_hours) * 3600.0)
    heal = bool(args.heal)
    mock = bool(args.mock) or str(os.getenv("UW_MOCK", "")).strip() in ("1", "true", "TRUE", "yes", "YES")

    checks: List[Dict[str, Any]] = []

    # Freshness checks
    freshness_targets = [
        ("daily_universe", Path("state/daily_universe.json")),
        ("core_universe", Path("state/core_universe.json")),
        ("daily_universe_v2", Path("state/daily_universe_v2.json")),
        ("premarket_intel", Path("state/premarket_intel.json")),
        ("postmarket_intel", Path("state/postmarket_intel.json")),
        ("uw_usage_state", Path("state/uw_usage_state.json")),
        ("regime_state", Path("state/regime_state.json")),
        ("uw_intel_pnl_summary", Path("state/uw_intel_pnl_summary.json")),
    ]
    for name, p in freshness_targets:
        if not p.exists():
            checks.append({"name": f"freshness:{name}", "status": "missing", "path": str(p)})
            continue
        ok, age = _is_fresh(p, max_age_sec=max_age_sec)
        checks.append({"name": f"freshness:{name}", "status": "ok" if ok else "stale", "path": str(p), "age_sec": round(age, 1)})

    # Schema checks
    checks.append(_check_schema("schema:daily_universe", Path("state/daily_universe.json"), validate_daily_universe))
    checks.append(_check_schema("schema:core_universe", Path("state/core_universe.json"), validate_core_universe))
    checks.append(_check_schema("schema:daily_universe_v2", Path("state/daily_universe_v2.json"), validate_daily_universe_v2))
    checks.append(_check_schema("schema:premarket_intel", Path("state/premarket_intel.json"), validate_premarket_intel))
    checks.append(_check_schema("schema:postmarket_intel", Path("state/postmarket_intel.json"), validate_postmarket_intel))
    checks.append(_check_schema("schema:uw_usage_state", Path("state/uw_usage_state.json"), validate_uw_usage_state))
    checks.append(_check_schema("schema:regime_state", Path("state/regime_state.json"), validate_regime_state))
    # PnL summary is optional early; only validate if present
    if Path("state/uw_intel_pnl_summary.json").exists():
        checks.append(_check_schema("schema:uw_intel_pnl_summary", Path("state/uw_intel_pnl_summary.json"), validate_uw_intel_pnl_summary))

    # UW usage check (warn threshold)
    usage = _read_json(Path("state/uw_usage_state.json")) if Path("state/uw_usage_state.json").exists() else None
    if isinstance(usage, dict):
        calls = int(usage.get("calls_today", 0) or 0)
        try:
            from config.registry import UW_DAILY_LIMIT, UW_SAFETY_BUFFER
            warn = calls >= int(float(UW_DAILY_LIMIT) * float(UW_SAFETY_BUFFER))
        except Exception:
            warn = False
        checks.append({"name": "uw_usage", "status": "warn" if warn else "ok", "calls_today": calls})
    else:
        checks.append({"name": "uw_usage", "status": "missing"})

    # Master trade log health (append-only, additive observability)
    try:
        mtl = Path("logs/master_trade_log.jsonl")
        if not mtl.exists():
            checks.append({"name": "master_trade_log", "status": "missing", "path": str(mtl)})
        else:
            # Basic freshness via mtime
            ok_fresh, age = _is_fresh(mtl, max_age_sec=max_age_sec)
            # Basic integrity: last N lines parse as JSON, required fields present when present.
            bad = 0
            parsed = 0
            newest_dt: Optional[datetime] = None
            for ln in _tail_lines(mtl, n=500):
                ln = (ln or "").strip()
                if not ln:
                    continue
                try:
                    obj = json.loads(ln)
                    if not isinstance(obj, dict):
                        bad += 1
                        continue
                    parsed += 1
                    for k in ["trade_id", "symbol", "side", "entry_ts", "source"]:
                        if k not in obj:
                            bad += 1
                            break
                    # Find newest timestamp (best-effort)
                    dt = _parse_iso(obj.get("exit_ts") or obj.get("entry_ts") or obj.get("timestamp"))
                    if dt and (newest_dt is None or dt > newest_dt):
                        newest_dt = dt
                except Exception:
                    bad += 1
                    continue
            status = "ok"
            if bad > 0:
                status = "bad_schema"
            elif not ok_fresh:
                status = "stale"
            checks.append(
                {
                    "name": "master_trade_log",
                    "status": status,
                    "path": str(mtl),
                    "age_sec": round(float(age), 1),
                    "parsed_lines": int(parsed),
                    "bad_lines": int(bad),
                    "newest_ts": newest_dt.isoformat() if newest_dt else None,
                }
            )
    except Exception as e:
        checks.append({"name": "master_trade_log", "status": "error", "detail": str(e)})

    # Droplet sync completeness (local-only; skip on droplet/servers without local sync dirs)
    latest = _latest_droplet_sync_dir()
    if latest is None:
        checks.append({"name": "droplet_sync", "status": "skip", "detail": "droplet_sync/ not found (local-only check)"})
    else:
        required = [
            "daily_universe.json",
            "core_universe.json",
            "premarket_intel.json",
            "postmarket_intel.json",
            "uw_usage_state.json",
        ]
        missing = [f for f in required if not (latest / f).exists()]
        checks.append({"name": "droplet_sync", "status": "ok" if not missing else "incomplete", "dir": str(latest), "missing": missing})

    # Self-healing (safe, best-effort)
    heal_events: List[Dict[str, Any]] = []
    if heal:
        if not Path("state/daily_universe.json").exists() or not Path("state/core_universe.json").exists():
            heal_events.append(_heal_if_needed(heal=True, mock=mock, check_name="heal:build_daily_universe", script=["scripts/build_daily_universe.py", "--mock"] if mock else ["scripts/build_daily_universe.py"]))
        if not Path("state/premarket_intel.json").exists():
            heal_events.append(_heal_if_needed(heal=True, mock=mock, check_name="heal:premarket_intel", script=["scripts/run_premarket_intel.py", "--mock"] if mock else ["scripts/run_premarket_intel.py"]))
        if not Path("state/postmarket_intel.json").exists():
            heal_events.append(_heal_if_needed(heal=True, mock=mock, check_name="heal:postmarket_intel", script=["scripts/run_postmarket_intel.py", "--mock"] if mock else ["scripts/run_postmarket_intel.py"]))
        if not Path("state/regime_state.json").exists():
            heal_events.append(_heal_if_needed(heal=True, mock=mock, check_name="heal:regime_state", script=["scripts/run_regime_detector.py"]))

    ok = all(c.get("status") in ("ok", "warn", "skip") for c in checks)
    doc = {
        "_meta": {"ts": _now_iso(), "version": "2026-01-20_intel_health_v1"},
        "ok": bool(ok),
        "checks": checks,
        "self_heal": heal_events,
    }

    v_ok, v_msg = validate_intel_health_state(doc)
    if not v_ok:
        print(f"intel health schema invalid: {v_msg}")
        return 2

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
    print(str(OUT))
    if bool(args.nonfatal):
        return 0
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

