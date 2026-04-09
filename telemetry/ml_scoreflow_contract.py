"""
Canonical v2 composite component keys for strict ML cohort (Harvester era).

Must match uw_composite_v2._compute_composite_score_core ``components`` dict (minus path drift).
Used by alpaca_ml_flattener (normalize + fill) and alpaca_cohort_train (allowlist filter).
"""
from __future__ import annotations

from typing import Any, Dict, List

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
    "freshness_factor",
)


def mlf_scoreflow_component_column_names() -> List[str]:
    return [f"mlf_scoreflow_components_{k}" for k in ML_CANONICAL_SCOREFLOW_COMPONENT_KEYS]


def normalize_composite_components_for_ml(comp: Any) -> Dict[str, float]:
    """
    Map raw composite ``components`` to finite floats. Missing / NaN → 0.0
    (neutral contribution; not a price fabrication — scoreflow feature hygiene).
    """
    out: Dict[str, float] = {}
    raw = comp if isinstance(comp, dict) else {}
    for k in ML_CANONICAL_SCOREFLOW_COMPONENT_KEYS:
        v = raw.get(k)
        try:
            if v is None:
                out[k] = 0.0
                continue
            f = float(v)
            if f != f:  # NaN
                out[k] = 0.0
            else:
                out[k] = f
        except (TypeError, ValueError):
            out[k] = 0.0
    return out
