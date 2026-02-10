"""
Signal evaluation contract for open positions.

Contract:
- evaluate_signal_for_symbol(symbol, context) -> (strength, evaluated, skip_reason).
- Always returns a float for strength (0.0 when skipped).
- Never silently skip: when data is missing, return evaluated=False and skip_reason.
- Caller must emit signal_strength_evaluated or signal_strength_skipped and persist cache.
"""

from __future__ import annotations

import logging
from typing import Any

LOG = logging.getLogger(__name__)


def evaluate_signal_for_symbol(
    symbol: str,
    context: dict[str, Any],
) -> tuple[float, bool, str | None]:
    """
    Evaluate current signal strength for a symbol (e.g. open position).

    context must contain:
      - uw_cache: dict (symbol -> enriched data)
      - regime: str (e.g. "mixed", "NEUTRAL")

    Returns:
      (strength, evaluated, skip_reason).
      - If evaluated is True: strength is the composite score, skip_reason is None.
      - If evaluated is False: strength is 0.0, skip_reason is the reason (e.g. "symbol_not_in_uw_cache").
    """
    uw_cache = context.get("uw_cache") or {}
    regime = context.get("regime", "mixed") or "mixed"

    if not isinstance(uw_cache, dict):
        LOG.warning("signal_open_position: uw_cache not a dict for %s", symbol)
        return (0.0, False, "uw_cache_invalid")

    if symbol not in uw_cache:
        LOG.debug("signal_open_position: no uw_cache entry for %s", symbol)
        return (0.0, False, "symbol_not_in_uw_cache")

    enriched = uw_cache.get(symbol)
    if not enriched or not isinstance(enriched, dict):
        LOG.debug("signal_open_position: empty enriched for %s", symbol)
        return (0.0, False, "no_enriched_data")

    try:
        import uw_enrichment_v2 as uw_enrich
        enriched_live = uw_enrich.enrich_signal(symbol, uw_cache, regime) or enriched
    except Exception as e:
        LOG.warning("signal_open_position: enrich_signal failed for %s: %s", symbol, e)
        enriched_live = enriched

    try:
        import uw_composite_v2 as uw_v2
        composite = uw_v2.compute_composite_score_v2(symbol, enriched_live, regime)
    except Exception as e:
        LOG.warning("signal_open_position: compute_composite_score_v2 failed for %s: %s", symbol, e)
        return (0.0, False, "composite_score_error")

    if not composite or not isinstance(composite, dict):
        return (0.0, False, "composite_empty")

    score = composite.get("score")
    if score is None:
        return (0.0, False, "composite_no_score")

    try:
        strength = float(score)
    except (TypeError, ValueError):
        return (0.0, False, "composite_score_not_numeric")

    LOG.info("signal_open_position: evaluated %s -> %.4f", symbol, strength)
    return (strength, True, None)
