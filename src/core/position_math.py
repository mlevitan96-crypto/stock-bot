"""Side-aware position math for long/short parity."""
from __future__ import annotations

import math
from typing import Optional


LONG_ALIASES = {"buy", "long", "bull", "bullish", "1", "+1"}
SHORT_ALIASES = {"sell", "short", "bear", "bearish", "-1"}


def get_position_sign(side: str) -> int:
    """Return +1 for long-like sides and -1 for short-like sides."""
    normalized = str(side or "").strip().lower()
    if normalized in LONG_ALIASES:
        return 1
    if normalized in SHORT_ALIASES:
        return -1
    raise ValueError(f"unknown position side: {side!r}")


def calculate_signed_pnl_pct(entry_price: float, current_price: float, side: str) -> float:
    """Return PnL percent where profitable moves are positive for both longs and shorts."""
    entry = float(entry_price)
    current = float(current_price)
    if not math.isfinite(entry) or entry <= 0:
        raise ValueError("entry_price must be positive and finite")
    if not math.isfinite(current) or current <= 0:
        raise ValueError("current_price must be positive and finite")
    return ((current - entry) / entry) * 100.0 * get_position_sign(side)


def is_stop_loss_hit(current_price: float, stop_price: float, side: str) -> bool:
    """Return whether price has crossed the stop in the adverse direction."""
    current = float(current_price)
    stop = float(stop_price)
    if not math.isfinite(current) or not math.isfinite(stop) or current <= 0 or stop <= 0:
        return False
    return current <= stop if get_position_sign(side) == 1 else current >= stop


def calculate_new_trailing_stop(
    current_price: float,
    current_stop: Optional[float],
    side: str,
    trail_amount: float,
) -> float:
    """
    Ratchet a trailing stop using side-aware favorable price movement.

    Longs trail below price and only ratchet upward. Shorts trail above price and only
    ratchet downward as price moves in favor.
    """
    price = float(current_price)
    amount = float(trail_amount)
    if not math.isfinite(price) or price <= 0:
        raise ValueError("current_price must be positive and finite")
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("trail_amount must be positive and finite")

    if get_position_sign(side) == 1:
        candidate = price - amount
        if current_stop is None or not math.isfinite(float(current_stop)) or float(current_stop) <= 0:
            return float(candidate)
        return float(max(float(current_stop), candidate))

    candidate = price + amount
    if current_stop is None or not math.isfinite(float(current_stop)) or float(current_stop) <= 0:
        return float(candidate)
    return float(min(float(current_stop), candidate))


def favorable_extreme_price(current_extreme: float, current_price: float, side: str) -> float:
    """Update the favorable price extreme: highest high for longs, lowest low for shorts."""
    extreme = float(current_extreme)
    price = float(current_price)
    if not math.isfinite(extreme) or extreme <= 0:
        return price
    if not math.isfinite(price) or price <= 0:
        return extreme
    return max(extreme, price) if get_position_sign(side) == 1 else min(extreme, price)
