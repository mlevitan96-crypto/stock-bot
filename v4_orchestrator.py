# v2_nightly_orchestration_with_auto_promotion.py
# One-drop module: runs nightly execution tasks (sector rotation, canary evaluation, feature rollup),
# computes promotion metrics, and auto-flips a promotion flag to enable direct V2 execution in the main cycle.
#
# How to use:
# 1) Paste this file into your project.
# 2) Call nightly_orchestrate() from your nightly scheduler (after the learning burn-in finishes).
# 3) In main.py, gate execution with the promotion flag:
#      from v2_nightly_orchestration_with_auto_promotion import should_run_direct_v2
#      if should_run_direct_v2():
#          # run V2 execution inside trading loop (cross-asset confirmation, motif-aware routing, feature attribution)
#      else:
#          # hybrid: V2 intelligence only in trading loop, execution modules run nightly
#
# This file is self-contained: it handles metrics rollup, promotion/demotion logic, auditing, and safe defaults.

import json
import os
from datetime import datetime, timedelta

from config.registry import CacheFiles, StateFiles, append_jsonl, atomic_write_json, read_json

# -------------------- Paths (canonical) --------------------
# Keep the same “concepts”, but remove hardcoded strings to prevent drift.
PATHS = {
    "alpha_attribution_v2": CacheFiles.ALPHA_ATTRIBUTION_V2,
    "orders_log": CacheFiles.V2_ORDERS_LOG,
    "sector_profiles": StateFiles.SECTOR_PROFILES,
    "canary_registry": StateFiles.CANARY_REGISTRY,
    "metrics_rollup": StateFiles.V2_METRICS,
    "promotion_flag": StateFiles.V2_PROMOTED,
    "audit": CacheFiles.AUDIT_V2_PROMOTION,
}

# -------------------- Promotion Criteria --------------------
CRITERIA = {
    "expectancy_delta_min": 0.10,   # +10% uplift vs legacy/hybrid baseline
    "drawdown_max": 0.08,           # <= 8% drawdown
    "consecutive_nights_min": 3,    # at least 3 nights meeting criteria before promotion
    "demote_on_fail_nights": 2      # demote after 2 consecutive fail nights
}

# -------------------- Helpers --------------------
def _now():
    return datetime.utcnow().isoformat() + "Z"

def _read_json(path, default=None):
    try:
        return read_json(path, default=default)
    except Exception:
        return default

def _write_json(path, obj):
    try:
        atomic_write_json(path, obj)
    except Exception:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(obj, indent=2))
        except Exception:
            pass

def _read_jsonl(path, max_lines=None):
    try:
        lines = path.read_text().splitlines()
        if max_lines is not None:
            lines = lines[-max_lines:]
        return [json.loads(l) for l in lines if l.strip()]
    except Exception:
        return []

# -------------------- Nightly Tasks (Bridge Calls) --------------------
def run_sector_rotation_v2():
    try:
        from sector_rotation_v2 import rebalance_sectors
        profiles = rebalance_sectors()
        append_jsonl(PATHS["audit"], {"ts": _now(), "event": "sector_rotation_rebalance", "profiles": profiles})
        return profiles
    except Exception as e:
        profiles = {"error": str(e)}
        append_jsonl(PATHS["audit"], {"ts": _now(), "event": "sector_rotation_error", "error": str(e)})
        return profiles

def run_canary_router_v2():
    try:
        from canary_router_v2 import evaluate_canaries, promote_canaries
        eval_results = evaluate_canaries()
        promote_results = promote_canaries()
        registry = {"eval": eval_results, "promote": promote_results, "ts": _now()}
        _write_json(PATHS["canary_registry"], registry)
        append_jsonl(PATHS["audit"], {"ts": _now(), "event": "canary_update", "registry": registry})
        return registry
    except Exception as e:
        registry = {"error": str(e), "ts": _now()}
        append_jsonl(PATHS["audit"], {"ts": _now(), "event": "canary_error", "error": str(e)})
        return registry

def run_feature_rollup_v2():
    try:
        from feature_attribution_v2 import rollup_feature_pnl
        metrics = rollup_feature_pnl()
        append_jsonl(PATHS["audit"], {"ts": _now(), "event": "feature_pnl_rollup", "metrics": metrics})
        return metrics
    except Exception as e:
        metrics = {"error": str(e)}
        append_jsonl(PATHS["audit"], {"ts": _now(), "event": "feature_rollup_error", "error": str(e)})
        return metrics

# -------------------- Metrics & Promotion Logic --------------------
def compute_expectancy_delta(attrib_events):
    """
    Expectancy = avg PnL per trade. Here we approximate legacy/hybrid baseline
    by using earlier events as control and recent events as treatment.
    """
    if not attrib_events:
        return 0.0

    mid = len(attrib_events) // 2
    baseline = attrib_events[:mid]
    treatment = attrib_events[mid:]

    def avg_pnl(arr):
        if not arr:
            return 0.0
        return sum(float(e.get("pnl", 0.0)) for e in arr) / len(arr)

    base_avg = avg_pnl(baseline)
    treat_avg = avg_pnl(treatment)
    if base_avg == 0.0:
        return 1.0 if treat_avg > 0 else -1.0 if treat_avg < 0 else 0.0
    return (treat_avg - base_avg) / abs(base_avg)

def estimate_drawdown(attrib_events):
    """
    Rough drawdown estimate from cumulative PnL path.
    """
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for e in attrib_events:
        cum += float(e.get("pnl", 0.0))
        peak = max(peak, cum)
        dd = (peak - cum)
        max_dd = max(max_dd, dd)
    if peak <= 0:
        return 1.0 if max_dd > 0 else 0.0
    return max_dd / peak

def update_metrics_and_flag():
    attrib_events = _read_jsonl(PATHS["alpha_attribution_v2"], max_lines=7000)
    expectancy_delta = compute_expectancy_delta(attrib_events)
    drawdown = estimate_drawdown(attrib_events)

    metrics_state = _read_json(PATHS["metrics_rollup"], default={
        "history": [],
        "consecutive_nights": 0,
        "fail_streak": 0
    })

    tonight = {
        "ts": _now(),
        "expectancy_delta": round(expectancy_delta, 4),
        "drawdown": round(drawdown, 4),
        "meets": (
            expectancy_delta >= CRITERIA["expectancy_delta_min"] and
            drawdown <= CRITERIA["drawdown_max"]
        )
    }

    if tonight["meets"]:
        metrics_state["consecutive_nights"] = metrics_state.get("consecutive_nights", 0) + 1
        metrics_state["fail_streak"] = 0
    else:
        metrics_state["fail_streak"] = metrics_state.get("fail_streak", 0) + 1
        metrics_state["consecutive_nights"] = 0

    history = metrics_state.get("history", [])
    history.append(tonight)
    metrics_state["history"] = history[-14:]
    _write_json(PATHS["metrics_rollup"], metrics_state)

    flag = _read_json(PATHS["promotion_flag"], default={"enabled": False, "ts": _now()})
    promoted = flag.get("enabled", False)

    if metrics_state["consecutive_nights"] >= CRITERIA["consecutive_nights_min"]:
        promoted = True
        flag = {"enabled": True, "ts": _now(), "reason": "promotion_criteria_met"}
        append_jsonl(PATHS["audit"], {"ts": _now(), "event": "promotion", "metrics": tonight, "state": metrics_state})

    if metrics_state["fail_streak"] >= CRITERIA["demote_on_fail_nights"]:
        promoted = False
        flag = {"enabled": False, "ts": _now(), "reason": "demotion_fail_streak"}
        append_jsonl(PATHS["audit"], {"ts": _now(), "event": "demotion", "metrics": tonight, "state": metrics_state})

    _write_json(PATHS["promotion_flag"], flag)

    append_jsonl(PATHS["audit"], {
        "ts": _now(),
        "event": "nightly_metrics_update",
        "tonight": tonight,
        "rollup_state": {
            "consecutive_nights": metrics_state["consecutive_nights"],
            "fail_streak": metrics_state["fail_streak"]
        },
        "promotion_enabled": promoted
    })

    return tonight, flag

# -------------------- Public Nightly Orchestration --------------------
def nightly_orchestrate():
    """
    Run nightly V2 execution tasks + auto-promotion governance.
    Call this once per night after learning completes.
    """
    run_sector_rotation_v2()
    run_canary_router_v2()
    _ = run_feature_rollup_v2()
    tonight, flag = update_metrics_and_flag()
    append_jsonl(PATHS["audit"], {"ts": _now(), "event": "nightly_orchestrate_complete", "tonight": tonight, "promotion_flag": flag})
    return {"metrics": tonight, "flag": flag}

# -------------------- Main-cycle gate --------------------
def should_run_direct_v2():
    """
    Read the promotion flag to decide whether to run direct V2 execution inside the trading loop.
    Returns True if promotion flag enabled, else False.
    """
    flag = _read_json(PATHS["promotion_flag"], default={"enabled": False})
    return bool(flag.get("enabled", False))

if __name__ == "__main__":
    result = nightly_orchestrate()
    print("Nightly orchestration complete:", json.dumps(result, indent=2))
