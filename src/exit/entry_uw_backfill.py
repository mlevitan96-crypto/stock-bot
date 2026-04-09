"""
Best-effort reconstruction of v2_uw_inputs at exit when position_metadata lost the v2 blob.

Uses the same UW cache + composite path as live exit scoring (no fabricated prices).
Never raises; returns {} on failure.
"""
from __future__ import annotations

from typing import Any, Dict


def _normalize_regime(reg: str) -> str:
    r = str(reg or "").strip().upper()
    if not r or r == "UNKNOWN":
        return "NEUTRAL"
    return r


def try_backfill_v2_uw_inputs(symbol: str, regime_label: str = "NEUTRAL") -> Dict[str, Any]:
    """
    Recompute v2_uw_inputs from data/uw_flow_cache.json + uw_composite_score_v2.

    Mirrors main.py exit-loop enrichment so exit_attribution rows stay telemetry-dense
    when mark_open omitted v2 (reconcile gap, partial metadata, etc.).
    """
    sym = str(symbol or "").upper().strip()
    if not sym:
        return {}
    regime = _normalize_regime(regime_label)
    try:
        from config.registry import CacheFiles, read_json

        uw_cache = read_json(CacheFiles.UW_FLOW_CACHE, default={})
        if not isinstance(uw_cache, dict):
            uw_cache = {}
        enriched: Dict[str, Any] = dict(uw_cache.get(sym, {}) or {})
        try:
            import uw_enrichment_v2 as uw_enrich

            enriched_live = uw_enrich.enrich_signal(sym, uw_cache, regime) or enriched
            if isinstance(enriched_live, dict):
                enriched = enriched_live
        except Exception:
            pass
        import uw_composite_v2 as uw_v2

        comp = uw_v2.compute_composite_score_v2(sym, enriched, regime=regime)
        if not isinstance(comp, dict):
            return {}
        ui = comp.get("v2_uw_inputs")
        if isinstance(ui, dict) and ui:
            return dict(ui)
    except Exception:
        return {}
    return {}


def entry_uw_has_finite_ml_telemetry(entry_uw: Any) -> bool:
    """True if zero-tolerance / ML gates would accept entry_uw."""
    import math

    if not isinstance(entry_uw, dict) or not entry_uw:
        return False

    def _fin(v: Any) -> bool:
        if v is None:
            return False
        try:
            return math.isfinite(float(v))
        except (TypeError, ValueError):
            return False

    if not _fin(entry_uw.get("earnings_proximity")):
        return False
    if not _fin(entry_uw.get("sentiment_score")):
        return False
    return True
