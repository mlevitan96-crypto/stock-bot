"""
Shared feature snapshot builder for entry / exit / blocked paths (additive fields only).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from telemetry.feature_snapshot import build_feature_snapshot
from telemetry.attribution_emit_keys import uw_cache_probe


def _coerce_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def apply_uw_decomposition_fields(
    snap: Dict[str, Any],
    enriched_signal: Dict[str, Any],
    *,
    comps_fallback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Add basic-tier-friendly UW component fields + provenance. Composite score stays derived (v2_score).
    """
    out = dict(snap)
    src = enriched_signal if isinstance(enriched_signal, dict) else {}
    fb = comps_fallback if isinstance(comps_fallback, dict) else {}

    def g(*keys: str) -> Any:
        for k in keys:
            if k in src and src[k] is not None:
                return src[k]
            if k in fb and fb[k] is not None:
                return fb[k]
        return None

    out["uw_flow_conviction_proxy"] = _coerce_float(g("flow_conviction", "uw_flow_conviction"))
    out["uw_dark_pool_notional_proxy"] = _coerce_float(
        g("dark_pool_notional", "dp_notional", "dark_pool_total_premium")
    )
    out["uw_dark_pool_print_count_proxy"] = g("dark_pool_print_count", "dp_print_count")
    out["uw_options_skew_proxy"] = _coerce_float(g("iv_skew", "options_skew"))
    out["uw_unusual_activity_proxy"] = g("unusual_print_count", "cluster_count", "flow_cluster_count")
    out["uw_composite_score_derived"] = out.get("v2_score")
    out["uw_score_is_derived_only"] = False

    probe = uw_cache_probe()
    out["uw_asof_ts"] = out.get("ts")
    out["uw_ingest_ts"] = probe.get("uw_ingest_ts")
    out["uw_staleness_seconds"] = probe.get("uw_staleness_seconds")
    out["uw_missing_reason"] = probe.get("uw_missing_reason")
    # Component presence => not composite-only
    has_component = any(
        out.get(k) is not None
        for k in (
            "uw_flow_strength",
            "uw_flow_direction",
            "uw_flow_conviction_proxy",
            "dark_pool_bias",
            "dark_pool_activity",
            "uw_dark_pool_notional_proxy",
        )
    )
    if not has_component and out.get("v2_score") is not None:
        out["uw_missing_reason"] = out.get("uw_missing_reason") or "uw_components_sparse"
    return out


def build_shared_feature_snapshot(
    enriched_signal: Dict[str, Any],
    market_context: Optional[Dict[str, Any]],
    regime_state: Optional[Dict[str, Any]],
    *,
    snapshot_stage: str,
    comps_fallback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Single builder for entry / exit / blocked telemetry snapshots.
    snapshot_stage: 'entry' | 'exit' | 'blocked' (additive metadata only).
    """
    snap = build_feature_snapshot(enriched_signal, market_context, regime_state)
    snap = apply_uw_decomposition_fields(snap, enriched_signal, comps_fallback=comps_fallback)
    snap["attribution_snapshot_stage"] = snapshot_stage
    snap["schema_version"] = "attribution_feature_snapshot_v1"
    return snap


def build_exit_snapshot_from_metadata(
    symbol: str,
    info: Dict[str, Any],
    metadata: Optional[Dict[str, Any]],
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Exit path: reuse persisted entry market/regime for parity with entry snapshots.
    Returns (snapshot, thesis_tags placeholder — caller runs derive_thesis_tags).
    """
    from telemetry.thesis_tags import derive_thesis_tags

    meta = metadata if isinstance(metadata, dict) else {}
    enriched: Dict[str, Any] = {"symbol": symbol, "score": info.get("entry_score")}
    if isinstance(meta.get("v2_exit"), dict):
        v2e = meta["v2_exit"]
        now_v2 = v2e.get("now_v2") or {}
        v2_in = (now_v2.get("v2_inputs") or {}) if isinstance(now_v2.get("v2_inputs"), dict) else {}
        enriched["realized_vol_20d"] = v2_in.get("realized_vol_20d")
    comps = meta.get("components") if isinstance(meta.get("components"), dict) else {}
    mc = meta.get("entry_market_context") if isinstance(meta.get("entry_market_context"), dict) else {}
    rs = meta.get("entry_regime_posture") if isinstance(meta.get("entry_regime_posture"), dict) else {}
    snap = build_shared_feature_snapshot(
        enriched,
        mc,
        rs,
        snapshot_stage="exit",
        comps_fallback=comps,
    )
    tags = derive_thesis_tags(snap)
    return snap, tags
