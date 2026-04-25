"""
Regime-modulated max concurrent positions (slot elasticity).

Reads ``regime_posture_v2`` snapshot (typically from ``state/regime_posture_state.json`` via
``read_regime_posture_state``). Does **not** fetch broker data; optional BP clamp left to callers.

Contract: regime is a **modifier** only (see ``docs/CAPACITY_AND_DISPLACEMENT.md``).
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def resolve_effective_max_slots(
    *,
    base_cap: int,
    enabled: bool,
    chop_max: int,
    neutral_max: int,
    trend_max: int,
    crash_max: int,
    ladder_conf: float,
    regime_posture: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Return effective max open slots.

    - **base_cap:** env ``MAX_CONCURRENT_POSITIONS`` (center / paper default).
    - **chop / neutral / trend / crash:** hard ceilings per regime bucket.
    """
    base = max(1, int(base_cap))
    if not enabled:
        return base

    rp = regime_posture if isinstance(regime_posture, dict) else {}
    label = str(rp.get("regime_label") or "chop").lower().strip()
    conf = float(rp.get("regime_confidence") or 0.0)
    posture = str(rp.get("posture") or "neutral").lower().strip()

    # Crash: consolidate hard.
    if label == "crash":
        return max(1, min(base, int(crash_max)))

    # Trend / high-opportunity: expand when confident bull or bear with directional posture.
    if label == "bull" and conf >= ladder_conf and posture == "long":
        return max(1, min(int(trend_max), max(base, int(trend_max))))
    if label == "bear" and conf >= ladder_conf and posture == "short":
        return max(1, min(int(trend_max), max(base, int(trend_max))))

    # Chop-like: consolidate.
    if label in ("chop",):
        return max(1, min(base, int(chop_max)))

    # Neutral / unknown: middle rail.
    return max(1, min(base, int(neutral_max)))
