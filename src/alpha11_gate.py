"""
Alpha 11 flow-strength: hard block floor + tiered entry sizing (Operation Apex).

**Gate:** Blocks when persisted UW ``flow_strength`` (or ``conviction``) is strictly
below ``ALPHA11_MIN_FLOW_STRENGTH``. Missing / non-finite telemetry **allows** entry
(fail-open) so partial UW payloads do not brick the book.

**Sizing:** After the gate, notional may be scaled:
  - Tier 1: missing/invalid flow OR ``flow_strength >= ALPHA11_TIER1_FLOW_THRESHOLD`` → 1.0x
  - Tier 2: ``MIN_FLOW <= flow_strength < TIER1`` → ``ALPHA11_TIER2_SIZING_MULTIPLIER`` (default 0.5x)

Adjusted notional is clamped to at least ``min_notional_usd`` (broker / policy floor).

Configure:
  ALPHA11_FLOW_GATE_ENABLED          default 1  (set 0 to disable gate)
  ALPHA11_MIN_FLOW_STRENGTH          default 0.90 (hard block below this)
  ALPHA11_TIER1_FLOW_THRESHOLD       default 0.985 (full size at/above; missing → full)
  ALPHA11_TIER2_SIZING_MULTIPLIER    default 0.5
  ALPHA11_TIER_SIZING_ENABLED        default 1  (set 0 to skip multiplier; gate still applies)
"""

from __future__ import annotations

import math
import os
from typing import Any, Mapping, Optional, Tuple


def _truthy_env(name: str, default: str = "1") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


def _min_flow_strength() -> float:
    """Hard block below this strength (when flow is present and finite)."""
    raw = os.environ.get("ALPHA11_MIN_FLOW_STRENGTH", "0.90").strip()
    try:
        v = float(raw)
    except ValueError:
        return 0.90
    if not math.isfinite(v):
        return 0.90
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


def check_alpha11_flow_strength_gate(
    *,
    symbol: str,
    composite_result: Optional[Mapping[str, Any]],
    composite_meta: Optional[Mapping[str, Any]],
) -> Tuple[bool, Optional[str], Optional[float]]:
    """
    Returns (allowed, block_reason_or_none, flow_strength_or_none).

    Disabled → allow. Missing flow → allow with reason ``alpha11_flow_skipped``.
    Below floor → block ``alpha11_flow_strength_below_gate``.
    """
    if not _truthy_env("ALPHA11_FLOW_GATE_ENABLED", "1"):
        return True, None, None

    fs = _extract_flow_strength(composite_result, composite_meta)
    if fs is None:
        return True, "alpha11_flow_skipped_missing_flow_strength", None

    floor = _min_flow_strength()
    if fs < floor:
        return False, "alpha11_flow_strength_below_gate", fs
    return True, None, fs
