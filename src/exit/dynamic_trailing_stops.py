"""
Dynamic ATR trailing stops (Wilder ATR + ratchet).

Used for long exits: stop only ratchets **up**. Initial anchor:
``entry_price - multiplier * entry_atr``. Live trail:
``highest_high_since_entry - multiplier * current_atr``, then
``max(previous_stop, combined_candidate)`` so the stop never moves down.
"""
from __future__ import annotations

import math
from typing import List, Optional, Sequence


def _finite(x: float) -> bool:
    try:
        v = float(x)
        return v == v and not math.isinf(v)
    except (TypeError, ValueError):
        return False


def _true_range(high: float, low: float, close_prev: float) -> float:
    return max(high - low, abs(high - close_prev), abs(low - close_prev))


def wilders_atr_last(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> float:
    """
    Wilder (RMA) ATR at the final bar.

    Requires at least ``period + 1`` closes (so ``period`` true ranges exist for the seed).
    """
    p = int(period)
    n = len(closes)
    if p < 1 or n < p + 1:
        raise ValueError("need at least period+1 bars for Wilder ATR")
    trs: List[float] = []
    for i in range(1, n):
        if not (_finite(highs[i]) and _finite(lows[i]) and _finite(closes[i - 1])):
            raise ValueError("non-finite OHLC in ATR window")
        trs.append(_true_range(float(highs[i]), float(lows[i]), float(closes[i - 1])))
    if len(trs) < p:
        raise ValueError("insufficient true ranges")
    atr = sum(trs[:p]) / float(p)
    for j in range(p, len(trs)):
        atr = (atr * float(p - 1) + trs[j]) / float(p)
    return float(atr)


def calculate_atr_trailing_stop(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
    multiplier: float = 2.0,
    *,
    highest_high_since_entry: Optional[float] = None,
) -> float:
    """
    Chandelier-style **raw** trailing level for a long at the last bar:
    ``HH - multiplier * ATR_now``.

    If ``highest_high_since_entry`` is omitted, uses ``max(highs)`` over the supplied window
    (caller should pass bars covering the hold when possible).
    """
    atr = wilders_atr_last(highs, lows, closes, period=period)
    hh = float(highest_high_since_entry) if highest_high_since_entry is not None else float(max(highs))
    m = float(multiplier)
    return float(hh - m * atr)


def long_ratcheted_trailing_stop(
    *,
    entry_price: float,
    entry_atr: float,
    highest_high_since_entry: float,
    current_atr: float,
    multiplier: float,
    previous_stop: Optional[float],
) -> float:
    """
    Ratcheted long stop: never moves down. Combines initial anchor with chandelier trail.

    ``initial = entry_price - multiplier * entry_atr``
    ``chandelier = highest_high_since_entry - multiplier * current_atr``
    ``candidate = max(initial, chandelier)``
    ``return max(previous_stop, candidate)`` when ``previous_stop`` is set.
    """
    ep = float(entry_price)
    ea = float(entry_atr)
    hh = float(highest_high_since_entry)
    atr = float(current_atr)
    m = float(multiplier)
    initial = ep - m * ea
    chandelier = hh - m * atr
    candidate = max(initial, chandelier)
    if previous_stop is None or not _finite(float(previous_stop)):
        return float(candidate)
    return float(max(float(previous_stop), candidate))


def long_stop_hit(*, current_price: float, trailing_stop: float) -> bool:
    """True when price is at or below the trailing stop (long)."""
    return float(current_price) <= float(trailing_stop)


def short_ratcheted_trailing_stop(
    *,
    entry_price: float,
    entry_atr: float,
    lowest_low_since_entry: float,
    current_atr: float,
    multiplier: float,
    previous_stop: Optional[float],
) -> float:
    """
    Ratcheted short stop: never moves up. Combines initial anchor with chandelier trail.

    ``initial = entry_price + multiplier * entry_atr``
    ``chandelier = lowest_low_since_entry + multiplier * current_atr``
    ``candidate = min(initial, chandelier)``
    ``return min(previous_stop, candidate)`` when ``previous_stop`` is set.
    """
    ep = float(entry_price)
    ea = float(entry_atr)
    ll = float(lowest_low_since_entry)
    atr = float(current_atr)
    m = float(multiplier)
    initial = ep + m * ea
    chandelier = ll + m * atr
    candidate = min(initial, chandelier)
    if previous_stop is None or not _finite(float(previous_stop)):
        return float(candidate)
    return float(min(float(previous_stop), candidate))


def short_stop_hit(*, current_price: float, trailing_stop: float) -> bool:
    """True when price is at or above the trailing stop (short)."""
    return float(current_price) >= float(trailing_stop)
