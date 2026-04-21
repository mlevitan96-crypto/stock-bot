"""
Canonical v2 composite component keys for strict ML cohort (Harvester era).

Must match uw_composite_v2._compute_composite_score_core ``components`` dict (minus path drift).
Used by alpaca_ml_flattener (normalize + fill) and alpaca_cohort_train (allowlist filter).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Order-stable; keep aligned with uw_composite_v2.py components block.
ML_CANONICAL_SCOREFLOW_COMPONENT_KEYS: tuple[str, ...] = (
    "flow",
    "dark_pool",
    "insider",
    "iv_skew",
    "smile",
    "whale",
    "event",
    "motif_bonus",
    "toxicity_penalty",
    "regime",
    "congress",
    "shorts_squeeze",
    "institutional",
    "market_tide",
    "calendar",
    "greeks_gamma",
    "ftd_pressure",
    "iv_rank",
    "oi_change",
    "etf_flow",
    "squeeze_score",
    "toxicity_correlation_penalty",
    "freshness_factor",
)


def mlf_scoreflow_component_column_names() -> List[str]:
    return [f"mlf_scoreflow_components_{k}" for k in ML_CANONICAL_SCOREFLOW_COMPONENT_KEYS]


# When older logs / snapshots used engine-internal names, coalesce into ML canonical keys
# (prevents silent 0.0 in mlf_scoreflow_components_* columns).
_SCOREFLOW_COMPONENT_ALIASES: Dict[str, tuple[str, ...]] = {
    # Legacy logs / snapshots may use iv_term_skew; uw_composite_v2 components dict uses iv_skew.
    "iv_skew": ("iv_term_skew",),
}


def _first_float_from_raw(raw: Dict[str, Any], keys: tuple[str, ...]) -> Optional[float]:
    for k in keys:
        if k not in raw:
            continue
        v = raw.get(k)
        if isinstance(v, dict):
            continue
        try:
            if v is None:
                continue
            f = float(v)
        except (TypeError, ValueError):
            continue
        if f == f:
            return f
    return None


def normalize_composite_components_for_ml(comp: Any) -> Dict[str, float]:
    """
    Map raw composite ``components`` to finite floats. Missing / NaN → 0.0
    (neutral contribution; not a price fabrication — scoreflow feature hygiene).
    """
    out: Dict[str, float] = {}
    raw = comp if isinstance(comp, dict) else {}
    for k in ML_CANONICAL_SCOREFLOW_COMPONENT_KEYS:
        aliases = (k,) + _SCOREFLOW_COMPONENT_ALIASES.get(k, ())
        picked = _first_float_from_raw(raw, aliases)
        if picked is None:
            out[k] = 0.0
        else:
            out[k] = picked
    return out
