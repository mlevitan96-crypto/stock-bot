#!/usr/bin/env python3
"""
Regression Checks (contract-driven)
==================================

This repo previously lacked a canonical regression runner; this script is now the
single place to validate "no-break" guarantees for new additive layers.

Contracts enforced:
- v1 composite MUST remain unchanged for a fixed test set.
- UW client + intel scripts MUST run in mock mode without network.
- v2 composite MUST compute with mock UW intel (shadow-only).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _run(cmd: List[str], *, env: Dict[str, str] | None = None) -> None:
    p = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    base_env = dict(os.environ)
    base_env["UW_MOCK"] = "1"
    base_env["PYTHONIOENCODING"] = "utf-8"

    # 1) uw_client importable
    _run([sys.executable, "-c", "from src.uw.uw_client import uw_get; assert callable(uw_get)"], env=base_env)

    # 2) rate limit config present
    _run([sys.executable, "-c", "from config import registry; assert registry.UW_RATE_LIMIT_PER_MIN and registry.UW_DAILY_LIMIT"], env=base_env)

    # 3) uw usage state can be created/updated in mock mode
    _run([sys.executable, "-c", "import os; os.environ['UW_MOCK']='1'; from src.uw.uw_client import uw_get; uw_get('/api/market/top-net-impact', {'limit': 1}); print('ok')"], env=base_env)

    # 4) build_daily_universe runs in mock mode
    _run([sys.executable, "scripts/build_daily_universe.py", "--mock", "--max", "20", "--core", "10"], env=base_env)
    _assert(Path("state/daily_universe.json").exists(), "state/daily_universe.json not written")
    _assert(Path("state/core_universe.json").exists(), "state/core_universe.json not written")

    # 5) pre/post-market scripts run in mock mode
    _run([sys.executable, "scripts/run_premarket_intel.py", "--mock"], env=base_env)
    _run([sys.executable, "scripts/run_postmarket_intel.py", "--mock"], env=base_env)
    _assert(Path("state/premarket_intel.json").exists(), "state/premarket_intel.json not written")
    _assert(Path("state/postmarket_intel.json").exists(), "state/postmarket_intel.json not written")

    # 5b) schema validation for intel/universe state
    from scripts.uw_intel_schema import (
        validate_core_universe,
        validate_daily_universe,
        validate_postmarket_intel,
        validate_premarket_intel,
        validate_uw_usage_state,
    )
    daily = json.loads(Path("state/daily_universe.json").read_text(encoding="utf-8"))
    core = json.loads(Path("state/core_universe.json").read_text(encoding="utf-8"))
    pm = json.loads(Path("state/premarket_intel.json").read_text(encoding="utf-8"))
    post = json.loads(Path("state/postmarket_intel.json").read_text(encoding="utf-8"))
    ok, msg = validate_daily_universe(daily); _assert(ok, f"daily_universe schema: {msg}")
    ok, msg = validate_core_universe(core); _assert(ok, f"core_universe schema: {msg}")
    ok, msg = validate_premarket_intel(pm); _assert(ok, f"premarket_intel schema: {msg}")
    ok, msg = validate_postmarket_intel(post); _assert(ok, f"postmarket_intel schema: {msg}")

    # 5c) UW client dry-run validation (rate limit + persistence + cache)
    # - Rate limit: set per-minute cap to 1; second call should be blocked.
    rate_env = dict(base_env)
    rate_env["UW_RATE_LIMIT_PER_MIN"] = "1"
    rate_env["UW_MOCK_ENFORCE_LIMITS"] = "1"
    _run([sys.executable, "-c", "import os; os.environ['UW_MOCK']='1'; os.environ['UW_MOCK_ENFORCE_LIMITS']='1'; "
                               "from src.uw.uw_client import uw_http_get; "
                               "uw_http_get('/api/market/top-net-impact', {'limit':1}); "
                               "st, data, _=uw_http_get('/api/market/top-net-impact', {'limit':1}); "
                               "assert (st==429 or (isinstance(data,dict) and data.get('_blocked'))); print('ok')"], env=rate_env)
    # - Usage persistence file exists and validates
    _assert(Path("state/uw_usage_state.json").exists(), "state/uw_usage_state.json not written")
    usage = json.loads(Path("state/uw_usage_state.json").read_text(encoding="utf-8"))
    ok, msg = validate_uw_usage_state(usage); _assert(ok, f"uw_usage_state schema: {msg}")

    # 5d) droplet runner scripts importable + local-only mock sync works (no SSH)
    _run([sys.executable, "-c", "import scripts.run_uw_intel_on_droplet, scripts.run_premarket_on_droplet, scripts.run_postmarket_on_droplet; print('ok')"], env=base_env)
    _run([sys.executable, "scripts/run_uw_intel_on_droplet.py", "--no-ssh", "--mock", "--date", "2026-01-01"], env=base_env)
    _assert(Path("droplet_sync/2026-01-01/daily_universe.json").exists(), "droplet_sync daily_universe missing")

    # 6) v1 composite outputs unchanged for fixed test set (golden embedded here)
    # NOTE: this checks the *function output* deterministically for mock enriched inputs.
    v1_check = _read(ROOT / "uw_composite_v2.py")
    _assert("def compute_composite_score_v3(" in v1_check, "v1 composite function missing")

    # compute v1 for a fixed enriched payload
    gold_path = Path("reports/_regression_v1_composite_golden.json")
    input_path = Path("reports/_regression_v1_composite_input.json")
    test_payload = {
        "symbol": "AAPL",
        "enriched": {
            "sentiment": "BULLISH",
            "conviction": 0.62,
            "trade_count": 10,
            "dark_pool": {"total_premium": 2500000},
            "insider": {"sentiment": "NEUTRAL", "conviction_modifier": 0.0},
            "iv_term_skew": 0.2,
            "smile_slope": 0.1,
            "toxicity": 0.2,
            "event_alignment": 0.4,
            "freshness": 1.0,
        },
    }
    Path("reports").mkdir(exist_ok=True)
    input_path.write_text(json.dumps(test_payload, indent=2), encoding="utf-8")

    out = subprocess.check_output(
        [sys.executable, "-c", "import json; from uw_composite_v2 import compute_composite_score_v3; p=json.load(open('reports/_regression_v1_composite_input.json','r')); r=compute_composite_score_v3(p['symbol'], p['enriched']); print(json.dumps(r, sort_keys=True))"],
        cwd=str(ROOT),
        env=base_env,
        text=True,
    ).strip()

    if gold_path.exists():
        golden = json.loads(gold_path.read_text(encoding="utf-8"))
        got = json.loads(out)
        _assert(float(got.get("score", 0.0)) == float(golden.get("score", 0.0)), "v1 composite score changed (regression)")
    else:
        # First run creates the golden file in-repo (explicit, visible).
        gold_path.write_text(out + "\n", encoding="utf-8")

    # 7) v2 composite computes with mock UW intel (shadow-only)
    _run([sys.executable, "-c", "import json; from uw_composite_v2 import compute_composite_score_v3_v2; from config.registry import COMPOSITE_WEIGHTS_V2; enriched={'sentiment':'BULLISH','conviction':0.62,'trade_count':10,'realized_vol_20d':0.35,'beta_vs_spy':1.4}; r=compute_composite_score_v3_v2('AAPL', enriched, market_context={}, posture_state={'posture':'long','regime_confidence':0.8}, base_override={'score':3.5}, v2_params=COMPOSITE_WEIGHTS_V2); assert r.get('composite_version')=='v2'; print('ok')"], env=base_env)

    print("REGRESSION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

