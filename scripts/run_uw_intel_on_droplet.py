#!/usr/bin/env python3
"""
Run UW intelligence layer on droplet and sync artifacts locally.

Outputs (local):
  droplet_sync/YYYY-MM-DD/
    - state_*.json
    - shadow_tail.jsonl
    - system_events_tail.jsonl
    - sync_log.jsonl

Safety:
- If regression fails on droplet, abort sync.
- If UW usage exceeds 95% of daily limit, log WARN in sync_log.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from droplet_client import DropletClient
from scripts.droplet_sync_utils import (
    append_sync_log,
    decode_b64,
    droplet_b64_read_file,
    droplet_b64_tail_file,
    ensure_dir,
    write_bytes,
    write_text,
)
from scripts.uw_intel_schema import (
    validate_core_universe,
    validate_daily_universe,
    validate_daily_universe_v2,
    validate_intel_health_state,
    validate_postmarket_intel,
    validate_premarket_intel,
    validate_regime_state,
    validate_uw_daemon_health_state,
    validate_uw_intel_pnl_summary,
    validate_uw_usage_state,
)


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _run_remote(client: DropletClient, cmd: str, *, timeout: int = 300) -> Dict[str, Any]:
    return client.execute_command(cmd, timeout=timeout)


def _remote_py(script_path: str, *, mock: bool) -> str:
    # Always run in droplet venv. Source .env for API keys (best-effort).
    # IMPORTANT: DropletClient executes inside project_dir already.
    env = "UW_MOCK=1 " if mock else ""
    args = " --mock" if mock else ""
    return f"bash -c \"set -a && source .env >/dev/null 2>&1 || true; set +a; {env}./venv/bin/python {script_path}{args}\""


def _validate_json(path: Path, validator) -> None:
    obj = json.loads(path.read_text(encoding="utf-8"))
    ok, msg = validator(obj)
    if not ok:
        raise RuntimeError(f"Schema validation failed for {path}: {msg}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--mock", action="store_true", help="Mock mode (no real UW calls)")
    ap.add_argument("--no-pull", action="store_true", help="Do not git pull on droplet before running")
    ap.add_argument("--no-ssh", action="store_true", help="Local-only mock sync (regression helper)")
    args = ap.parse_args()

    date = args.date.strip() or _today_utc()
    out_dir = Path("droplet_sync") / date
    ensure_dir(out_dir)
    sync_log = out_dir / "sync_log.jsonl"

    append_sync_log(sync_log, {"event": "sync_start", "date": date, "mock": bool(args.mock), "no_ssh": bool(args.no_ssh)})

    # Local-only mock path (used by regression checks)
    if args.no_ssh:
        # Produce local state using mock scripts.
        os.environ["UW_MOCK"] = "1"
        os.system(f"{os.sys.executable} scripts/build_daily_universe.py --mock --max 20 --core 10")
        os.system(f"{os.sys.executable} scripts/run_premarket_intel.py --mock")
        os.system(f"{os.sys.executable} scripts/run_postmarket_intel.py --mock")
        os.system(f"{os.sys.executable} scripts/run_regime_detector.py")
        os.system(f"{os.sys.executable} scripts/run_daily_intel_pnl.py --date {date}")
        os.system(f"{os.sys.executable} scripts/run_intel_health_checks.py --mock")
        os.system(f"{os.sys.executable} scripts/run_daemon_health_check.py --mock --nonfatal")
        os.environ["PREOPEN_SKIP_REGRESSION"] = "1"
        os.system(f"{os.sys.executable} scripts/run_preopen_readiness_check.py --allow-mock")
        os.system(f"{os.sys.executable} reports/_dashboard/intel_dashboard_generator.py --date {date}")
        # Copy artifacts into droplet_sync folder
        for src, dst in [
            ("state/daily_universe.json", out_dir / "daily_universe.json"),
            ("state/core_universe.json", out_dir / "core_universe.json"),
            ("state/daily_universe_v2.json", out_dir / "daily_universe_v2.json"),
            ("state/premarket_intel.json", out_dir / "premarket_intel.json"),
            ("state/postmarket_intel.json", out_dir / "postmarket_intel.json"),
            ("state/regime_state.json", out_dir / "regime_state.json"),
            ("state/uw_intel_pnl_summary.json", out_dir / "uw_intel_pnl_summary.json"),
            ("state/intel_health_state.json", out_dir / "intel_health_state.json"),
            ("state/uw_daemon_health_state.json", out_dir / "uw_daemon_health_state.json"),
        ]:
            p = Path(src)
            if p.exists():
                write_bytes(dst, p.read_bytes())
        # Best-effort: copy intel dashboard (if generated)
        dash = Path("reports") / f"INTEL_DASHBOARD_{date}.md"
        if dash.exists():
            write_bytes(out_dir / f"INTEL_DASHBOARD_{date}.md", dash.read_bytes())
        write_text(out_dir / "shadow_tail.jsonl", "")
        write_text(out_dir / "system_events_tail.jsonl", "")
        write_text(out_dir / "uw_attribution_tail.jsonl", "")
        append_sync_log(sync_log, {"event": "sync_complete", "mode": "no_ssh_mock"})
        return 0

    with DropletClient() as c:
        if not args.no_pull:
            r = _run_remote(c, "cd /root/stock-bot && git pull origin main", timeout=180)
            append_sync_log(sync_log, {"event": "git_pull", "success": bool(r.get("success"))})

        # Run in required order
        for step in [
            # Pre-open safe ordering:
            # 1) regression (mock-safe) to catch contract violations early
            # 2) universe + intel generation
            ("run_regression_checks", _remote_py("scripts/run_regression_checks.py", mock=True)),  # always mock-safe
            ("build_daily_universe", _remote_py("scripts/build_daily_universe.py", mock=bool(args.mock))),
            ("run_premarket_intel", _remote_py("scripts/run_premarket_intel.py", mock=bool(args.mock))),
            ("run_postmarket_intel", _remote_py("scripts/run_postmarket_intel.py", mock=bool(args.mock))),
            ("run_regime_detector", "bash -c \"./venv/bin/python scripts/run_regime_detector.py\""),
            ("run_daily_intel_pnl", f"bash -c \"set -a && source .env >/dev/null 2>&1 || true; set +a; ./venv/bin/python scripts/run_daily_intel_pnl.py --date {date}\""),
            ("run_intel_health_checks", _remote_py("scripts/run_intel_health_checks.py", mock=True)),
            ("run_daemon_health_check", "bash -c \"./venv/bin/python scripts/run_daemon_health_check.py --nonfatal\""),
            ("run_preopen_readiness_check", "bash -c \"PREOPEN_SKIP_REGRESSION=1 ./venv/bin/python scripts/run_preopen_readiness_check.py --allow-mock\""),
            ("run_intel_dashboard", f"bash -c \"./venv/bin/python reports/_dashboard/intel_dashboard_generator.py --date {date}\""),
            ("run_shadow_day_summary", f"bash -c \"./venv/bin/python scripts/run_shadow_day_summary.py --date {date}\""),
            ("run_v2_tuning_suggestions", "bash -c \"./venv/bin/python -m src.intel.v2_tuning_helper\""),
        ]:
            name, cmd = step
            rr = _run_remote(c, cmd, timeout=600)
            append_sync_log(sync_log, {"event": "run", "step": name, "success": bool(rr.get("success"))})
            if name == "run_regression_checks" and not bool(rr.get("success")):
                append_sync_log(sync_log, {"event": "abort", "reason": "regression_failed", "stderr": (rr.get("stderr") or "")[:800]})
                return 1

        # Fetch state files
        fetch_map = {
            "state/daily_universe.json": out_dir / "daily_universe.json",
            "state/core_universe.json": out_dir / "core_universe.json",
            "state/daily_universe_v2.json": out_dir / "daily_universe_v2.json",
            "state/premarket_intel.json": out_dir / "premarket_intel.json",
            "state/postmarket_intel.json": out_dir / "postmarket_intel.json",
            "state/uw_usage_state.json": out_dir / "uw_usage_state.json",
            "state/regime_state.json": out_dir / "regime_state.json",
            "state/uw_intel_pnl_summary.json": out_dir / "uw_intel_pnl_summary.json",
            "state/intel_health_state.json": out_dir / "intel_health_state.json",
            "state/uw_daemon_health_state.json": out_dir / "uw_daemon_health_state.json",
            f"reports/INTEL_DASHBOARD_{date}.md": out_dir / f"INTEL_DASHBOARD_{date}.md",
            f"reports/SHADOW_DAY_SUMMARY_{date}.md": out_dir / f"SHADOW_DAY_SUMMARY_{date}.md",
            f"reports/V2_TUNING_SUGGESTIONS_{date}.md": out_dir / f"V2_TUNING_SUGGESTIONS_{date}.md",
        }
        for remote, local in fetch_map.items():
            res = droplet_b64_read_file(c, remote, timeout=60)
            if not res.success:
                append_sync_log(sync_log, {"event": "fetch_failed", "path": remote, "stderr": res.stderr[:300]})
                continue
            write_bytes(local, decode_b64(res.stdout.strip()))
            append_sync_log(sync_log, {"event": "fetched", "path": remote})

        # Fetch tails
        for remote, local_name in [
            ("logs/shadow.jsonl", "shadow_tail.jsonl"),
            ("logs/system_events.jsonl", "system_events_tail.jsonl"),
            ("logs/uw_attribution.jsonl", "uw_attribution_tail.jsonl"),
        ]:
            res = droplet_b64_tail_file(c, remote, lines=500, timeout=60)
            if res.success:
                write_bytes(out_dir / local_name, decode_b64(res.stdout.strip()))
                append_sync_log(sync_log, {"event": "fetched_tail", "path": remote})

    # Local schema validation on synced files (must not break v1)
    try:
        _validate_json(out_dir / "daily_universe.json", validate_daily_universe)
        _validate_json(out_dir / "core_universe.json", validate_core_universe)
        if (out_dir / "daily_universe_v2.json").exists():
            _validate_json(out_dir / "daily_universe_v2.json", validate_daily_universe_v2)
        _validate_json(out_dir / "premarket_intel.json", validate_premarket_intel)
        _validate_json(out_dir / "postmarket_intel.json", validate_postmarket_intel)
        _validate_json(out_dir / "uw_usage_state.json", validate_uw_usage_state)
        if (out_dir / "regime_state.json").exists():
            _validate_json(out_dir / "regime_state.json", validate_regime_state)
        if (out_dir / "uw_intel_pnl_summary.json").exists():
            _validate_json(out_dir / "uw_intel_pnl_summary.json", validate_uw_intel_pnl_summary)
        if (out_dir / "intel_health_state.json").exists():
            _validate_json(out_dir / "intel_health_state.json", validate_intel_health_state)
        if (out_dir / "uw_daemon_health_state.json").exists():
            _validate_json(out_dir / "uw_daemon_health_state.json", validate_uw_daemon_health_state)
        append_sync_log(sync_log, {"event": "schema_validated", "success": True})
    except Exception as e:
        append_sync_log(sync_log, {"event": "schema_validated", "success": False, "error": str(e)})

    # Usage warning
    try:
        usage = json.loads((out_dir / "uw_usage_state.json").read_text(encoding="utf-8"))
        calls_today = int(usage.get("calls_today") or 0)
        from config.registry import UW_DAILY_LIMIT

        if UW_DAILY_LIMIT and calls_today / float(UW_DAILY_LIMIT) >= 0.95:
            append_sync_log(sync_log, {"event": "uw_usage_warn", "calls_today": calls_today, "daily_limit": UW_DAILY_LIMIT})
    except Exception:
        pass

    append_sync_log(sync_log, {"event": "sync_complete", "date": date})
    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

