"""
Decision Intelligence Trace — canonical multi-layer explainability for every trade/block.

Every trade_intent (entered OR blocked) must include:
- multiple contributing signals (signal_layers)
- weighted influence (aggregation)
- opposing signals
- gating outcomes (gates)
- final arbitration logic (final_decision)

If a decision cannot explain itself in layers, it is INVALID.

Schema: DecisionIntelligenceTrace (see MEMORY_BANK.md "Decision Intelligence Trace Contract").
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Blocked reason codes (enum) — replace opaque string reasons
BLOCKED_REASON_CODES = [
    "capacity_full",
    "displacement_min_hold",
    "displacement_no_dominance",
    "displacement_blocked",
    "displacement_failed",
    "directional_conflict",
    "blocked_high_vol_no_alignment",
    "risk_exceeded",
    "symbol_exposure_limit",
    "sector_exposure_limit",
    "opposing_signal_override",
    "score_below_min",
    "max_positions_reached",
    "symbol_on_cooldown",
    "momentum_ignition_filter",
    "market_closed",
    "long_only_blocked_short_entry",
    "regime_blocked",
    "concentration_gate",
    "theme_exposure_blocked",
    "other",
]


def _code_from_reason(reason: Optional[str]) -> str:
    """Map legacy blocked_reason string to blocked_reason_code."""
    r = (reason or "").strip().lower()
    if not r:
        return "other"
    if "capacity" in r or "max_position" in r or "full" in r:
        return "capacity_full"
    if "displacement_blocked" in r or "displacement_policy" in r:
        return "displacement_blocked"
    if "displacement_failed" in r:
        return "displacement_failed"
    if "min_hold" in r:
        return "displacement_min_hold"
    if "no_dominance" in r or "delta" in r:
        return "displacement_no_dominance"
    if "directional" in r or "high_vol" in r or "alignment" in r:
        return "blocked_high_vol_no_alignment"
    if "risk" in r or "exposure" in r:
        return "risk_exceeded"
    if "symbol_exposure" in r:
        return "symbol_exposure_limit"
    if "sector_exposure" in r:
        return "sector_exposure_limit"
    if "score_below" in r or "score_too_low" in r:
        return "score_below_min"
    if "max_position" in r or "capacity_limit" in r:
        return "max_positions_reached"
    if "cooldown" in r or "duplicate" in r:
        return "symbol_on_cooldown"
    if "momentum" in r or "ignition" in r:
        return "momentum_ignition_filter"
    if "market_closed" in r:
        return "market_closed"
    if "long_only" in r:
        return "long_only_blocked_short_entry"
    if "regime" in r:
        return "regime_blocked"
    if "concentration" in r:
        return "concentration_gate"
    if "theme" in r:
        return "theme_exposure_blocked"
    return "other"


def _comps_to_signal_layers(comps: Dict[str, Any], direction: str) -> Dict[str, List[Dict[str, Any]]]:
    """Derive signal_layers from components dict. Names mapped to alpha/flow/regime/volatility/dark_pool."""
    layers: Dict[str, List[Dict[str, Any]]] = {
        "alpha_signals": [],
        "flow_signals": [],
        "regime_signals": [],
        "volatility_signals": [],
        "dark_pool_signals": [],
    }
    if not isinstance(comps, dict):
        return layers
    for name, val in comps.items():
        try:
            v = float(val) if val is not None else 0.0
        except (TypeError, ValueError):
            v = 0.0
        conf = 0.5
        if abs(v) > 0.5:
            conf = min(1.0, 0.5 + abs(v) * 0.1)
        entry = {"name": str(name), "value": v, "score": v, "direction": direction, "confidence": round(conf, 2)}
        n = str(name).lower()
        if "flow" in n or "whale" in n or "premium" in n:
            layers["flow_signals"].append(entry)
        elif "regime" in n or "macro" in n:
            layers["regime_signals"].append(entry)
        elif "vol" in n or "atr" in n or "rv" in n:
            layers["volatility_signals"].append(entry)
        elif "dark" in n or "dp" in n or "dark_pool" in n:
            layers["dark_pool_signals"].append(entry)
        else:
            layers["alpha_signals"].append(entry)
    return layers


def build_initial_trace(
    symbol: str,
    side_intended: str,
    score: float,
    comps: Dict[str, Any],
    cluster: Dict[str, Any],
    ts: Optional[str] = None,
    cycle_id: Optional[int] = None,
    engine: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Build initial DecisionIntelligenceTrace from scoring context.
    Call this at the start of a decision; then append_gate_result / set_final_decision.
    """
    direction = (cluster.get("direction") or "bullish").lower()
    ts = ts or datetime.now(timezone.utc).isoformat()
    signal_layers = _comps_to_signal_layers(comps or {}, direction)
    # Ensure at least 2 layers have content (invariant)
    non_empty = [k for k, v in signal_layers.items() if v]
    if len(non_empty) < 2 and isinstance(comps, dict) and comps:
        # Spread remaining comps into alpha if we have comps but <2 layers
        for name, val in (comps or {}).items():
            if any(name in str(s.get("name")) for layer in signal_layers.values() for s in layer):
                continue
            try:
                v = float(val) if val is not None else 0.0
            except (TypeError, ValueError):
                v = 0.0
            signal_layers["alpha_signals"].append({
                "name": str(name), "value": v, "score": v, "direction": direction, "confidence": 0.5,
            })
    # Opposing: any negative-score contributions
    opposing: List[Dict[str, Any]] = []
    for layer_name, arr in signal_layers.items():
        for s in arr:
            if (s.get("score") or 0) < 0:
                opposing.append({
                    "name": s.get("name"),
                    "layer": layer_name,
                    "reason": "negative_contribution",
                    "magnitude": float(s.get("score") or 0),
                })
    # Aggregation
    raw_score = float(score)
    score_components = {str(k): round(float(v), 4) for k, v in (comps or {}).items() if v is not None}
    aggregation = {
        "raw_score": round(raw_score, 4),
        "normalized_score": round(raw_score, 4),
        "direction_confidence": 0.5 + min(0.5, abs(raw_score) * 0.1),
        "score_components": score_components or {"composite": raw_score},
    }
    trace: Dict[str, Any] = {
        "intent_id": str(uuid.uuid4()),
        "symbol": symbol,
        "side_intended": side_intended,
        "ts": ts,
        "cycle_id": cycle_id,
        "signal_layers": signal_layers,
        "opposing_signals": opposing,
        "aggregation": aggregation,
        "gates": {},
        "final_decision": {},
    }
    return trace


def append_gate_result(
    trace: Dict[str, Any],
    gate_name: str,
    passed: bool,
    reason: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Append one gate result. No overwrites."""
    g = trace.get("gates") or {}
    if gate_name == "displacement_gate" and isinstance(details, dict):
        trace["gates"] = {**g, gate_name: {"evaluated": details.get("evaluated", True), "passed": passed, "reason": reason, "incumbent_symbol": details.get("incumbent_symbol"), "challenger_delta": details.get("challenger_delta"), "min_hold_remaining": details.get("min_hold_remaining")}}
    else:
        trace["gates"] = {**g, gate_name: {"passed": passed, "reason": reason or ("ok" if passed else "blocked")}}


def set_final_decision(
    trace: Dict[str, Any],
    outcome: str,
    primary_reason: str,
    secondary_reasons: Optional[List[str]] = None,
) -> None:
    """Set final_decision. outcome must be 'entered' or 'blocked'."""
    trace["final_decision"] = {
        "outcome": outcome,
        "primary_reason": primary_reason,
        "secondary_reasons": list(secondary_reasons or []),
    }


def trace_to_emit_fields(trace: Dict[str, Any], blocked: bool) -> Dict[str, Any]:
    """Produce the add-on fields for a trade_intent record: intent_id, intelligence_trace, active_signal_names, opposing_signal_names, gate_summary, final_decision.primary_reason, and when blocked: blocked_reason_code, blocked_reason_details."""
    layers = trace.get("signal_layers") or {}
    active: List[str] = []
    for arr in layers.values():
        for s in arr:
            n = s.get("name")
            if n:
                active.append(str(n))
    opposing_names: List[str] = [str(o.get("name", "")) for o in (trace.get("opposing_signals") or []) if o.get("name")]
    gates = trace.get("gates") or {}
    gate_summary = {k: {"passed": v.get("passed"), "reason": v.get("reason")} for k, v in gates.items()}
    out: Dict[str, Any] = {
        "intent_id": trace.get("intent_id"),
        "intelligence_trace": trace,
        "active_signal_names": active,
        "opposing_signal_names": opposing_names,
        "gate_summary": gate_summary,
        "final_decision_primary_reason": (trace.get("final_decision") or {}).get("primary_reason"),
    }
    if blocked:
        reason = (trace.get("final_decision") or {}).get("primary_reason")
        out["blocked_reason_code"] = _code_from_reason(reason)
        out["blocked_reason_details"] = {"primary_reason": reason, "gates": gate_summary}
    return out


def validate_trace(trace: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate trace: multiple layers, gates populated, final_decision coherent, size reasonable. Returns (ok, list of error messages)."""
    errs: List[str] = []
    import json
    try:
        bloat = len(json.dumps(trace))
        if bloat > 500_000:
            errs.append(f"trace JSON size {bloat} exceeds 500KB")
    except Exception:
        errs.append("trace not JSON-serializable")
    layers = trace.get("signal_layers") or {}
    non_empty = [k for k, v in layers.items() if v]
    if len(non_empty) < 2:
        errs.append("fewer than 2 signal layers with content")
    fd = trace.get("final_decision") or {}
    if fd.get("outcome") not in ("entered", "blocked"):
        errs.append("final_decision.outcome missing or not 'entered'|'blocked'")
    if not fd.get("primary_reason") and fd.get("outcome") == "blocked":
        errs.append("blocked decision missing primary_reason")
    return (len(errs) == 0, errs)
