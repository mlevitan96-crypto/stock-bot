"""
Thesis tags: derive WHY a trade was taken from feature snapshots.

Contract:
- derive_thesis_tags(snapshot) -> dict
- All tags explicit; missing data => None (never silently False).
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def _safe_float(x: Any, default: Optional[float] = None) -> Optional[float]:
    if x is None:
        return default
    try:
        v = float(x)
        if v != v:  # NaN
            return default
        return v
    except Exception:
        return default


def _safe_bool(x: Any) -> Optional[bool]:
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return bool(x)
    return None


def derive_thesis_tags(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Derive thesis tags from a feature snapshot.

    Args:
        snapshot: from build_feature_snapshot (symbol, v2_score, uw_flow_*, dark_pool_*,
                  regime_label, posture, premarket_*, congress_*, insider_*, etc.)

    Returns:
        Dict of thesis tags. Missing => None.
    """
    out: Dict[str, Any] = {
        "thesis_flow_continuation": None,
        "thesis_flow_reversal": None,
        "thesis_dark_pool_accumulation": None,
        "thesis_dark_pool_distribution": None,
        "thesis_premarket_gap_continuation": None,
        "thesis_event_earnings_drift": None,
        "thesis_congress_tailwind": None,
        "thesis_insider_tailwind": None,
        "thesis_regime_alignment_score": None,
        "thesis_vol_expansion": None,
        "thesis_vol_compression": None,
    }
    if not snapshot:
        return out

    flow_strength = _safe_float(snapshot.get("uw_flow_strength"))
    flow_dir = (snapshot.get("uw_flow_direction") or snapshot.get("flow_direction") or "").lower()
    flow_reversal = snapshot.get("flow_reversal")
    dp_bias = _safe_float(snapshot.get("dark_pool_bias"))
    dp_activity = snapshot.get("dark_pool_activity")
    premarket_gap = _safe_float(snapshot.get("premarket_gap"))
    premarket_relvol = _safe_float(snapshot.get("premarket_relvol"))
    earnings_days = snapshot.get("earnings_days_away")
    congress = snapshot.get("congress_recent_flag")
    insider = snapshot.get("insider_recent_flag")
    regime_label = (snapshot.get("regime_label") or "").lower()
    posture = (snapshot.get("posture") or "").lower()
    vol_20d = _safe_float(snapshot.get("realized_vol_20d"))
    side_bias = (snapshot.get("side_bias") or "").lower()

    # Flow continuation: flow strength present and aligned (bullish flow for long, bearish for short)
    if flow_strength is not None and flow_strength > 0:
        if flow_dir in ("bullish", "long") or (not flow_dir and flow_strength > 0):
            out["thesis_flow_continuation"] = True
        elif flow_dir in ("bearish", "short"):
            out["thesis_flow_continuation"] = False
        else:
            out["thesis_flow_continuation"] = True  # default if strength present
    elif flow_reversal is not None:
        out["thesis_flow_continuation"] = not bool(flow_reversal)

    # Flow reversal: explicit flag
    out["thesis_flow_reversal"] = _safe_bool(flow_reversal) if flow_reversal is not None else None

    # Dark pool accumulation (positive bias) / distribution (negative)
    if dp_bias is not None:
        out["thesis_dark_pool_accumulation"] = dp_bias > 0
        out["thesis_dark_pool_distribution"] = dp_bias < 0
    elif dp_activity is not None:
        try:
            a = str(dp_activity).lower()
            out["thesis_dark_pool_accumulation"] = "accum" in a or "buy" in a
            out["thesis_dark_pool_distribution"] = "dist" in a or "sell" in a
        except Exception:
            pass

    # Premarket gap continuation: gap present and relvol present (simplified)
    if premarket_gap is not None and premarket_relvol is not None and premarket_relvol > 0:
        out["thesis_premarket_gap_continuation"] = abs(premarket_gap) > 0.001
    elif premarket_gap is not None:
        out["thesis_premarket_gap_continuation"] = abs(premarket_gap) > 0.001

    # Earnings drift: earnings_days_away in window (e.g. 0–5 days)
    if earnings_days is not None:
        try:
            d = int(earnings_days) if isinstance(earnings_days, (int, float)) else int(float(earnings_days))
            out["thesis_event_earnings_drift"] = 0 <= d <= 5
        except Exception:
            out["thesis_event_earnings_drift"] = None
    else:
        out["thesis_event_earnings_drift"] = None

    # Congress / insider tailwind
    out["thesis_congress_tailwind"] = _safe_bool(congress) if congress is not None else None
    out["thesis_insider_tailwind"] = _safe_bool(insider) if insider is not None else None

    # Regime alignment score (0–1). Map regime+posture to scalar.
    if regime_label or posture:
        s = 0.5
        if regime_label in ("bull", "risk_on"):
            s = 0.8 if posture in ("bullish", "long") else 0.4
        elif regime_label in ("bear", "risk_off", "crash"):
            s = 0.2 if posture in ("bearish", "short") else 0.6
        elif regime_label in ("chop", "mixed", "neutral"):
            s = 0.5
        out["thesis_regime_alignment_score"] = round(s, 2)
    else:
        out["thesis_regime_alignment_score"] = None

    # Vol expansion / compression (vs typical; we have no baseline, use simple heuristic)
    if vol_20d is not None:
        # Arbitrary: >0.4 as expansion, <0.15 as compression
        out["thesis_vol_expansion"] = vol_20d > 0.4
        out["thesis_vol_compression"] = vol_20d < 0.15
    else:
        out["thesis_vol_expansion"] = None
        out["thesis_vol_compression"] = None

    return out
