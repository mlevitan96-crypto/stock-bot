#!/usr/bin/env python3
"""
Directional Intelligence Sources (TELEMETRY ONLY)
=================================================

Normalized fetchers for pre-market, post-market, overnight, futures, volatility,
breadth, sector, ETF flow, macro, and UW extensions. All values numeric or categorical.
Used only for CAPTURE, STORAGE, and REPLAY — no live behavior changes.

Contract:
- Never raise; return defaults on failure.
- All fetchers return dicts with normalized keys and numeric/categorical values.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except Exception:
        return default


def _direction_from_ret(ret: float) -> str:
    if ret > 0.0025:
        return "up"
    if ret < -0.0025:
        return "down"
    return "flat"


def _normalized_direction_score(direction: str) -> float:
    """Map direction to contribution score: up=1, flat=0, down=-1."""
    d = (direction or "").strip().lower()
    if d == "up":
        return 1.0
    if d == "down":
        return -1.0
    return 0.0


# ---------------------------------------------------------------------------
# 1. PRE-MARKET (proxies from market context + stubs)
# ---------------------------------------------------------------------------


def fetch_premarket_intel(api: Any = None, market_context: Optional[Dict] = None) -> Dict[str, Any]:
    """Premarket: gap, volume ratio, volatility, sentiment, flow (UW if available)."""
    out: Dict[str, Any] = {
        "premarket_gap_pct": 0.0,
        "premarket_volume_ratio": 1.0,
        "premarket_volatility": 0.0,
        "premarket_sentiment": "neutral",
        "premarket_flow": 0.0,
    }
    try:
        if market_context:
            spy_ret = _safe_float(market_context.get("spy_overnight_ret"))
            qqq_ret = _safe_float(market_context.get("qqq_overnight_ret"))
            out["premarket_gap_pct"] = 100.0 * 0.5 * (spy_ret + qqq_ret)
            out["premarket_sentiment"] = "bullish" if (spy_ret + qqq_ret) > 0.005 else (
                "bearish" if (spy_ret + qqq_ret) < -0.005 else "neutral"
            )
        # Stub: volume ratio and volatility (would need premarket bars)
        out["premarket_volume_ratio"] = 1.0
        out["premarket_volatility"] = 0.0
        out["premarket_flow"] = 0.0
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# 2. POST-MARKET
# ---------------------------------------------------------------------------


def fetch_postmarket_intel(api: Any = None) -> Dict[str, Any]:
    """Post-market: gap, AH volume ratio, earnings flag, sentiment."""
    return {
        "postmarket_gap_pct": 0.0,
        "after_hours_volume_ratio": 1.0,
        "earnings_reaction_flag": False,
        "postmarket_sentiment": "neutral",
    }


# ---------------------------------------------------------------------------
# 3. OVERNIGHT (from market context proxies)
# ---------------------------------------------------------------------------


def fetch_overnight_intel(market_context: Optional[Dict] = None) -> Dict[str, Any]:
    """Overnight return, volatility, flow, dark pool imbalance."""
    out: Dict[str, Any] = {
        "overnight_return": 0.0,
        "overnight_volatility": 0.0,
        "overnight_flow": 0.0,
        "overnight_dark_pool_imbalance": 0.0,
    }
    try:
        if market_context:
            spy_ret = _safe_float(market_context.get("spy_overnight_ret"))
            qqq_ret = _safe_float(market_context.get("qqq_overnight_ret"))
            out["overnight_return"] = 0.5 * (spy_ret + qqq_ret)
        # Stubs for vol/flow/dp (would need overnight bars / UW)
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# 4. FUTURES (proxies: SPY/QQQ/IWM as ES/NQ/RTY; VXX as VX)
# ---------------------------------------------------------------------------


def fetch_futures_intel(market_context: Optional[Dict] = None) -> Dict[str, Any]:
    """ES/NQ/RTY/VX direction, basis, trend strength (proxies)."""
    out: Dict[str, Any] = {
        "ES_direction": "flat",
        "NQ_direction": "flat",
        "RTY_direction": "flat",
        "VX_direction": "flat",
        "futures_basis": 0.0,
        "futures_trend_strength": 0.0,
    }
    try:
        if market_context:
            spy_ret = _safe_float(market_context.get("spy_overnight_ret"))
            qqq_ret = _safe_float(market_context.get("qqq_overnight_ret"))
            out["ES_direction"] = _direction_from_ret(spy_ret)
            out["NQ_direction"] = _direction_from_ret(qqq_ret)
            out["RTY_direction"] = "flat"  # stub
            out["VX_direction"] = "flat"  # stub; would use VXX change
            out["futures_trend_strength"] = 0.5 * (spy_ret + qqq_ret)
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# 5. VOLATILITY (from market context + symbol_risk if available)
# ---------------------------------------------------------------------------


def fetch_volatility_intel(
    market_context: Optional[Dict] = None,
    symbol_risk: Optional[Dict] = None,
) -> Dict[str, Any]:
    """VIX level/change, VVIX, realized vol 1d/5d/20d, vol_regime."""
    out: Dict[str, Any] = {
        "VIX_level": 20.0,
        "VIX_change": 0.0,
        "VVIX_level": 0.0,
        "realized_vol_1d": 0.0,
        "realized_vol_5d": 0.0,
        "realized_vol_20d": 0.2,
        "vol_regime": "mid",
    }
    try:
        if market_context:
            out["vol_regime"] = str(market_context.get("volatility_regime") or "mid").lower()
            vxx = _safe_float(market_context.get("vxx_close_1d"), 20.0)
            out["VIX_level"] = max(10.0, min(80.0, vxx * 1.2))  # rough VXX->VIX proxy
        if symbol_risk and isinstance(symbol_risk, dict):
            out["realized_vol_20d"] = _safe_float(symbol_risk.get("realized_vol_20d"), 0.2)
            out["realized_vol_5d"] = _safe_float(symbol_risk.get("realized_vol_5d"), 0.0)
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# 6. BREADTH (stubs; would need adv/dec, up/down volume API)
# ---------------------------------------------------------------------------


def fetch_breadth_intel(api: Any = None) -> Dict[str, Any]:
    """Adv/dec ratio, up_vol/down_vol, new highs/lows, index/sector breadth."""
    return {
        "adv_dec_ratio": 1.0,
        "up_vol_down_vol_ratio": 1.0,
        "new_highs_lows": 0.0,
        "index_breadth": {},
        "sector_breadth": {},
    }


# ---------------------------------------------------------------------------
# 7. SECTOR ROTATION (from sector_intel + stubs)
# ---------------------------------------------------------------------------


def fetch_sector_intel(symbol: Optional[str] = None) -> Dict[str, Any]:
    """Sector strength rank, momentum, volatility, ETF flow."""
    out: Dict[str, Any] = {
        "sector_strength_rank": 0,
        "sector_momentum": 0.0,
        "sector_volatility": 0.0,
        "sector_ETF_flow": 0.0,
        "sector": "UNKNOWN",
    }
    try:
        from src.intel.sector_intel import get_sector
        out["sector"] = get_sector(symbol or "")
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# 8. ETF FLOWS (stubs)
# ---------------------------------------------------------------------------


def fetch_etf_flow_intel() -> Dict[str, Any]:
    """SPY/QQQ/IWM and sector ETF flows."""
    return {
        "SPY_flow": 0.0,
        "QQQ_flow": 0.0,
        "IWM_flow": 0.0,
        "sector_ETF_flows": {},
    }


# ---------------------------------------------------------------------------
# 9. MACRO (from macro_gate if available)
# ---------------------------------------------------------------------------


def fetch_macro_intel() -> Dict[str, Any]:
    """Macro events today, risk flag, sentiment score."""
    out: Dict[str, Any] = {
        "macro_events_today": [],
        "macro_risk_flag": False,
        "macro_sentiment_score": 0.0,
    }
    try:
        from structural_intelligence.macro_gate import MacroGate
        mg = MacroGate()
        trend = (getattr(mg, "yield_trend", None) or "NEUTRAL").upper()
        if trend == "RISING":
            out["macro_sentiment_score"] = -0.3
        elif trend == "FALLING":
            out["macro_sentiment_score"] = 0.2
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# 10. UW EXTENSIONS (read from state/cache if present)
# ---------------------------------------------------------------------------


def fetch_uw_intel(symbol: Optional[str] = None) -> Dict[str, Any]:
    """UW pre-market/overnight sentiment and flow (if endpoints exist)."""
    return {
        "uw_premarket_sentiment": "neutral",
        "uw_overnight_sentiment": "neutral",
        "uw_preopen_flow": 0.0,
        "uw_preopen_dark_pool": 0.0,
    }


# ---------------------------------------------------------------------------
# AGGREGATE: build full intelligence snapshot
# ---------------------------------------------------------------------------


def build_full_intel_snapshot(
    api: Any = None,
    symbol: Optional[str] = None,
    market_context: Optional[Dict] = None,
    regime_posture: Optional[Dict] = None,
    symbol_risk: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Build one full snapshot for entry or exit (telemetry only). Never returns empty dict."""
    ts = datetime.now(timezone.utc).isoformat()
    minimal = {"timestamp": ts, "premarket_intel": {}, "postmarket_intel": {}, "overnight_intel": {}, "futures_intel": {}, "volatility_intel": {}, "breadth_intel": {}, "sector_intel": {}, "etf_flow_intel": {}, "macro_intel": {}, "uw_intel": {}, "regime_posture": dict(regime_posture or {})}
    try:
        premarket = fetch_premarket_intel(api, market_context)
        postmarket = fetch_postmarket_intel(api)
        overnight = fetch_overnight_intel(market_context)
        futures = fetch_futures_intel(market_context)
        volatility = fetch_volatility_intel(market_context, symbol_risk)
        breadth = fetch_breadth_intel(api)
        sector = fetch_sector_intel(symbol)
        etf_flow = fetch_etf_flow_intel()
        macro = fetch_macro_intel()
        uw = fetch_uw_intel(symbol)
        return {
            "timestamp": ts,
            "premarket_intel": premarket,
            "postmarket_intel": postmarket,
            "overnight_intel": overnight,
            "futures_intel": futures,
            "volatility_intel": volatility,
            "breadth_intel": breadth,
            "sector_intel": sector,
            "etf_flow_intel": etf_flow,
            "macro_intel": macro,
            "uw_intel": uw,
            "regime_posture": dict(regime_posture or {}),
        }
    except Exception:
        return minimal
