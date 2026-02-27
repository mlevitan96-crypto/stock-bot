"""
UW Micro-Signals — Decompose Unusual Whales into constituent signals.
========================================

Phase 2: UW must NEVER emit a single composite score. Every UW component is logged
as an independent signal using Phase 1 schema (signal_id, raw_value, normalized_value,
weight, contribution_to_score, quality_flags). UW micro-signals are treated
identically to internal signals.

Quality flags: stale, missing, conflicting, low_liquidity, defaulted (never silent).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Optional: use canonical schema component builder
try:
    from schema.attribution_v1 import score_component_dict
except ImportError:

    def score_component_dict(
        name: str,
        source: str,
        contribution_to_score: float,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "signal_id": name,
            "name": name,
            "source": source,
            "contribution_to_score": contribution_to_score,
        }
        for k, v in kwargs.items():
            if v is not None and k not in ("signal_id",):
                out[k] = v
        return out


def _component(signal_id: str, source: str, contribution: float, **kwargs: Any) -> Dict[str, Any]:
    """Phase 1 component with signal_id and name (same as signal_id)."""
    d = score_component_dict(signal_id, source, contribution, **kwargs)
    d["signal_id"] = signal_id
    d.setdefault("name", signal_id)
    return d


def _num(x: Any, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except (TypeError, ValueError):
        return default


def _str(x: Any, default: str = "") -> str:
    return str(x).strip() if x is not None else default


# ----- Flow trade micro-signals (from normalized flow trade dict) -----

def extract_flow_micro_signals(
    flow_trades: List[Dict[str, Any]],
    *,
    weights: Optional[Dict[str, float]] = None,
    timestamp_utc: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    From a list of normalized flow trades (e.g. from UW client _normalize_flow_trade),
    extract micro-signals: flow_type, premium, sweep vs split, bid/ask, aggressor,
    volume, OI, sentiment, magnitude, signal_type.
    Returns list of component dicts (schema v1 compatible).
    """
    weights = weights or {}
    out: List[Dict[str, Any]] = []
    if not flow_trades:
        out.append(_component(
            "uw.flow.aggregate",
            "uw",
            0.0,
            missing_reason="no_flow_trades",
            quality_flags=["missing"],
            timestamp_utc=timestamp_utc,
        ))
        return out

    # Aggregate metrics across trades
    total_premium = 0.0
    sweep_count = 0
    block_count = 0
    buy_premium = 0.0
    sell_premium = 0.0
    total_volume = 0
    total_oi = 0
    convictions: List[float] = []
    magnitudes: List[str] = []

    for t in flow_trades:
        if not isinstance(t, dict):
            continue
        total_premium += _num(t.get("premium_usd") or t.get("total_premium"))
        ft = _str(t.get("flow_type"), "").lower()
        if ft == "sweep":
            sweep_count += 1
        elif ft in ("block", "floor"):
            block_count += 1
        is_buy = (t.get("direction") or "").lower() in ("bullish", "buy")
        prem = _num(t.get("premium_usd") or t.get("total_premium"))
        if is_buy:
            buy_premium += prem
        else:
            sell_premium += prem
        total_volume += int(_num(t.get("volume"), 0))
        total_oi += int(_num(t.get("open_interest") or t.get("oi"), 0))
        convictions.append(_num(t.get("flow_conv") or t.get("conviction")))
        mag = _str(t.get("flow_magnitude") or t.get("magnitude"))
        if mag:
            magnitudes.append(mag.upper())

    # Normalized features (0–1 or bounded)
    n_trades = len(flow_trades)
    prem_norm = min(1.0, math.log10(total_premium + 1) / 7.5) if total_premium > 0 else 0.0  # log scale
    sweep_ratio = sweep_count / n_trades if n_trades else 0.0
    aggressor_imbalance = (buy_premium - sell_premium) / (total_premium + 1e-9)
    agg_norm = (aggressor_imbalance + 1) / 2.0  # 0..1
    avg_conv = sum(convictions) / len(convictions) if convictions else 0.5
    vol_norm = min(1.0, total_volume / 1000) if total_volume else 0.0
    oi_norm = min(1.0, total_oi / 5000) if total_oi else 0.0
    high_magnitude_ratio = sum(1 for m in magnitudes if m in ("HIGH", "MEDIUM")) / (len(magnitudes) or 1)

    w_prem = weights.get("uw_flow_premium", 0.4)
    w_sweep = weights.get("uw_flow_sweep_ratio", 0.2)
    w_agg = weights.get("uw_flow_aggressor", 0.25)
    w_conv = weights.get("uw_flow_conviction", 0.5)
    w_vol = weights.get("uw_flow_volume", 0.1)
    w_oi = weights.get("uw_flow_oi", 0.1)
    w_mag = weights.get("uw_flow_magnitude", 0.2)

    _ts = timestamp_utc or datetime.now(timezone.utc).isoformat()
    _flags: List[str] = [] if flow_trades else ["missing"]
    out.append(_component(
        "uw.flow.premium",
        "uw",
        w_prem * prem_norm,
        raw_value=total_premium,
        normalized_value=prem_norm,
        weight=w_prem,
        quality_flags=_flags,
        timestamp_utc=_ts,
    ))
    out.append(_component(
        "uw.flow.sweep_ratio",
        "uw",
        w_sweep * sweep_ratio,
        raw_value=sweep_count / (n_trades or 1),
        normalized_value=sweep_ratio,
        weight=w_sweep,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    out.append(_component(
        "uw.flow.aggressor",
        "uw",
        w_agg * (agg_norm - 0.5),
        raw_value=aggressor_imbalance,
        normalized_value=agg_norm,
        weight=w_agg,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    out.append(_component(
        "uw.flow.conviction",
        "uw",
        w_conv * avg_conv,
        raw_value=avg_conv,
        normalized_value=avg_conv,
        weight=w_conv,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    out.append(_component(
        "uw.flow.volume",
        "uw",
        w_vol * vol_norm,
        raw_value=total_volume,
        normalized_value=vol_norm,
        weight=w_vol,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    out.append(_component(
        "uw.flow.oi",
        "uw",
        w_oi * oi_norm,
        raw_value=total_oi,
        normalized_value=oi_norm,
        weight=w_oi,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    out.append(_component(
        "uw.flow.magnitude",
        "uw",
        w_mag * high_magnitude_ratio,
        raw_value=",".join(magnitudes) if magnitudes else None,
        normalized_value=high_magnitude_ratio,
        weight=w_mag,
        quality_flags=[],
        timestamp_utc=_ts,
    ))

    return out


def extract_dark_pool_micro_signals(
    dark_pool: Dict[str, Any],
    *,
    weights: Optional[Dict[str, float]] = None,
    timestamp_utc: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Extract dark pool micro-signals: notional, lit vs off-lit ratio, side."""
    weights = weights or {}
    out: List[Dict[str, Any]] = []
    if not dark_pool or not isinstance(dark_pool, dict):
        out.append(_component(
            "uw.dark_pool.aggregate",
            "uw",
            0.0,
            missing_reason="no_dark_pool_data",
            quality_flags=["missing"],
            timestamp_utc=timestamp_utc or datetime.now(timezone.utc).isoformat(),
        ))
        return out

    total = _num(dark_pool.get("total_volume") or dark_pool.get("total_notional") or dark_pool.get("total_premium"))
    lit = _num(dark_pool.get("lit_volume"), 0)
    off_lit = _num(dark_pool.get("off_lit_volume"), 0)
    notional_1h = _num(dark_pool.get("total_notional_1h") or dark_pool.get("notional_1h"))
    notional_norm = min(1.0, math.log10(notional_1h + 1) / 7.5) if notional_1h > 0 else min(1.0, math.log10(total + 1) / 7.5)
    lit_ratio = lit / (lit + off_lit + 1e-9)
    side = _str(dark_pool.get("side")).lower()
    side_norm = 0.5
    if side in ("buy", "bullish"):
        side_norm = 0.7
    elif side in ("sell", "bearish"):
        side_norm = 0.3

    w_not = weights.get("uw_dp_notional", 0.5)
    w_lit = weights.get("uw_dp_lit_ratio", 0.2)
    w_side = weights.get("uw_dp_side", 0.3)

    _ts = timestamp_utc or datetime.now(timezone.utc).isoformat()
    out.append(_component(
        "uw.dark_pool.notional",
        "uw",
        w_not * notional_norm,
        raw_value=notional_1h or total,
        normalized_value=notional_norm,
        weight=w_not,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    out.append(_component(
        "uw.dark_pool.lit_ratio",
        "uw",
        w_lit * lit_ratio,
        raw_value=lit_ratio,
        normalized_value=lit_ratio,
        weight=w_lit,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    out.append(_component(
        "uw.dark_pool.side",
        "uw",
        w_side * (side_norm - 0.5),
        raw_value=side,
        normalized_value=side_norm,
        weight=w_side,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    return out


def extract_insider_micro_signals(
    insider: Dict[str, Any],
    *,
    weights: Optional[Dict[str, float]] = None,
    timestamp_utc: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Extract insider micro-signals: net_buys, net_sells, total_usd, sentiment, conviction_modifier."""
    weights = weights or {}
    out: List[Dict[str, Any]] = []
    if not insider or not isinstance(insider, dict):
        out.append(_component(
            "uw.insider.aggregate",
            "uw",
            0.0,
            missing_reason="no_insider_data",
            quality_flags=["missing"],
            timestamp_utc=timestamp_utc or datetime.now(timezone.utc).isoformat(),
        ))
        return out

    net_buys = int(_num(insider.get("net_buys"), 0))
    net_sells = int(_num(insider.get("net_sells"), 0))
    total_usd = _num(insider.get("total_usd"))
    sent = _str(insider.get("sentiment"), "NEUTRAL").upper()
    mod = _num(insider.get("conviction_modifier"), 0.0)

    net_activity = net_buys - net_sells
    activity_norm = (net_activity + 20) / 40.0  # rough -20..+20 -> 0..1
    activity_norm = max(0.0, min(1.0, activity_norm))
    usd_norm = min(1.0, math.log10(total_usd + 1) / 8.0) if total_usd > 0 else 0.0
    sent_norm = 0.5
    if sent == "BULLISH":
        sent_norm = 0.5 + mod
    elif sent == "BEARISH":
        sent_norm = 0.5 - abs(mod)
    sent_norm = max(0.0, min(1.0, sent_norm))

    w_act = weights.get("uw_insider_activity", 0.4)
    w_usd = weights.get("uw_insider_usd", 0.3)
    w_sent = weights.get("uw_insider_sentiment", 0.3)

    _ts = timestamp_utc or datetime.now(timezone.utc).isoformat()
    out.append(_component(
        "uw.insider.activity",
        "uw",
        w_act * (activity_norm - 0.5),
        raw_value=net_activity,
        normalized_value=activity_norm,
        weight=w_act,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    out.append(_component(
        "uw.insider.usd",
        "uw",
        w_usd * usd_norm,
        raw_value=total_usd,
        normalized_value=usd_norm,
        weight=w_usd,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    out.append(_component(
        "uw.insider.sentiment",
        "uw",
        w_sent * (sent_norm - 0.5),
        raw_value=sent,
        normalized_value=sent_norm,
        weight=w_sent,
        quality_flags=[],
        timestamp_utc=_ts,
    ))
    return out


def extract_uw_micro_signals(
    enriched_data: Dict[str, Any],
    *,
    weights: Optional[Dict[str, float]] = None,
    timestamp_utc: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], float]:
    """
    Full UW decomposition from enriched_data (flow, dark_pool, insider, flow_trades).
    Returns (list of all micro-signal components, total_uw_contribution).
    """
    flow_trades = enriched_data.get("flow_trades") or []
    dark_pool = enriched_data.get("dark_pool") or {}
    insider = enriched_data.get("insider") or {}

    components: List[Dict[str, Any]] = []
    components.extend(extract_flow_micro_signals(flow_trades, weights=weights, timestamp_utc=timestamp_utc))
    components.extend(extract_dark_pool_micro_signals(dark_pool, weights=weights, timestamp_utc=timestamp_utc))
    components.extend(extract_insider_micro_signals(insider, weights=weights, timestamp_utc=timestamp_utc))

    total = sum(float(c.get("contribution_to_score") or 0.0) for c in components)
    for c in components:
        if "quality_flags" not in c or c.get("quality_flags") is None:
            c["quality_flags"] = []
    return components, total


def scale_uw_components_to_target(
    uw_components: List[Dict[str, Any]],
    target_total: float,
) -> List[Dict[str, Any]]:
    """
    Scale UW component contributions so they sum to target_total.
    Preserves ratios; used when composite pipeline computes flow+dp+insider
    as a single total and we must emit UW micro-signals that sum to that total.
    """
    if not uw_components:
        return []
    current = sum(float(c.get("contribution_to_score") or 0.0) for c in uw_components)
    if abs(current) < 1e-12:
        # All zero: set all to 0 or scale proportionally to target (e.g. 0)
        return [dict(c, contribution_to_score=0.0) for c in uw_components]
    scale = target_total / current
    out = []
    for c in uw_components:
        copy = dict(c)
        copy["contribution_to_score"] = round(float(copy.get("contribution_to_score") or 0.0) * scale, 6)
        out.append(copy)
    return out
