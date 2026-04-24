"""
Exit telemetry: canonical exit components (raw/normalized/contribution), entry→exit deltas,
exit signal snapshot, and unified EXIT_EVENT record. Observational only; never affects execution.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Canonical component names for replay and decomposition
CANONICAL_EXIT_COMPONENTS = [
    "exit_flow_deterioration",
    "exit_volatility_spike",
    "exit_regime_shift",
    "exit_sentiment_reversal",
    "exit_gamma_collapse",
    "exit_dark_pool_reversal",
    "exit_insider_shift",
    "exit_sector_rotation",
    "exit_time_decay",
    "exit_microstructure_noise",
    "exit_score_deterioration",
]

V2_KEY_TO_CANONICAL = {
    "flow_deterioration": "exit_flow_deterioration",
    "darkpool_deterioration": "exit_dark_pool_reversal",
    "sentiment_deterioration": "exit_sentiment_reversal",
    "score_deterioration": "exit_score_deterioration",
    "regime_shift": "exit_regime_shift",
    "sector_shift": "exit_sector_rotation",
    "vol_expansion": "exit_volatility_spike",
    "thesis_invalidated": "exit_sentiment_reversal",
    "earnings_risk": "exit_volatility_spike",
    "overnight_flow_risk": "exit_flow_deterioration",
    "time_decay": "exit_time_decay",
    "signal_deterioration": "exit_score_deterioration",
    "flow_reversal": "exit_flow_deterioration",
    "regime_risk": "exit_regime_shift",
    "position_risk": "exit_volatility_spike",
    "profit_protection": "exit_microstructure_noise",
    "crowding_risk": "exit_microstructure_noise",
    "price_action": "exit_microstructure_noise",
}


def _float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except (TypeError, ValueError):
        return default


def build_exit_components_granular(
    v2_exit_components: Dict[str, Any],
    v2_exit_score: float,
    attribution_components: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Build canonical exit_components with raw_value, normalized_value, contribution_to_exit_score
    for every CANONICAL_EXIT_COMPONENTS key. Fills with 0 when missing.
    """
    out: Dict[str, Dict[str, float]] = {}
    for c in CANONICAL_EXIT_COMPONENTS:
        out[c] = {"raw_value": 0.0, "normalized_value": 0.0, "contribution_to_exit_score": 0.0}

    comp = v2_exit_components or {}
    for k, v in comp.items():
        val = _float(v)
        canon = V2_KEY_TO_CANONICAL.get(k) or (k if k in CANONICAL_EXIT_COMPONENTS else None)
        if canon and canon in out:
            out[canon]["raw_value"] = val
            out[canon]["normalized_value"] = min(1.0, max(0.0, val))
            # Contribution: use weight proxy (equal share if unknown)
            out[canon]["contribution_to_exit_score"] = round(val * 0.1, 6)

    if attribution_components:
        for a in attribution_components:
            if not isinstance(a, dict):
                continue
            sid = (a.get("signal_id") or a.get("name") or "").strip().replace("exit_", "")
            contrib = _float(a.get("contribution_to_score") or a.get("contribution"))
            canon = V2_KEY_TO_CANONICAL.get(sid) or (f"exit_{sid}" if f"exit_{sid}" in out else None)
            if canon and canon in out:
                out[canon]["contribution_to_exit_score"] = round(contrib, 6)
                if out[canon]["raw_value"] == 0 and contrib > 0:
                    out[canon]["normalized_value"] = min(1.0, contrib * 2)

    return {k: {kk: round(vv, 6) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in out.items()}


def build_entry_exit_deltas(
    entry_uw: Dict[str, Any],
    exit_uw: Dict[str, Any],
    composite_at_entry: float,
    composite_at_exit: float,
    entry_regime: str,
    exit_regime: str,
    entry_sector: str = "",
    exit_sector: str = "",
) -> Dict[str, Any]:
    """Build delta_* fields for entry→exit. Uses available keys; missing => None or 0."""
    entry_uw = entry_uw or {}
    exit_uw = exit_uw or {}
    flow_entry = _float(entry_uw.get("flow_strength"))
    flow_exit = _float(exit_uw.get("flow_strength"))
    dp_entry = _float(entry_uw.get("darkpool_bias"))
    dp_exit = _float(exit_uw.get("darkpool_bias"))
    return {
        "delta_composite": round(composite_at_exit - composite_at_entry, 6),
        "delta_flow_conviction": round(flow_exit - flow_entry, 6),
        "delta_dark_pool_notional": round(dp_exit - dp_entry, 6),
        "delta_sentiment": 1 if (entry_uw.get("sentiment") != exit_uw.get("sentiment")) else 0,
        "delta_regime": 1 if (str(entry_regime or "").strip() != str(exit_regime or "").strip()) else 0,
        "delta_gamma": _float(exit_uw.get("gamma", 0)) - _float(entry_uw.get("gamma", 0)),
        "delta_vol": _float(exit_uw.get("realized_vol", 0)) - _float(entry_uw.get("realized_vol", 0)),
        "delta_iv_rank": _float(exit_uw.get("iv_rank", 0)) - _float(entry_uw.get("iv_rank", 0)),
        "delta_squeeze_score": _float(exit_uw.get("squeeze_score", 0)) - _float(entry_uw.get("squeeze_score", 0)),
        "delta_sector_strength": 1 if (str(entry_sector or "").strip() != str(exit_sector or "").strip()) else 0,
    }


def build_exit_signal_snapshot(
    symbol: str,
    exit_ts: str,
    entry_ts: str,
    composite_at_exit: float,
    composite_components_at_exit: Dict[str, Any],
    exit_uw: Dict[str, Any],
    exit_regime: str,
    exit_sector: str = "",
    entry_composite: float = 0.0,
    entry_uw: Optional[Dict[str, Any]] = None,
    entry_regime: str = "",
    entry_sector: str = "",
    deltas: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Single row for logs/exit_signal_snapshot.jsonl."""
    entry_uw = entry_uw or {}
    snap: Dict[str, Any] = {
        "symbol": str(symbol).upper(),
        "exit_ts": exit_ts,
        "entry_ts": entry_ts,
        "composite_at_exit": round(composite_at_exit, 6),
        "composite_components_at_exit": dict(composite_components_at_exit or {}),
        "regime_at_exit": str(exit_regime or ""),
        "uw_conviction_at_exit": _float(exit_uw.get("flow_strength") or exit_uw.get("conviction")),
        "sector_at_exit": str(exit_sector or ""),
        "flow_conviction": _float(exit_uw.get("flow_strength")),
        "dark_pool_totals": _float(exit_uw.get("darkpool_bias")),
        "sentiment": str(exit_uw.get("sentiment") or ""),
        "regime": str(exit_regime or ""),
        "composite_at_entry": round(entry_composite, 6),
        "regime_at_entry": str(entry_regime or ""),
        "uw_conviction_at_entry": _float(entry_uw.get("flow_strength") or entry_uw.get("conviction")),
    }
    if deltas:
        snap["deltas"] = deltas
    return snap


def build_exit_event_record(
    trade_id: str,
    symbol: str,
    entry_ts: str,
    exit_ts: str,
    entry_price: Optional[float],
    exit_price: Optional[float],
    exit_reason_code: str,
    exit_components: Dict[str, Dict[str, float]],
    entry_signal_snapshot: Dict[str, Any],
    exit_signal_snapshot: Dict[str, Any],
    deltas: Dict[str, Any],
    exit_quality_metrics: Optional[Dict[str, Any]],
    regime_at_entry: str,
    regime_at_exit: str,
    uw_conviction_entry: float = 0.0,
    uw_conviction_exit: float = 0.0,
    composite_at_entry: float = 0.0,
    composite_at_exit: float = 0.0,
    composite_components_entry: Optional[Dict[str, Any]] = None,
    composite_components_exit: Optional[Dict[str, Any]] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Unified EXIT_EVENT record for logs/exit_event.jsonl (replay canonical input)."""
    evt: Dict[str, Any] = {
        "event_type": "EXIT_EVENT",
        "trade_id": trade_id,
        "symbol": str(symbol).upper(),
        "entry_ts": entry_ts,
        "exit_ts": exit_ts,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "exit_reason_code": str(exit_reason_code or "unknown"),
        "exit_components": dict(exit_components or {}),
        "entry_signal_snapshot": dict(entry_signal_snapshot or {}),
        "exit_signal_snapshot": dict(exit_signal_snapshot or {}),
        "entry_exit_deltas": dict(deltas or {}),
        "exit_quality_metrics": dict(exit_quality_metrics or {}),
        "regime_at_entry": str(regime_at_entry or ""),
        "regime_at_exit": str(regime_at_exit or ""),
        "uw_conviction_entry": round(uw_conviction_entry, 6),
        "uw_conviction_exit": round(uw_conviction_exit, 6),
        "composite_at_entry": round(composite_at_entry, 6),
        "composite_at_exit": round(composite_at_exit, 6),
        "composite_components_entry": dict(composite_components_entry or {}),
        "composite_components_exit": dict(composite_components_exit or {}),
    }
    for k, v in extra.items():
        evt[k] = v
    return evt
