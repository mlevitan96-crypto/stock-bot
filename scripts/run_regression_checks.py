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
from datetime import datetime, timezone
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
    telemetry_date = (os.environ.get("REGRESSION_TELEMETRY_DATE") or datetime.now(timezone.utc).strftime("%Y-%m-%d")).strip()

    # 0) UW spec integrity (must exist + load + sanity size)
    _run(
        [
            sys.executable,
            "-c",
            "from src.uw.uw_spec_loader import SPEC_PATH, get_valid_uw_paths; "
            "assert SPEC_PATH.exists(), 'missing api_spec.yaml'; "
            "paths=get_valid_uw_paths(); "
            "assert isinstance(paths,set) and len(paths)>=50, f'bad openapi paths count: {len(paths) if isinstance(paths,set) else type(paths)}'; "
            "print('ok')",
        ],
        env=base_env,
    )

    # 0b) Static audit of UW endpoints in code
    _run([sys.executable, "scripts/audit_uw_endpoints.py"], env=base_env)

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
        validate_daily_universe_v2,
        validate_intel_health_state,
        validate_postmarket_intel,
        validate_premarket_intel,
        validate_regime_state,
        validate_uw_intel_pnl_summary,
        validate_uw_usage_state,
    )
    daily = json.loads(Path("state/daily_universe.json").read_text(encoding="utf-8"))
    core = json.loads(Path("state/core_universe.json").read_text(encoding="utf-8"))
    daily_v2 = json.loads(Path("state/daily_universe_v2.json").read_text(encoding="utf-8")) if Path("state/daily_universe_v2.json").exists() else {}
    pm = json.loads(Path("state/premarket_intel.json").read_text(encoding="utf-8"))
    post = json.loads(Path("state/postmarket_intel.json").read_text(encoding="utf-8"))
    ok, msg = validate_daily_universe(daily); _assert(ok, f"daily_universe schema: {msg}")
    ok, msg = validate_core_universe(core); _assert(ok, f"core_universe schema: {msg}")
    if daily_v2:
        ok, msg = validate_daily_universe_v2(daily_v2); _assert(ok, f"daily_universe_v2 schema: {msg}")
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

    # 5e) UW client must reject invalid endpoints even in mock mode (and log it)
    def _tail_system_events() -> str:
        p = Path("logs/system_events.jsonl")
        if not p.exists():
            return ""
        try:
            return p.read_text(encoding="utf-8", errors="replace")[-20000:]
        except Exception:
            return ""

    before = _tail_system_events()
    try:
        from src.uw.uw_client import uw_get  # type: ignore

        uw_get("INVALID_ENDPOINT", params=None, cache_policy=None)  # type: ignore[arg-type]
        _assert(False, "uw_get did not raise on invalid endpoint")
    except ValueError:
        pass
    after = _tail_system_events()
    _assert("uw_invalid_endpoint_attempt" in after[len(before):] or "uw_invalid_endpoint_attempt" in after, "missing uw_invalid_endpoint_attempt in system_events")

    # 5d) droplet runner scripts importable + local-only mock sync works (no SSH)
    _run([sys.executable, "-c", "import scripts.run_uw_intel_on_droplet, scripts.run_premarket_on_droplet, scripts.run_postmarket_on_droplet; print('ok')"], env=base_env)
    _run([sys.executable, "scripts/run_uw_intel_on_droplet.py", "--no-ssh", "--mock", "--date", "2026-01-01"], env=base_env)
    _assert(Path("droplet_sync/2026-01-01/daily_universe.json").exists(), "droplet_sync daily_universe missing")
    _run([sys.executable, "scripts/run_uw_intel_on_droplet.py", "--no-ssh", "--mock", "--date", "2026-01-01", "--full-telemetry"], env=base_env)
    _assert(Path("telemetry/2026-01-01/FULL_TELEMETRY_2026-01-01.md").exists(), "full telemetry not generated in no-ssh mode")

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
        [
            sys.executable,
            "-c",
            "import json,time; import uw_composite_v2 as m; "
            # Freeze weights to deterministic baseline (avoid adaptive/state-driven drift on droplet).
            "m._cached_weights = m.WEIGHTS_V3.copy(); m._weights_cache_ts = time.time(); "
            "p=json.load(open('reports/_regression_v1_composite_input.json','r')); "
            "r=m.compute_composite_score_v3(p['symbol'], p['enriched']); "
            "print(json.dumps(r, sort_keys=True))",
        ],
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

    # 8) regime state exists + schema valid (additive)
    _run([sys.executable, "scripts/run_regime_detector.py"], env=base_env)
    _assert(Path("state/regime_state.json").exists(), "state/regime_state.json not written")
    reg = json.loads(Path("state/regime_state.json").read_text(encoding="utf-8"))
    ok, msg = validate_regime_state(reg); _assert(ok, f"regime_state schema: {msg}")

    # 9) attribution log created (additive, append-only)
    _assert(Path("logs/uw_attribution.jsonl").exists(), "logs/uw_attribution.jsonl not created by v2 scoring")
    try:
        tail = Path("logs/uw_attribution.jsonl").read_text(encoding="utf-8", errors="replace").splitlines()[-1].strip()
        rec = json.loads(tail) if tail else {}
        _assert(isinstance(rec, dict) and "symbol" in rec and "uw_features" in rec and "uw_contribution" in rec, "uw_attribution schema missing keys")
    except Exception:
        _assert(False, "failed to parse last uw_attribution record")

    # 10) daily intel P&L script runs and writes summary state (best-effort)
    _run([sys.executable, "scripts/run_daily_intel_pnl.py", "--date", "2026-01-01"], env=base_env)
    _assert(Path("state/uw_intel_pnl_summary.json").exists(), "state/uw_intel_pnl_summary.json not written")
    pnl = json.loads(Path("state/uw_intel_pnl_summary.json").read_text(encoding="utf-8"))
    ok, msg = validate_uw_intel_pnl_summary(pnl); _assert(ok, f"uw_intel_pnl_summary schema: {msg}")

    # 11) intel health checks run and write health state
    _run([sys.executable, "scripts/run_intel_health_checks.py", "--mock", "--nonfatal"], env=base_env)
    _assert(Path("state/intel_health_state.json").exists(), "state/intel_health_state.json not written")
    hs = json.loads(Path("state/intel_health_state.json").read_text(encoding="utf-8"))
    ok, msg = validate_intel_health_state(hs); _assert(ok, f"intel_health_state schema: {msg}")

    # 12) intel dashboard generator runs
    _run([sys.executable, "reports/_dashboard/intel_dashboard_generator.py", "--date", "2026-01-01"], env=base_env)
    _assert(Path("reports/INTEL_DASHBOARD_2026-01-01.md").exists(), "intel dashboard not generated")
    dash_text = Path("reports/INTEL_DASHBOARD_2026-01-01.md").read_text(encoding="utf-8", errors="replace")
    _assert("UW Flow Daemon Health" in dash_text, "intel dashboard missing daemon health section")
    _assert("Shadow Trading Snapshot (v2)" in dash_text, "intel dashboard missing shadow trading snapshot section")

    # 13) daemon health sentinel (mock scenarios)
    _run([sys.executable, "-c", "import scripts.run_daemon_health_check; print('ok')"], env=base_env)
    from scripts.uw_intel_schema import validate_uw_daemon_health_state
    for scenario in ["healthy", "missing_pid", "stale_lock", "stale_poll", "crash_loop", "endpoint_errors"]:
        env = dict(base_env)
        env["DAEMON_HEALTH_MOCK"] = "1"
        env["DAEMON_HEALTH_SCENARIO"] = scenario
        _run([sys.executable, "scripts/run_daemon_health_check.py", "--mock", "--nonfatal"], env=env)
        _assert(Path("state/uw_daemon_health_state.json").exists(), "uw daemon health state not written")
        dh = json.loads(Path("state/uw_daemon_health_state.json").read_text(encoding="utf-8"))
        ok, msg = validate_uw_daemon_health_state(dh); _assert(ok, f"uw_daemon_health_state schema: {msg}")

    # 14) shadow trading artifacts: logger/executor + summary + readiness (mock)
    _run([sys.executable, "-c", "from src.trading.shadow_executor import log_shadow_decision; from src.trading.shadow_logger import append_shadow_trade; print('ok')"], env=base_env)
    # true-sim smoke: open + exit a shadow position using real simulator fields
    _run(
        [
            sys.executable,
            "-c",
            "import json; from pathlib import Path; "
            "from src.trading.shadow_executor import log_shadow_decision; "
            "Path('state').mkdir(exist_ok=True); "
            "Path('state/shadow_v2_positions.json').write_text(json.dumps({'positions': {}}, indent=2)); "
            "comp={'uw_intel_version':'test','v2_uw_inputs':{'flow_strength':0.6,'darkpool_bias':0.1,'sector_alignment':0.2,'regime_alignment':0.2},"
            "'v2_uw_adjustments':{'flow_strength':0.05,'darkpool_bias':0.01,'sector_alignment':0.01,'regime_alignment':0.01,'total':0.08},"
            "'v2_uw_sector_profile':{'sector':'TECH'},'v2_uw_regime_profile':{'regime_label':'NEUTRAL'}}; "
            "log_shadow_decision(symbol='AAPL',direction='bullish',v1_score=3.2,v2_score=4.0,v1_pass=True,v2_pass=True,composite_v2=comp,current_price=100.0,account_equity=55000.0,buying_power=100000.0,position_size_usd=500.0); "
            "assert Path('state/shadow_v2_positions.json').exists(); "
            "pos=json.loads(Path('state/shadow_v2_positions.json').read_text()); "
            "assert 'AAPL' in (pos.get('positions') or {}); "
            "log_shadow_decision(symbol='AAPL',direction='bullish',v1_score=3.2,v2_score=3.9,v1_pass=True,v2_pass=False,composite_v2=comp,current_price=1000.0,account_equity=55000.0,buying_power=100000.0,position_size_usd=500.0); "
            "print('ok')",
        ],
        env=base_env,
    )
    from scripts.uw_intel_schema import validate_shadow_trade_log_entry
    st = Path("logs/shadow_trades.jsonl")
    _assert(st.exists(), "logs/shadow_trades.jsonl not created")
    last = st.read_text(encoding="utf-8", errors="replace").splitlines()[-1].strip()
    got = json.loads(last) if last else {}
    ok, msg = validate_shadow_trade_log_entry(got); _assert(ok, f"shadow_trades schema: {msg}")

    # shadow day summary runs (realized PnL best-effort when entry/exit present)
    _run([sys.executable, "scripts/run_shadow_day_summary.py", "--date", "2026-01-01"], env=base_env)
    _assert(Path("reports/SHADOW_DAY_SUMMARY_2026-01-01.md").exists(), "shadow day summary not generated")

    # preopen readiness check runs in regression with regression-skip
    pre_env = dict(base_env)
    pre_env["PREOPEN_SKIP_REGRESSION"] = "1"
    pre_env["DAEMON_HEALTH_MOCK"] = "1"
    pre_env["DAEMON_HEALTH_SCENARIO"] = "healthy"
    _run([sys.executable, "scripts/run_daemon_health_check.py", "--mock", "--nonfatal"], env=pre_env)
    _run([sys.executable, "scripts/run_preopen_readiness_check.py", "--allow-mock"], env=pre_env)

    # v2 tuning helper runs (suggestions only)
    _run([sys.executable, "-m", "src.intel.v2_tuning_helper"], env=base_env)

    # 15) Exit intelligence layer (mock)
    _run([sys.executable, "-c", "from src.exit.exit_score_v2 import compute_exit_score_v2; from src.exit.profit_targets_v2 import compute_profit_target; from src.exit.stops_v2 import compute_stop_price; from src.exit.replacement_logic_v2 import choose_replacement_candidate; print('ok')"], env=base_env)
    _run([sys.executable, "-c", "from src.exit.exit_attribution import build_exit_attribution_record, append_exit_attribution; r=build_exit_attribution_record(symbol='AAPL', entry_timestamp='2026-01-01T00:00:00+00:00', exit_reason='profit', pnl=None, time_in_trade_minutes=None, entry_uw={}, exit_uw={}, entry_regime='NEUTRAL', exit_regime='NEUTRAL', entry_sector_profile={'sector':'TECH'}, exit_sector_profile={'sector':'TECH'}, score_deterioration=0.1, relative_strength_deterioration=0.0, v2_exit_score=0.5, v2_exit_components={'score_deterioration':0.1}); append_exit_attribution(r); print('ok')"], env=base_env)
    from scripts.uw_intel_schema import validate_exit_attribution, validate_exit_intel_pnl_summary, validate_exit_intel_state
    ea = Path("logs/exit_attribution.jsonl")
    _assert(ea.exists(), "logs/exit_attribution.jsonl not created")
    last_ea = ea.read_text(encoding="utf-8", errors="replace").splitlines()[-1].strip()
    ea_rec = json.loads(last_ea) if last_ea else {}
    ok, msg = validate_exit_attribution(ea_rec); _assert(ok, f"exit_attribution schema: {msg}")
    _assert("entry_price" in ea_rec and "exit_price" in ea_rec, "exit_attribution missing entry_price/exit_price fields")

    # Pre/postmarket exit intel scripts run (mock)
    _run([sys.executable, "scripts/run_premarket_exit_intel.py", "--mock"], env=base_env)
    _run([sys.executable, "scripts/run_postmarket_exit_intel.py", "--mock"], env=base_env)
    pre = json.loads(Path("state/premarket_exit_intel.json").read_text(encoding="utf-8"))
    ok, msg = validate_exit_intel_state(pre, kind="premarket_exit_intel"); _assert(ok, msg)
    post = json.loads(Path("state/postmarket_exit_intel.json").read_text(encoding="utf-8"))
    ok, msg = validate_exit_intel_state(post, kind="postmarket_exit_intel"); _assert(ok, msg)

    # Exit intel PnL + day summary
    _run([sys.executable, "scripts/run_exit_intel_pnl.py", "--date", "2026-01-01"], env=base_env)
    _assert(Path("state/exit_intel_pnl_summary.json").exists(), "exit_intel_pnl_summary missing")
    ep = json.loads(Path("state/exit_intel_pnl_summary.json").read_text(encoding="utf-8"))
    ok, msg = validate_exit_intel_pnl_summary(ep); _assert(ok, f"exit_intel_pnl_summary schema: {msg}")
    _run([sys.executable, "scripts/run_exit_day_summary.py", "--date", "2026-01-01"], env=base_env)
    _assert(Path("reports/EXIT_DAY_SUMMARY_2026-01-01.md").exists(), "exit day summary not generated")

    dash_text = Path("reports/INTEL_DASHBOARD_2026-01-01.md").read_text(encoding="utf-8", errors="replace")
    _assert("Exit Intelligence Snapshot (v2)" in dash_text, "intel dashboard missing exit intelligence section")

    # 16) Post-close analysis pack (mock)
    _run([sys.executable, "-c", "import scripts.run_postclose_analysis_pack; print('ok')"], env=base_env)
    _run([sys.executable, "scripts/run_postclose_analysis_pack.py", "--mock", "--archive", "--date", "2026-01-01"], env=base_env)
    pack_dir = Path("analysis_packs/2026-01-01")
    _assert(pack_dir.exists(), "analysis_packs/2026-01-01 not created")
    _assert((pack_dir / "MASTER_SUMMARY_2026-01-01.md").exists(), "MASTER_SUMMARY not created")
    _assert((pack_dir / "manifest.json").exists(), "postclose pack manifest.json missing")
    _assert((pack_dir / "analysis_pack_2026-01-01.tar.gz").exists(), "postclose pack archive missing")

    # 17) Full telemetry extract (bundle + master report) (read-only)
    _run([sys.executable, "scripts/run_full_telemetry_extract.py", "--date", telemetry_date], env=base_env)
    tdir = Path(f"telemetry/{telemetry_date}")
    _assert(tdir.exists(), "telemetry bundle dir missing")
    _assert((tdir / f"FULL_TELEMETRY_{telemetry_date}.md").exists(), "FULL_TELEMETRY master report missing")
    _assert((tdir / "telemetry_manifest.json").exists(), "telemetry_manifest.json missing")
    for sub in ["state", "logs", "reports"]:
        _assert((tdir / sub).exists(), f"telemetry/{sub} missing")
    # New equalizer-ready computed artifacts
    comp = tdir / "computed"
    _assert(comp.exists(), "telemetry/computed missing")
    for f in [
        "feature_equalizer_builder.json",
        "long_short_analysis.json",
        "exit_intel_completeness.json",
        "feature_value_curves.json",
        "regime_sector_feature_matrix.json",
        "shadow_vs_live_parity.json",
        "entry_parity_details.json",
        "score_distribution_curves.json",
        "regime_timeline.json",
        "feature_family_summary.json",
        "replacement_telemetry_expanded.json",
    ]:
        _assert((comp / f).exists(), f"computed artifact missing: {f}")
    feq = json.loads((comp / "feature_equalizer_builder.json").read_text(encoding="utf-8"))
    _assert(isinstance(feq, dict), "feature_equalizer_builder not dict")
    for k in ["features", "feature_exit_impact", "exit_reason_distributions", "score_evolution", "volatility_expansion", "alignment_drift", "feature_contribution_decay"]:
        _assert(k in feq, f"feature_equalizer_builder missing {k}")

    # Strict schema validation for computed telemetry artifacts
    from scripts.telemetry_schema import (
        validate_exit_intel_completeness,
        validate_feature_value_curves,
        validate_entry_parity_details,
        validate_feature_family_summary,
        validate_long_short_analysis,
        validate_regime_timeline,
        validate_regime_sector_feature_matrix,
        validate_replacement_telemetry_expanded,
        validate_score_distribution_curves,
        validate_shadow_vs_live_parity,
    )

    lsa = json.loads((comp / "long_short_analysis.json").read_text(encoding="utf-8"))
    ok, msg = validate_long_short_analysis(lsa); _assert(ok, f"long_short_analysis schema: {msg}")

    eic = json.loads((comp / "exit_intel_completeness.json").read_text(encoding="utf-8"))
    ok, msg = validate_exit_intel_completeness(eic); _assert(ok, f"exit_intel_completeness schema: {msg}")

    fvc = json.loads((comp / "feature_value_curves.json").read_text(encoding="utf-8"))
    ok, msg = validate_feature_value_curves(fvc); _assert(ok, f"feature_value_curves schema: {msg}")

    rsm = json.loads((comp / "regime_sector_feature_matrix.json").read_text(encoding="utf-8"))
    ok, msg = validate_regime_sector_feature_matrix(rsm); _assert(ok, f"regime_sector_feature_matrix schema: {msg}")

    parity = json.loads((comp / "shadow_vs_live_parity.json").read_text(encoding="utf-8"))
    ok, msg = validate_shadow_vs_live_parity(parity); _assert(ok, f"shadow_vs_live_parity schema: {msg}")

    epd = json.loads((comp / "entry_parity_details.json").read_text(encoding="utf-8"))
    ok, msg = validate_entry_parity_details(epd); _assert(ok, f"entry_parity_details schema: {msg}")

    sdc = json.loads((comp / "score_distribution_curves.json").read_text(encoding="utf-8"))
    ok, msg = validate_score_distribution_curves(sdc); _assert(ok, f"score_distribution_curves schema: {msg}")

    rt = json.loads((comp / "regime_timeline.json").read_text(encoding="utf-8"))
    ok, msg = validate_regime_timeline(rt); _assert(ok, f"regime_timeline schema: {msg}")

    ffs = json.loads((comp / "feature_family_summary.json").read_text(encoding="utf-8"))
    ok, msg = validate_feature_family_summary(ffs); _assert(ok, f"feature_family_summary schema: {msg}")

    rte = json.loads((comp / "replacement_telemetry_expanded.json").read_text(encoding="utf-8"))
    ok, msg = validate_replacement_telemetry_expanded(rte); _assert(ok, f"replacement_telemetry_expanded schema: {msg}")

    # Manifest must include new computed fields and computed_files mapping
    man = json.loads((tdir / "telemetry_manifest.json").read_text(encoding="utf-8"))
    _assert(isinstance(man, dict), "telemetry_manifest not dict")
    comp_obj = man.get("computed") if isinstance(man.get("computed"), dict) else {}
    _assert(isinstance(comp_obj.get("computed_files"), dict), "telemetry_manifest.computed.computed_files missing")
    for k in [
        "feature_equalizer",
        "long_short_analysis",
        "exit_intel_completeness",
        "feature_value_curves",
        "regime_sector_feature_matrix",
        "shadow_vs_live_parity",
        "entry_parity_details",
        "score_distribution_curves",
        "regime_timeline",
        "feature_family_summary",
        "replacement_telemetry_expanded",
    ]:
        _assert(k in comp_obj, f"telemetry_manifest.computed missing {k}")

    print("REGRESSION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

