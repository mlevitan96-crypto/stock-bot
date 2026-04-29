"""
Alpha 11 flow-strength: hard block floor + tiered entry sizing (Operation Apex).

**Gate (default — ensemble funnel):** Uses a **score-conditioned effective floor** so high
``composite_score`` tolerates lower UW ``flow_strength`` (and vice versa). Below that floor,
flow becomes a **notional multiplier** (soft penalty), not a series AND-veto, unless flow is
below ``ALPHA11_ABSOLUTE_FLOW_FLOOR`` (catastrophic / garbage tape) or legacy
``ALPHA11_FLOW_SERIES_VETO=1`` restores strict series blocking.

Missing / non-finite telemetry **allows** entry (fail-open).

**Sizing:** After the gate, notional may be scaled:
  - Tier 1: missing/invalid flow OR ``flow_strength >= ALPHA11_TIER1_FLOW_THRESHOLD`` → 1.0x
  - Tier 2: ``MIN_FLOW <= flow_strength < TIER1`` → ``ALPHA11_TIER2_SIZING_MULTIPLIER`` (default 0.5x)

Adjusted notional is clamped to at least ``min_notional_usd`` (broker / policy floor).

Configure:
  ALPHA11_FLOW_GATE_ENABLED          default 1  (set 0 to disable gate)
  ALPHA11_MIN_FLOW_STRENGTH          default 0.75 (regime base floor before dynamic relief)
  ALPHA11_FLOW_SERIES_VETO           default 0  (set 1 for legacy hard veto vs regime floor only)
  ALPHA11_DYNAMIC_FLOOR_ENABLED      default 1  (score lowers effective UW floor)
  ALPHA11_DYNAMIC_SCORE_LO           default 3.0  (at/below: use full regime floor)
  ALPHA11_DYNAMIC_SCORE_HI           default 6.5  (at/above: maximum floor relief applied)
  ALPHA11_DYNAMIC_FLOOR_SPAN         default 0.20  (max reduction from regime floor at HI score)
  ALPHA11_ABSOLUTE_FLOW_FLOOR        default 0.22  (below: hard block catastrophic_flow)
  ALPHA11_SOFT_MULT_FLOOR            default 0.28  (notional mult uses fs/max(eff_floor, this))
  ALPHA11_TIER1_FLOW_THRESHOLD       default 0.985 (full size at/above; missing → full)
  ALPHA11_TIER2_SIZING_MULTIPLIER    default 0.5
  ALPHA11_TIER_SIZING_ENABLED        default 1  (set 0 to skip multiplier; gate still applies)
"""

from __future__ import annotations

import math
import os
from typing import Any, Mapping, NamedTuple, Optional, Tuple


def _truthy_env(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _min_flow_strength() -> float:
    """Hard block below this strength (when flow is present and finite)."""
    raw = os.environ.get("ALPHA11_MIN_FLOW_STRENGTH", "0.75").strip()
    try:
        v = float(raw)
    except ValueError:
        return 0.75
    if not math.isfinite(v):
        return 0.75
    return v


def _tier1_flow_threshold() -> float:
    """Flow at/above this (or missing flow) → full 1.0x sizing."""
    raw = os.environ.get("ALPHA11_TIER1_FLOW_THRESHOLD", "0.985").strip()
    try:
        v = float(raw)
    except ValueError:
        return 0.985
    if not math.isfinite(v):
        return 0.985
    return v


def _tier2_sizing_multiplier() -> float:
    raw = os.environ.get("ALPHA11_TIER2_SIZING_MULTIPLIER", "0.5").strip()
    try:
        m = float(raw)
    except ValueError:
        return 0.5
    if not math.isfinite(m) or m <= 0.0:
        return 0.5
    return min(m, 1.0)


def _tier_sizing_enabled() -> bool:
    return _truthy_env("ALPHA11_TIER_SIZING_ENABLED", "1")


def alpha11_flow_tier_multiplier(flow_strength: Optional[float]) -> Tuple[float, str]:
    """
    Returns (multiplier, tier_label). Missing/non-finite → Tier 1 full size (fail-open).
    Never divides by flow_strength.
    """
    if not _tier_sizing_enabled():
        return 1.0, "tier_sizing_disabled"
    tier1 = _tier1_flow_threshold()
    if flow_strength is None:
        return 1.0, "tier1_missing_flow_full_size"
    try:
        fs = float(flow_strength)
    except (TypeError, ValueError):
        return 1.0, "tier1_non_numeric_flow_full_size"
    if not math.isfinite(fs):
        return 1.0, "tier1_non_finite_flow_full_size"
    if fs >= tier1:
        return 1.0, "tier1_high_flow"
    m2 = _tier2_sizing_multiplier()
    return m2, "tier2_reduced_flow"


def adjust_notional_for_alpha11_tier(
    notional_usd: float,
    *,
    symbol: str,
    composite_result: Optional[Mapping[str, Any]],
    composite_meta: Optional[Mapping[str, Any]],
    min_notional_usd: float,
) -> Tuple[float, Optional[float], float, str, bool]:
    """
    Apply tier multiplier then clamp to ``min_notional_usd``.

    Returns:
        (adjusted_notional, flow_strength_or_none, multiplier_used, tier_label, min_notional_clamped)
    """
    _ = symbol  # reserved for future per-symbol policy / logging context
    try:
        mn = float(min_notional_usd)
    except (TypeError, ValueError):
        mn = 0.0
    if not math.isfinite(mn) or mn < 0.0:
        mn = 0.0

    try:
        nt0 = float(notional_usd)
    except (TypeError, ValueError):
        nt0 = 0.0
    if not math.isfinite(nt0) or nt0 <= 0.0:
        out = mn if mn > 0.0 else nt0
        return out, None, 1.0, "tier_skip_invalid_notional", False

    fs = _extract_flow_strength(composite_result, composite_meta)
    mult, tier = alpha11_flow_tier_multiplier(fs)
    try:
        raw_adj = nt0 * float(mult)
    except (TypeError, ValueError, OverflowError):
        raw_adj = nt0
        mult, tier = 1.0, "tier_error_fallback_full_size"
    if not math.isfinite(raw_adj):
        raw_adj = nt0
        mult, tier = 1.0, "tier_error_fallback_full_size"

    if mn > 0.0:
        adj = max(raw_adj, mn)
        clamped = adj > raw_adj + 1e-9
    else:
        adj = raw_adj
        clamped = False

    if not math.isfinite(adj):
        adj = nt0
        clamped = False
    return adj, fs, float(mult), tier, clamped


def _flow_strength_from_uw(uw: Any) -> Optional[float]:
    if not isinstance(uw, dict):
        return None
    for k in ("flow_strength", "conviction"):
        v = uw.get(k)
        if v is None:
            continue
        try:
            f = float(v)
            if math.isfinite(f):
                return f
        except (TypeError, ValueError):
            continue
    return None


def _extract_flow_strength(
    composite_result: Optional[Mapping[str, Any]],
    composite_meta: Optional[Mapping[str, Any]],
) -> Optional[float]:
    for src in (composite_result, composite_meta):
        if not isinstance(src, dict):
            continue
        uw = src.get("v2_uw_inputs")
        fs = _flow_strength_from_uw(uw)
        if fs is not None:
            return fs
    return None


def _effective_flow_floor(regime_state: Optional[str]) -> float:
    """
    When ``REGIME_ENGINE_ENABLED=1``, adjust the Alpha 11 floor by continuous regime:
    - CHOP: raise floor (fade marginal breakouts; hysteresis lives in regime module).
    - MACRO_DOWNTREND: slightly relax floor (paired with LONG_ONLY / short policy elsewhere).
    """
    base = _min_flow_strength()
    if not _truthy_env("REGIME_ENGINE_ENABLED", "0"):
        return base
    r = str(regime_state or "TREND").strip().upper()
    if r == "CHOP":
        try:
            add = float(os.environ.get("ALPHA11_CHOP_FLOOR_ADD", "0.00").strip())
        except ValueError:
            add = 0.00
        return float(min(0.999, base + max(0.0, add)))
    if r == "MACRO_DOWNTREND":
        try:
            rel = float(os.environ.get("ALPHA11_MACRO_DOWNTREND_FLOOR_RELAX", "0.05").strip())
        except ValueError:
            rel = 0.05
        return float(max(0.5, base - max(0.0, rel)))
    return base


class Alpha11FunnelResult(NamedTuple):
    """Result of :func:`resolve_alpha11_entry_funnel`."""

    allowed: bool
    block_reason: Optional[str]
    flow_strength: Optional[float]
    effective_floor: float
    notional_mult: float
    policy: str


def _float_env(name: str, default: float) -> float:
    try:
        v = float(os.environ.get(name, str(default)).strip())
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def _dynamic_effective_floor(composite_score: float, regime_floor: float) -> float:
    """
    Lower the required UW flow when composite_score is high (ensemble complement).
    When disabled or score missing path not used, caller passes regime_floor unchanged.
    """
    if not _truthy_env("ALPHA11_DYNAMIC_FLOOR_ENABLED", "1"):
        return float(regime_floor)
    try:
        s = float(composite_score)
    except (TypeError, ValueError):
        return float(regime_floor)
    if not math.isfinite(s):
        return float(regime_floor)
    s_lo = _float_env("ALPHA11_DYNAMIC_SCORE_LO", 3.0)
    s_hi = _float_env("ALPHA11_DYNAMIC_SCORE_HI", 6.5)
    span = max(0.0, _float_env("ALPHA11_DYNAMIC_FLOOR_SPAN", 0.20))
    if s_hi <= s_lo:
        return float(regime_floor)
    t = (s - s_lo) / (s_hi - s_lo)
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    eff = float(regime_floor) - span * t
    abs_cap = _float_env("ALPHA11_ABSOLUTE_FLOW_FLOOR", 0.22)
    # Never relax below absolute tape floor (still above catastrophic hard block).
    return float(max(abs_cap, eff))


def _absolute_catastrophic_flow_floor() -> float:
    """Below this (when finite flow present): hard block regardless of score."""
    return max(0.0, min(0.5, _float_env("ALPHA11_ABSOLUTE_FLOW_FLOOR", 0.22) * 0.85))


def resolve_alpha11_entry_funnel(
    *,
    composite_score: Optional[float],
    composite_result: Optional[Mapping[str, Any]],
    composite_meta: Optional[Mapping[str, Any]],
    regime_state: Optional[str] = None,
) -> Alpha11FunnelResult:
    """
    Ensemble Alpha11 policy.

    - If ``composite_score`` is **None** (unit tests / legacy callers): strict regime-floor
      series veto (same as historical ``check_alpha11_flow_strength_gate``).
    - If ``composite_score`` is set (live ``main``): dynamic effective floor + soft notional
      multiplier instead of vetoing strong AI + mediocre flow.

    ``ALPHA11_FLOW_SERIES_VETO=1`` forces legacy hard veto vs regime floor even when score is set.
    """
    if not _truthy_env("ALPHA11_FLOW_GATE_ENABLED", "1"):
        return Alpha11FunnelResult(True, None, None, _min_flow_strength(), 1.0, "gate_disabled")

    fs = _extract_flow_strength(composite_result, composite_meta)
    regime_floor = _effective_flow_floor(regime_state)

    if fs is None:
        return Alpha11FunnelResult(
            True,
            "alpha11_flow_skipped_missing_flow_strength",
            None,
            float(regime_floor),
            1.0,
            "missing_flow_fail_open",
        )

    cat = _absolute_catastrophic_flow_floor()
    if math.isfinite(fs) and fs < cat:
        return Alpha11FunnelResult(
            False,
            "alpha11_flow_strength_catastrophic",
            float(fs),
            float(regime_floor),
            1.0,
            "catastrophic_hard_block",
        )

    # Legacy series veto: tests omit composite_score; operators can set ALPHA11_FLOW_SERIES_VETO=1.
    if composite_score is None or _truthy_env("ALPHA11_FLOW_SERIES_VETO", "0"):
        if fs < regime_floor:
            return Alpha11FunnelResult(
                False,
                "alpha11_flow_strength_below_gate",
                float(fs),
                float(regime_floor),
                1.0,
                "series_veto_legacy",
            )
        return Alpha11FunnelResult(True, None, float(fs), float(regime_floor), 1.0, "series_pass")

    try:
        sc = float(composite_score)
    except (TypeError, ValueError):
        sc = float("nan")
    if not math.isfinite(sc):
        if fs < regime_floor:
            return Alpha11FunnelResult(
                False,
                "alpha11_flow_strength_below_gate",
                float(fs),
                float(regime_floor),
                1.0,
                "series_veto_bad_score",
            )
        return Alpha11FunnelResult(True, None, float(fs), float(regime_floor), 1.0, "series_pass_bad_score")

    eff = _dynamic_effective_floor(sc, regime_floor)
    if fs >= eff:
        return Alpha11FunnelResult(True, None, float(fs), float(eff), 1.0, "dynamic_pass")

    soft_den = max(
        eff,
        _float_env("ALPHA11_SOFT_MULT_FLOOR", 0.28),
        1e-9,
    )
    mult = max(0.25, min(1.0, float(fs) / float(soft_den)))
    return Alpha11FunnelResult(
        True,
        None,
        float(fs),
        float(eff),
        float(mult),
        "dynamic_soft_scale",
    )


def check_alpha11_flow_strength_gate(
    *,
    symbol: str,
    composite_result: Optional[Mapping[str, Any]],
    composite_meta: Optional[Mapping[str, Any]],
    regime_state: Optional[str] = None,
    composite_score: Optional[float] = None,
) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Returns (allowed, block_reason_or_none, flow_strength_or_none).

    When ``composite_score`` is provided, delegates to :func:`resolve_alpha11_entry_funnel`
    (dynamic floor + soft multiplier path). When omitted, uses strict legacy series gate
    (unit-test compatible).
    """
    _ = symbol
    r = resolve_alpha11_entry_funnel(
        composite_score=composite_score,
        composite_result=composite_result,
        composite_meta=composite_meta,
        regime_state=regime_state,
    )
    if not r.allowed:
        return False, r.block_reason, r.flow_strength
    # Skipped / pass: preserve fail-open telemetry reason string when missing flow
    br = r.block_reason if r.flow_strength is None else None
    return True, br, r.flow_strength
