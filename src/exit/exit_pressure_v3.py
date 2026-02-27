"""
Exit Pressure (v3) — Multi-factor continuous exit decision engine.

Computes a single ExitPressureScore in [0, 1] from multiple components.
Primary trigger: exit_pressure >= EXIT_PRESSURE_NORMAL (or URGENT).
Hard overrides (stop loss, compliance, etc.) remain in the caller and always win.

Contract:
- Read-only: MUST NOT place orders.
- Safe-by-default: missing inputs -> conservative (low pressure).
- All outputs suitable for truth logging (components, thresholds, decision).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

# Default weights (overridable via env/config)
_DEFAULT_WEIGHTS = {
    "signal_deterioration": 0.22,
    "flow_reversal": 0.12,
    "regime_risk": 0.10,
    "position_risk": 0.18,
    "time_decay": 0.12,
    "profit_protection": 0.14,
    "crowding_risk": 0.06,
    "price_action": 0.06,
}


def _clamp(x: float, lo: float, hi: float) -> float:
    try:
        return max(float(lo), min(float(hi), float(x)))
    except Exception:
        return float(lo)


def _get_float_env(name: str, default: float) -> float:
    try:
        v = os.environ.get(name)
        return float(v) if v is not None else default
    except Exception:
        return default


def compute_exit_pressure(
    *,
    symbol: str,
    direction: str,
    entry_v2_score: float,
    now_v2_score: float,
    entry_uw_inputs: Optional[Dict[str, Any]] = None,
    now_uw_inputs: Optional[Dict[str, Any]] = None,
    entry_regime: str = "NEUTRAL",
    now_regime: str = "NEUTRAL",
    entry_sector: str = "UNKNOWN",
    now_sector: str = "UNKNOWN",
    realized_vol_20d: Optional[float] = None,
    thesis_flags: Optional[Dict[str, Any]] = None,
    # Position / PnL
    pnl_pct: Optional[float] = None,
    high_water_pct: Optional[float] = None,
    mfe_pct: Optional[float] = None,
    mae_pct: Optional[float] = None,
    giveback_from_mfe: Optional[float] = None,
    age_minutes: Optional[float] = None,
    # Thresholds (env overrides)
    threshold_normal: Optional[float] = None,
    threshold_urgent: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[
    float,
    str,
    List[Dict[str, Any]],
    str,
    str,
    List[Dict[str, Any]],
]:
    """
    Returns:
        (exit_pressure [0..1], decision, components_for_log, close_reason, exit_reason_code, attribution_components)
    decision: HOLD | CLOSE_NORMAL | CLOSE_URGENT
    """
    entry_uw = entry_uw_inputs or {}
    now_uw = now_uw_inputs or {}
    w = weights or _DEFAULT_WEIGHTS

    thr_norm = threshold_normal if threshold_normal is not None else _get_float_env("EXIT_PRESSURE_NORMAL", 0.55)
    thr_urgent = threshold_urgent if threshold_urgent is not None else _get_float_env("EXIT_PRESSURE_URGENT", 0.80)

    # --- 1) Signal deterioration (conviction decay, composite slope)
    score_det = _clamp(float(entry_v2_score or 0) - float(now_v2_score or 0), 0.0, 8.0) / 8.0
    entry_flow = float(entry_uw.get("flow_strength", 0) or 0)
    now_flow = float(now_uw.get("flow_strength", 0) or 0)
    flow_det = _clamp(entry_flow - now_flow, 0.0, 1.0)
    signal_deterioration = _clamp(0.6 * score_det + 0.4 * flow_det, 0.0, 1.0)

    # --- 2) Flow reversal (sentiment flip, dark pool flip)
    entry_sent = str(entry_uw.get("sentiment", "NEUTRAL") or "NEUTRAL").upper()
    now_sent = str(now_uw.get("sentiment", "NEUTRAL") or "NEUTRAL").upper()
    sent_flip = 1.0 if (entry_sent != "NEUTRAL" and now_sent != entry_sent) else 0.0
    entry_dp = float(entry_uw.get("darkpool_bias", 0) or 0)
    now_dp = float(now_uw.get("darkpool_bias", 0) or 0)
    dp_flip = 1.0 if (entry_dp * now_dp < 0 and entry_dp != 0) else 0.0
    flow_reversal = _clamp(sent_flip * 0.6 + dp_flip * 0.4, 0.0, 1.0)

    # --- 3) Regime risk (vol, regime shift, sector shift)
    r_shift = 1.0 if str(entry_regime or "").upper() != str(now_regime or "").upper() else 0.0
    s_shift = 1.0 if str(entry_sector or "").upper() != str(now_sector or "").upper() else 0.0
    vol = float(realized_vol_20d or 0)
    vol_exp = _clamp((vol - 0.35) / 0.25, 0.0, 1.0) if vol > 0 else 0.0
    regime_risk = _clamp(0.4 * r_shift + 0.2 * s_shift + 0.4 * vol_exp, 0.0, 1.0)

    # --- 4) Position risk (drawdown from high water, MAE)
    pnl_decimal = (float(pnl_pct or 0) / 100.0) if pnl_pct is not None else 0.0
    hw = float(high_water_pct or 0) / 100.0 if high_water_pct is not None else 0.0
    drawdown = _clamp(hw - pnl_decimal, 0.0, 1.0) if hw > 0 else 0.0
    mae = abs(float(mae_pct or 0)) / 100.0 if mae_pct is not None else 0.0
    position_risk = _clamp(0.5 * drawdown + 0.5 * min(mae, 1.0), 0.0, 1.0)

    # --- 5) Time decay / opportunity cost (stagnation)
    age_min = float(age_minutes or 0)
    # Normalize: after 120 min, time pressure ramps to 1
    time_decay = _clamp(age_min / 120.0, 0.0, 1.0) if age_min > 0 else 0.0

    # --- 6) Profit protection (giveback from MFE as pressure)
    gb = float(giveback_from_mfe or 0) if giveback_from_mfe is not None else 0.0
    mfe = float(mfe_pct or 0) / 100.0 if mfe_pct is not None else 0.0
    profit_protection = 0.0
    if mfe > 0 and gb > 0:
        profit_protection = _clamp(gb / mfe, 0.0, 1.0)

    # --- 7) Crowding / squeeze (placeholder: use FTD/shorts if in uw later)
    crowding_risk = 0.0

    # --- 8) Price action (trend break / momentum stall placeholder)
    price_action = 0.0

    # Thesis flags (fold into signal_deterioration or regime)
    tf = thesis_flags or {}
    thesis_bad = 1.0 if bool(tf.get("thesis_invalidated")) else 0.0
    earnings_risk = 1.0 if bool(tf.get("earnings_risk")) else 0.0
    signal_deterioration = _clamp(signal_deterioration + 0.3 * thesis_bad + 0.2 * earnings_risk, 0.0, 1.0)

    # Weighted pressure
    pressure = (
        w.get("signal_deterioration", 0.22) * signal_deterioration
        + w.get("flow_reversal", 0.12) * flow_reversal
        + w.get("regime_risk", 0.10) * regime_risk
        + w.get("position_risk", 0.18) * position_risk
        + w.get("time_decay", 0.12) * time_decay
        + w.get("profit_protection", 0.14) * profit_protection
        + w.get("crowding_risk", 0.06) * crowding_risk
        + w.get("price_action", 0.06) * price_action
    )
    pressure = _clamp(pressure, 0.0, 1.0)

    # Decision
    decision = "HOLD"
    if pressure >= thr_urgent:
        decision = "CLOSE_URGENT"
    elif pressure >= thr_norm:
        decision = "CLOSE_NORMAL"

    # Exit reason code (taxonomy)
    exit_reason_code = "hold"
    if decision != "HOLD":
        if thesis_bad >= 1.0 or score_det >= 0.35:
            exit_reason_code = "intel_deterioration"
        elif regime_risk >= 0.6 and pressure >= 0.6:
            exit_reason_code = "stop"
        elif pressure >= 0.75:
            exit_reason_code = "replacement"
        elif pressure >= 0.55:
            exit_reason_code = "profit"
        else:
            exit_reason_code = "pressure_exit"

    # Components for truth log (name, value, weight, contribution)
    comp_list = [
        {"name": "signal_deterioration", "value": round(signal_deterioration, 4), "weight": w.get("signal_deterioration", 0.22), "contribution": round(w.get("signal_deterioration", 0.22) * signal_deterioration, 4)},
        {"name": "flow_reversal", "value": round(flow_reversal, 4), "weight": w.get("flow_reversal", 0.12), "contribution": round(w.get("flow_reversal", 0.12) * flow_reversal, 4)},
        {"name": "regime_risk", "value": round(regime_risk, 4), "weight": w.get("regime_risk", 0.10), "contribution": round(w.get("regime_risk", 0.10) * regime_risk, 4)},
        {"name": "position_risk", "value": round(position_risk, 4), "weight": w.get("position_risk", 0.18), "contribution": round(w.get("position_risk", 0.18) * position_risk, 4)},
        {"name": "time_decay", "value": round(time_decay, 4), "weight": w.get("time_decay", 0.12), "contribution": round(w.get("time_decay", 0.12) * time_decay, 4)},
        {"name": "profit_protection", "value": round(profit_protection, 4), "weight": w.get("profit_protection", 0.14), "contribution": round(w.get("profit_protection", 0.14) * profit_protection, 4)},
        {"name": "crowding_risk", "value": round(crowding_risk, 4), "weight": w.get("crowding_risk", 0.06), "contribution": 0.0},
        {"name": "price_action", "value": round(price_action, 4), "weight": w.get("price_action", 0.06), "contribution": 0.0},
    ]

    # Attribution components (schema: signal_id, contribution_to_score)
    attribution = [
        {"signal_id": c["name"], "contribution_to_score": c["contribution"]} for c in comp_list
    ]

    # Composite close reason string (for display)
    parts = []
    if signal_deterioration >= 0.3:
        parts.append(f"signal_decay({score_det:.2f})")
    if flow_reversal >= 0.5:
        parts.append("flow_reversal")
    if regime_risk >= 0.5:
        parts.append("regime_risk")
    if position_risk >= 0.4:
        parts.append(f"drawdown({drawdown:.2f})")
    if time_decay >= 0.5:
        parts.append(f"time_decay({age_min:.0f}m)")
    if profit_protection >= 0.3:
        parts.append("profit_protection")
    close_reason = "+".join(parts) if parts else f"pressure({pressure:.2f})"

    return (
        round(pressure, 4),
        decision,
        comp_list,
        close_reason,
        exit_reason_code,
        attribution,
    )
