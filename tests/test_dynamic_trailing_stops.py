"""Tests for Wilder ATR and ratcheted long trailing stop."""

import pytest

from src.exit.dynamic_trailing_stops import (
    calculate_atr_trailing_stop,
    long_ratcheted_trailing_stop,
    long_stop_hit,
    wilders_atr_last,
)


def _flat_closes(n: int, base: float = 100.0, step: float = 0.1):
    c = [base + i * step for i in range(n)]
    h = [x + 0.2 for x in c]
    l = [x - 0.2 for x in c]
    return h, l, c


def test_wilders_atr_last_positive() -> None:
    h, l, c = _flat_closes(20)
    v = wilders_atr_last(h, l, c, period=14)
    assert v > 0


def test_calculate_atr_trailing_stop_uses_hh() -> None:
    h, l, c = _flat_closes(20)
    hh = 110.0
    raw = calculate_atr_trailing_stop(h, l, c, period=14, multiplier=2.0, highest_high_since_entry=hh)
    atr = wilders_atr_last(h, l, c, period=14)
    assert raw == pytest.approx(hh - 2.0 * atr)


def test_ratchet_never_moves_down() -> None:
    stop1 = long_ratcheted_trailing_stop(
        entry_price=100.0,
        entry_atr=1.0,
        highest_high_since_entry=101.0,
        current_atr=1.0,
        multiplier=2.0,
        previous_stop=None,
    )
    stop2 = long_ratcheted_trailing_stop(
        entry_price=100.0,
        entry_atr=1.0,
        highest_high_since_entry=101.0,
        current_atr=5.0,
        multiplier=2.0,
        previous_stop=stop1,
    )
    assert stop2 >= stop1


def test_long_stop_hit() -> None:
    assert long_stop_hit(current_price=99.0, trailing_stop=100.0) is True
    assert long_stop_hit(current_price=100.0, trailing_stop=100.0) is True
    assert long_stop_hit(current_price=100.01, trailing_stop=100.0) is False
