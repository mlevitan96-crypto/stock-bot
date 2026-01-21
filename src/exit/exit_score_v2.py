#!/usr/bin/env python3
"""
Composite Exit Score (v2, shadow-only)
=====================================

Computes an exit_score and recommended exit reason from:
- UW deterioration (flow/darkpool/sentiment)
- Sector/regime shifts
- Score deterioration (entry vs now)
- Relative strength deterioration (placeholder/best-effort)
- Volatility expansion (best-effort)
- Thesis invalidation flags (from pre/postmarket exit intel, optional)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def _clamp(x: float, lo: float, hi: float) -> float:
    try:
        return max(float(lo), min(float(hi), float(x)))
    except Exception:
        return float(lo)


def compute_exit_score_v2(
    *,
    symbol: str,
    direction: str,
    entry_v2_score: float,
    now_v2_score: float,
    entry_uw_inputs: Dict[str, Any],
    now_uw_inputs: Dict[str, Any],
    entry_regime: str,
    now_regime: str,
    entry_sector: str,
    now_sector: str,
    realized_vol_20d: Optional[float] = None,
    thesis_flags: Optional[Dict[str, Any]] = None,
) -> Tuple[float, Dict[str, Any], str]:
    """
    Returns (exit_score [0..1], components, recommended_reason)
    """
    entry_flow = float((entry_uw_inputs or {}).get("flow_strength", 0.0) or 0.0)
    now_flow = float((now_uw_inputs or {}).get("flow_strength", 0.0) or 0.0)
    entry_dp = float((entry_uw_inputs or {}).get("darkpool_bias", 0.0) or 0.0)
    now_dp = float((now_uw_inputs or {}).get("darkpool_bias", 0.0) or 0.0)
    entry_sent = str((entry_uw_inputs or {}).get("sentiment", "NEUTRAL") or "NEUTRAL").upper()
    now_sent = str((now_uw_inputs or {}).get("sentiment", "NEUTRAL") or "NEUTRAL").upper()

    # Deterioration terms are positive when things get worse.
    flow_det = _clamp(entry_flow - now_flow, 0.0, 1.0)
    dp_det = _clamp(abs(entry_dp) - abs(now_dp), 0.0, 1.0)
    sent_det = 1.0 if (entry_sent != "NEUTRAL" and now_sent == "NEUTRAL") else (1.0 if entry_sent != now_sent else 0.0)

    score_det = _clamp(float(entry_v2_score) - float(now_v2_score), 0.0, 8.0) / 8.0

    # Regime / sector shift (binary-ish)
    r_shift = 1.0 if str(entry_regime).upper() != str(now_regime).upper() else 0.0
    s_shift = 1.0 if str(entry_sector).upper() != str(now_sector).upper() else 0.0

    # Vol expansion proxy (best-effort)
    vol = float(realized_vol_20d or 0.0)
    vol_exp = _clamp((vol - 0.35) / 0.25, 0.0, 1.0) if vol > 0 else 0.0

    # Thesis flags
    tf = thesis_flags or {}
    thesis_bad = 1.0 if bool(tf.get("thesis_invalidated")) else 0.0
    earnings_risk = 1.0 if bool(tf.get("earnings_risk")) else 0.0
    overnight_risk = 1.0 if bool(tf.get("overnight_flow_risk")) else 0.0

    # Weighted combination (conservative)
    components = {
        "flow_deterioration": round(flow_det, 4),
        "darkpool_deterioration": round(dp_det, 4),
        "sentiment_deterioration": round(sent_det, 4),
        "score_deterioration": round(score_det, 4),
        "regime_shift": round(r_shift, 4),
        "sector_shift": round(s_shift, 4),
        "vol_expansion": round(vol_exp, 4),
        "thesis_invalidated": round(thesis_bad, 4),
        "earnings_risk": round(earnings_risk, 4),
        "overnight_flow_risk": round(overnight_risk, 4),
    }

    score = (
        0.20 * flow_det
        + 0.10 * dp_det
        + 0.10 * sent_det
        + 0.25 * score_det
        + 0.10 * r_shift
        + 0.05 * s_shift
        + 0.10 * vol_exp
        + 0.10 * thesis_bad
    )
    score = _clamp(score, 0.0, 1.0)

    # Recommended reason
    reason = "hold"
    if thesis_bad >= 1.0:
        reason = "intel_deterioration"
    elif score_det >= 0.35:
        reason = "intel_deterioration"
    elif vol_exp >= 0.8 and score >= 0.6:
        reason = "stop"
    elif earnings_risk >= 1.0 and score >= 0.5:
        reason = "stop"
    elif score >= 0.75:
        reason = "replacement"
    elif score >= 0.55:
        reason = "profit"

    return float(score), components, reason

