"""Bid/ask touch-crossing helpers for execution and TCA."""
from __future__ import annotations

from typing import Optional, Tuple


BUY_ALIASES = {"buy", "cover", "short_cover", "buy_to_cover"}
SELL_ALIASES = {"sell", "short", "sell_short", "long_exit"}


def touch_price_for_order_side(side: str, *, bid: float, ask: float) -> float:
    """Return ask for buy-like orders and bid for sell-like orders."""
    bid_f = float(bid)
    ask_f = float(ask)
    if bid_f <= 0 or ask_f <= 0 or bid_f > ask_f:
        raise ValueError("valid bid/ask required")
    normalized = str(side or "").strip().lower()
    if normalized in BUY_ALIASES:
        return ask_f
    if normalized in SELL_ALIASES:
        return bid_f
    raise ValueError(f"unknown order side: {side!r}")


def slippage_bps_vs_touch(
    *,
    ref_bid: Optional[float],
    ref_ask: Optional[float],
    fill_price: Optional[float],
    side: Optional[str],
) -> Tuple[Optional[float], Optional[str]]:
    """Directional slippage versus the side-appropriate bid/ask touch."""
    try:
        fill = float(fill_price)
        if fill <= 0:
            return None, None
        side_norm = str(side or "").strip().lower()
        if side_norm in BUY_ALIASES:
            ref = float(ref_ask)
            label = "decision_time_ask"
            bps = (fill - ref) / ref * 10000.0
        elif side_norm in SELL_ALIASES:
            ref = float(ref_bid)
            label = "decision_time_bid"
            bps = (ref - fill) / ref * 10000.0
        else:
            return None, None
        if ref <= 0:
            return None, None
    except (TypeError, ValueError):
        return None, None
    return round(bps, 4), label
