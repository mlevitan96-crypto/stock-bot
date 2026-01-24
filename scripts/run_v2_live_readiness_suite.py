#!/usr/bin/env python3
"""
v2 Live Readiness Suite (paper-only)
====================================

Runs a lightweight set of checks to validate the v2-only engine environment:
- Paper endpoint enforcement
- Alpaca connectivity
- UW spec allow-list loads
- UW intel reachable (live call)
- UW cache writable
- Telemetry extract runnable
- Deep-dive runnable
- Synthetic harness available (CLI present)
- Optional: run synthetic trade harness (broker mode; requires ALLOW_SYNTHETIC_ORDERS=1)
- No traceback spam in check outputs

Exit codes:
- 0: PASS
- 2: FAIL
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import List


def _is_paper_endpoint(url: str) -> bool:
    try:
        return "paper-api.alpaca.markets" in (url or "")
    except Exception:
        return False


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


def _run_py(args: List[str], env: dict) -> tuple[bool, str]:
    try:
        out = subprocess.check_output([sys.executable, *args], env=env, text=True, stderr=subprocess.STDOUT)
        return True, out.strip()
    except subprocess.CalledProcessError as e:
        return False, (e.output or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-synthetic", action="store_true", help="Run synthetic trade harness (requires ALLOW_SYNTHETIC_ORDERS=1)")
    ap.add_argument("--date", default=os.getenv("READINESS_DATE", ""), help="YYYY-MM-DD to validate telemetry/deep-dive (default: 2026-01-24)")
    args = ap.parse_args()

    env = dict(os.environ)
    results: List[CheckResult] = []

    # Required env vars (owner-level sanity)
    required_env = ["ALPACA_KEY", "ALPACA_SECRET", "ALPACA_BASE_URL", "UW_API_KEY"]
    missing_env = [k for k in required_env if not str(env.get(k, "") or "").strip()]
    results.append(CheckResult("required_env_vars", len(missing_env) == 0, ("missing=" + ",".join(missing_env)) if missing_env else "ok"))

    # 1) Paper endpoint enforcement
    base_url = str(env.get("ALPACA_BASE_URL", "") or "")
    if not _is_paper_endpoint(base_url):
        results.append(CheckResult("alpaca_paper_endpoint", False, f"ALPACA_BASE_URL not paper: {base_url}"))
    else:
        results.append(CheckResult("alpaca_paper_endpoint", True, base_url))

    # 2) Dependency checks (no traceback spam)
    ok, out = _run_py(
        [
            "-c",
            "import importlib.util, sys; "
            "missing=[]; "
            "mods=['requests','alpaca_trade_api']; "
            "[(missing.append(m) if importlib.util.find_spec(m) is None else None) for m in mods]; "
            "missing and (print('MISSING_DEP: ' + ','.join(missing)) or sys.exit(2)); "
            "print('OK')",
        ],
        env,
    )
    results.append(CheckResult("deps_present", ok, out[:4000]))

    # 3) Alpaca connectivity (paper account)
    ok, out = _run_py(
        [
            "-c",
            "import os, sys, importlib.util; "
            "spec=importlib.util.find_spec('alpaca_trade_api'); "
            "(spec is None) and (print('MISSING_DEP: alpaca_trade_api') or sys.exit(2)); "
            "import alpaca_trade_api as tradeapi; "
            "key=os.getenv('ALPACA_KEY',''); sec=os.getenv('ALPACA_SECRET',''); url=os.getenv('ALPACA_BASE_URL',''); "
            "((not key) or (not sec) or (not url)) and (print('MISSING_ENV: require ALPACA_KEY/ALPACA_SECRET/ALPACA_BASE_URL') or sys.exit(2)); "
            "api=tradeapi.REST(key, sec, url, api_version='v2'); a=api.get_account(); "
            "print(getattr(a,'status',None), getattr(a,'buying_power',None))",
        ],
        env,
    )
    results.append(CheckResult("alpaca_get_account", ok, out[:4000]))

    # 4) UW spec allow-list loads
    ok, out = _run_py(["-c", "from src.uw.uw_spec_loader import get_valid_uw_paths; p=get_valid_uw_paths(); assert isinstance(p,set) and len(p)>=50; print(len(p))"], env)
    results.append(CheckResult("uw_spec_loader", ok, out[:4000]))

    # 5) UW intel reachable (live call through uw_client)
    ok, out = _run_py(
        [
            "-c",
            "import os, sys; "
            "from src.uw.uw_client import uw_http_get; "
            "key=os.getenv('UW_API_KEY',''); "
            "(not key) and (print('MISSING_ENV: UW_API_KEY') or sys.exit(2)); "
            "status,data,hdr=uw_http_get('/api/alerts', params={'limit':1}, timeout_s=8.0); "
            "(status!=200) and (print(f'UW_FAIL status={status} body_keys={list((data or {}).keys())}') or sys.exit(2)); "
            "print('OK')",
        ],
        env,
    )
    results.append(CheckResult("uw_intel_reachable", ok, out[:4000]))

    # 6) UW cache writable
    ok, out = _run_py(
        [
            "-c",
            "import os, sys; from pathlib import Path; "
            "p=Path('state/uw_cache'); p.mkdir(parents=True, exist_ok=True); "
            "t=p/'_readiness_write_test.tmp'; "
            "t.write_text('ok', encoding='utf-8'); "
            "t.unlink(missing_ok=True) if hasattr(t,'unlink') else t.unlink(); "
            "print('OK')",
        ],
        env,
    )
    results.append(CheckResult("uw_cache_writable", ok, out[:4000]))

    # 7) Telemetry extract runnable (best-effort, idempotent output)
    day = (str(args.date or "").strip() or "2026-01-24")
    ok, out = _run_py(["scripts/run_full_telemetry_extract.py", "--date", day], env)
    results.append(CheckResult("telemetry_extract_runnable", ok, out[-4000:]))

    # 8) Deep-dive runnable (best-effort, v2-only mode)
    ok, out = _run_py(["scripts/run_shadow_vs_live_deep_dive.py", "--date", day], env)
    results.append(CheckResult("deep_dive_runnable", ok, out[-4000:]))

    # 9) Synthetic harness available (CLI loads)
    ok, out = _run_py(["scripts/run_v2_synthetic_trade_test.py", "--help"], env)
    results.append(CheckResult("synthetic_harness_available", ok, out[-2000:]))

    # 10) Optional synthetic trade (broker mode; uses live Alpaca paper orders)
    if args.run_synthetic:
        ok, out = _run_py(["scripts/run_v2_synthetic_trade_test.py"], env)
        results.append(CheckResult("synthetic_trade", ok, out[-4000:]))

    # Traceback spam detection (owner-level hygiene)
    for r in results:
        if (r.detail or "").find("Traceback") >= 0:
            r.ok = False
            if r.detail:
                r.detail = "TRACEBACK_DETECTED: " + r.detail[-2000:]

    all_ok = all(r.ok for r in results)
    print("V2 LIVE READINESS SUITE (paper-only)")
    for r in results:
        status = "PASS" if r.ok else "FAIL"
        print(f"- {status} {r.name} {('- ' + r.detail) if r.detail else ''}")

    if all_ok:
        print("OVERALL: PASS")
        return 0
    print("OVERALL: FAIL")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

