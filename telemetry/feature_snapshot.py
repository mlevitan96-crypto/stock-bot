"""
Feature snapshot: canonical per-trade feature vector for learning "why" winners/losers.

Contract:
- build_feature_snapshot(enriched_signal, market_context, regime_state) -> dict
- Include symbol, ts, v2_score, vol, beta, uw_flow, dark_pool, regime, posture, etc.
- All keys present or None when missing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def build_feature_snapshot(
    enriched_signal: Dict[str, Any],
    market_context: Optional[Dict[str, Any]] = None,
    regime_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a canonical feature snapshot from enriched signal + context.

    Args:
        enriched_signal: symbol, score, uw/dp/composite data, etc.
        market_context: market_context_v2 snapshot (premarket, vol, etc.)
        regime_state: regime_posture state (regime_label, posture)

    Returns:
        Snapshot dict with standard keys; missing => None.
    """
    mc = market_context or {}
    rs = regime_state or {}
    snap: Dict[str, Any] = {
        "symbol": enriched_signal.get("symbol"),
        "ts": datetime.now(timezone.utc).isoformat(),
        "side_bias": None,
        "v2_score": enriched_signal.get("composite_score") or enriched_signal.get("score"),
        "realized_vol_5d": None,
        "realized_vol_20d": enriched_signal.get("realized_vol_20d"),
        "beta_vs_spy": enriched_signal.get("beta_vs_spy"),
        "premarket_gap": mc.get("premarket_gap"),
        "premarket_relvol": mc.get("premarket_relvol"),
        "uw_flow_strength": enriched_signal.get("uw_flow_strength") or enriched_signal.get("flow_strength"),
        "uw_flow_direction": enriched_signal.get("uw_flow_direction") or enriched_signal.get("flow_direction"),
        "dark_pool_bias": enriched_signal.get("dark_pool_bias"),
        "dark_pool_activity": enriched_signal.get("dark_pool_activity"),
        "congress_recent_flag": enriched_signal.get("congress_recent") or enriched_signal.get("has_recent_congress_buy"),
        "insider_recent_flag": enriched_signal.get("insider_recent") or enriched_signal.get("has_insider_buy"),
        "earnings_days_away": enriched_signal.get("earnings_days_away"),
        "regime_label": rs.get("regime_label") or mc.get("regime_label"),
        "regime_confidence": rs.get("regime_confidence"),
        "posture": rs.get("posture"),
        "universe_membership": enriched_signal.get("in_v2_universe"),
        "flow_reversal": enriched_signal.get("flow_reversal"),
        "signal_decay": enriched_signal.get("signal_decay"),
    }
    return snap
