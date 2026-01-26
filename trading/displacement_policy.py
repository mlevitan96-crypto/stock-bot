"""
Displacement policy: min hold, min delta, thesis dominance.

Contract:
- evaluate_displacement(current_position, challenger_candidate, context) -> (allowed, reason, diagnostics)
- All decisions logged via caller (system_events.jsonl, subsystem=displacement).
- Config-driven; revert by DISPLACEMENT_MIN_HOLD_SECONDS=0, MIN_DELTA=0, REQUIRE_THESIS_DOMINANCE=false.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

# Config defaults (overridden by env via caller)
DISPLACEMENT_ENABLED = True
DISPLACEMENT_MIN_HOLD_SECONDS = 20 * 60  # 20 minutes
DISPLACEMENT_MIN_DELTA_SCORE = 0.75
DISPLACEMENT_REQUIRE_THESIS_DOMINANCE = True
DISPLACEMENT_THESIS_DOMINANCE_MODE = "flow_or_regime"
DISPLACEMENT_LOG_EVERY_DECISION = True
_EPSILON = 1e-6


def _ts_now() -> datetime:
    return datetime.now(timezone.utc)


def _age_seconds(entry_ts: Optional[Any]) -> float:
    if entry_ts is None:
        return 0.0
    try:
        if hasattr(entry_ts, "timestamp"):
            t = entry_ts
        elif isinstance(entry_ts, (int, float)):
            from datetime import datetime, timezone
            t = datetime.fromtimestamp(float(entry_ts), tz=timezone.utc)
        elif isinstance(entry_ts, str):
            t = datetime.fromisoformat(entry_ts.replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
        else:
            return 0.0
        return (_ts_now() - t).total_seconds()
    except Exception:
        return 0.0


def _regime_alignment_better(challenger_regime: Any, current_regime: Any, posture: str) -> bool:
    """True if challenger aligns with posture/regime better than current (simplified)."""
    if not posture or posture.upper() == "NEUTRAL":
        return False
    p = posture.upper()
    # Placeholder: same regime = no win; different regime we don't have full logic.
    return False


def evaluate_displacement(
    current_position: Dict[str, Any],
    challenger_candidate: Dict[str, Any],
    context: Dict[str, Any],
    *,
    config_overrides: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Evaluate whether displacement is allowed.

    Args:
        current_position: {symbol, entry_ts, current_score, entry_score, uw_flow_strength, dark_pool_bias, ...}
        challenger_candidate: {symbol, score, uw_flow_strength, dark_pool_bias, ...} (new signal)
        context: {regime_label, posture, ...}
        config_overrides: optional {DISPLACEMENT_MIN_HOLD_SECONDS, DISPLACEMENT_MIN_DELTA_SCORE, ...}

    Returns:
        (allowed: bool, reason: str, diagnostics: dict)
    """
    overrides = config_overrides or {}
    min_hold = overrides.get("DISPLACEMENT_MIN_HOLD_SECONDS", DISPLACEMENT_MIN_HOLD_SECONDS)
    min_delta = overrides.get("DISPLACEMENT_MIN_DELTA_SCORE", DISPLACEMENT_MIN_DELTA_SCORE)
    require_thesis = overrides.get("DISPLACEMENT_REQUIRE_THESIS_DOMINANCE", DISPLACEMENT_REQUIRE_THESIS_DOMINANCE)
    enabled = overrides.get("DISPLACEMENT_ENABLED", DISPLACEMENT_ENABLED)

    current_symbol = current_position.get("symbol", "UNKNOWN")
    challenger_symbol = challenger_candidate.get("symbol", "UNKNOWN")
    current_score = float(current_position.get("current_score") or current_position.get("entry_score") or 0.0)
    challenger_score = float(challenger_candidate.get("score") or challenger_candidate.get("new_signal_score") or 0.0)
    delta_score = challenger_score - current_score

    entry_ts = current_position.get("entry_ts") or current_position.get("ts")
    age_seconds = _age_seconds(entry_ts)
    if age_seconds <= 0 and current_position.get("age_hours") is not None:
        age_seconds = float(current_position["age_hours"]) * 3600

    regime_label = str(context.get("regime_label") or context.get("regime") or "UNKNOWN")
    posture = str(context.get("posture") or "NEUTRAL")

    uw_current = current_position.get("uw_flow_strength")
    uw_challenger = challenger_candidate.get("uw_flow_strength")
    dp_current = current_position.get("dark_pool_bias")
    dp_challenger = challenger_candidate.get("dark_pool_bias")

    diagnostics: Dict[str, Any] = {
        "current_symbol": current_symbol,
        "challenger_symbol": challenger_symbol,
        "current_score": round(current_score, 4),
        "challenger_score": round(challenger_score, 4),
        "delta_score": round(delta_score, 4),
        "current_entry_ts": str(entry_ts) if entry_ts else None,
        "age_seconds": round(age_seconds, 1),
        "regime_label": regime_label,
        "posture": posture,
        "uw_flow_strength_current": uw_current,
        "uw_flow_strength_challenger": uw_challenger,
        "dark_pool_bias_current": dp_current,
        "dark_pool_bias_challenger": dp_challenger,
        "note_missing_fields": [],
    }
    if uw_current is None and uw_challenger is None:
        diagnostics["note_missing_fields"].append("uw_flow_strength")
    if dp_current is None and dp_challenger is None:
        diagnostics["note_missing_fields"].append("dark_pool_bias")
    if not diagnostics["note_missing_fields"]:
        diagnostics["note_missing_fields"] = None

    if not enabled:
        diagnostics["allowed"] = False
        diagnostics["reason"] = "displacement_disabled"
        return False, "displacement_disabled", diagnostics

    # Emergency bypass: elite-tier (score < 3 or pnl < -0.5%) — no min hold.
    emergency = (
        current_score < 3.0
        or (isinstance(current_position.get("pnl_pct"), (int, float)) and float(current_position["pnl_pct"]) < -0.005)
    )
    if not emergency and age_seconds < min_hold:
        diagnostics["allowed"] = False
        diagnostics["reason"] = "displacement_min_hold"
        return False, "displacement_min_hold", diagnostics

    if delta_score < min_delta:
        diagnostics["allowed"] = False
        diagnostics["reason"] = "displacement_delta_too_small"
        return False, "displacement_delta_too_small", diagnostics

    if require_thesis:
        flow_win = False
        if uw_challenger is not None:
            if uw_current is None:
                flow_win = True
            else:
                flow_win = float(uw_challenger) >= float(uw_current) + _EPSILON
        regime_win = _regime_alignment_better(
            challenger_candidate.get("regime_label"),
            current_position.get("regime_label"),
            posture,
        )
        dp_win = False
        if dp_challenger is not None and dp_current is not None:
            # Same sign and challenger stronger
            try:
                dc, dch = float(dp_current), float(dp_challenger)
                dp_win = (dc * dch > 0) and (abs(dch) > abs(dc) + _EPSILON)
            except Exception:
                pass
        elif dp_challenger is not None and dp_current is None:
            dp_win = True
        if not (flow_win or regime_win or dp_win):
            diagnostics["allowed"] = False
            diagnostics["reason"] = "displacement_no_thesis_dominance"
            diagnostics["thesis_flow_win"] = flow_win
            diagnostics["thesis_regime_win"] = regime_win
            diagnostics["thesis_dp_win"] = dp_win
            return False, "displacement_no_thesis_dominance", diagnostics

    diagnostics["allowed"] = True
    diagnostics["reason"] = "displacement_allowed"
    return True, "displacement_allowed", diagnostics
