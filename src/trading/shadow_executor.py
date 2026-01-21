#!/usr/bin/env python3
"""
Shadow executor (v2, shadow-only)
================================

This module is called from the existing shadow A/B compare path in `main.py`.
It never submits orders; it only emits append-only records to logs/shadow_trades.jsonl.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.trading.shadow_logger import append_shadow_trade


def log_shadow_decision(
    *,
    symbol: str,
    direction: str,
    v1_score: float,
    v2_score: float,
    v1_pass: bool,
    v2_pass: bool,
    composite_v2: Dict[str, Any],
    market_regime: str = "",
    posture: str = "",
    regime_label: str = "",
    volatility_regime: str = "",
) -> None:
    """
    Emit a "shadow_trade_candidate" record when v2 would enter (v2_pass True).
    Also emits lightweight compare records for distribution analysis.
    """
    try:
        uw_attr = {
            "uw_intel_version": composite_v2.get("uw_intel_version", ""),
            "v2_uw_inputs": composite_v2.get("v2_uw_inputs", {}),
            "v2_uw_adjustments": composite_v2.get("v2_uw_adjustments", {}),
            "v2_uw_sector_profile": composite_v2.get("v2_uw_sector_profile", {}),
            "v2_uw_regime_profile": composite_v2.get("v2_uw_regime_profile", {}),
        }
        rec: Dict[str, Any] = {
            "event_type": "shadow_trade_candidate" if bool(v2_pass) else "shadow_score_compare",
            "symbol": str(symbol).upper(),
            "direction": str(direction),
            "v1_score": float(v1_score),
            "v2_score": float(v2_score),
            "v1_pass": bool(v1_pass),
            "v2_pass": bool(v2_pass),
            "composite_version": "v2",
            "universe_scoring_version": str(composite_v2.get("universe_scoring_version", "")),
            "universe_source": str(composite_v2.get("universe_source", "")),
            "in_universe": composite_v2.get("in_universe", None),
            "market_regime": str(market_regime),
            "posture": str(posture),
            "regime_label": str(regime_label),
            "volatility_regime": str(volatility_regime),
            "uw_attribution_snapshot": uw_attr,
        }
        append_shadow_trade(rec)
    except Exception:
        return

