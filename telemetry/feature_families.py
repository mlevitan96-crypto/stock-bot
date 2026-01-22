"""
Feature families (telemetry-only)
================================

Used by telemetry builders to group signals into coarse "families" for:
- score distribution curves
- parity deltas by family
- replacement telemetry summaries

Contract:
- Read-only helpers (no I/O).
- Best-effort: unknown keys map to "other" / "unknown".
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set


FAMILY_UNKNOWN = "unknown"
FAMILY_OTHER = "other"

# Coarse families (kept small on purpose).
FEATURE_FAMILIES: List[str] = [
    "flow",
    "darkpool",
    "sentiment",
    "earnings",
    "alignment",
    "greeks",
    "volatility",
    "regime",
    "event",
    "short_interest",
    "etf_flow",
    "calendar",
    "toxicity",
    FAMILY_OTHER,
    FAMILY_UNKNOWN,
]


def _absf(v: Any) -> float:
    try:
        return abs(float(v))
    except Exception:
        return 0.0


def v2_family_for_key(k: str) -> str:
    kk = str(k or "").strip().lower()
    if kk in ("flow_strength", "flow"):
        return "flow"
    if kk in ("darkpool_bias", "dark_pool", "darkpool"):
        return "darkpool"
    if kk in ("sentiment",):
        return "sentiment"
    if kk in ("earnings_proximity", "earnings"):
        return "earnings"
    if kk in ("sector_alignment", "regime_alignment", "alignment"):
        return "alignment"
    if kk in ("realized_vol_5d", "realized_vol_20d", "beta_vs_spy"):
        return "volatility"
    return FAMILY_OTHER


def v1_family_for_component_key(k: str) -> str:
    kk = str(k or "").strip().lower()
    if kk in ("flow", "flow_count", "flow_premium"):
        return "flow"
    if kk in ("dark_pool", "darkpool"):
        return "darkpool"
    if kk in ("whale",):
        return "flow"
    if kk in ("event", "motif_bonus"):
        return "event"
    if kk in ("regime", "market_tide", "gamma_regime"):
        return "regime"
    if kk in ("calendar",):
        return "calendar"
    if kk in ("greeks_gamma",):
        return "greeks"
    if kk in ("iv_skew", "smile", "iv_rank"):
        return "volatility"
    if kk in ("oi_change", "ftd_pressure"):
        return "flow"
    if kk in ("etf_flow",):
        return "etf_flow"
    if kk in ("shorts_squeeze", "squeeze_score"):
        return "short_interest"
    if kk in ("toxicity_penalty",):
        return "toxicity"
    if kk in ("insider", "congress", "institutional"):
        return "event"
    return FAMILY_OTHER


def active_v2_families_from_adjustments(adjustments: Any) -> Set[str]:
    fams: Set[str] = set()
    if not isinstance(adjustments, dict):
        return fams
    for k, v in adjustments.items():
        if str(k) == "total":
            continue
        if _absf(v) <= 1e-9:
            continue
        fams.add(v2_family_for_key(str(k)))
    return fams


def dominant_v1_family_from_components(components: Any) -> str:
    if not isinstance(components, dict) or not components:
        return FAMILY_UNKNOWN
    best_family = FAMILY_UNKNOWN
    best_mag = 0.0
    for k, v in components.items():
        fam = v1_family_for_component_key(str(k))
        mag = _absf(v)
        if mag > best_mag:
            best_mag = mag
            best_family = fam
    return best_family


def families_from_tags(tags: Iterable[str]) -> List[str]:
    out: List[str] = []
    for t in tags:
        tt = str(t or "").strip()
        if not tt:
            continue
        out.append(tt)
    return out

