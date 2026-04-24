import pytest

from src.core.position_math import (
    calculate_new_trailing_stop,
    calculate_signed_pnl_pct,
    get_position_sign,
    is_stop_loss_hit,
)


def test_get_position_sign_normalizes_long_aliases() -> None:
    assert get_position_sign("buy") == 1
    assert get_position_sign("long") == 1
    assert get_position_sign("bullish") == 1


def test_get_position_sign_normalizes_short_aliases() -> None:
    assert get_position_sign("sell") == -1
    assert get_position_sign("short") == -1
    assert get_position_sign("bearish") == -1


def test_get_position_sign_rejects_unknown_side() -> None:
    with pytest.raises(ValueError):
        get_position_sign("flat")


def test_calculate_signed_pnl_pct_mirrors_long_and_short_profit() -> None:
    assert calculate_signed_pnl_pct(100.0, 110.0, "long") == pytest.approx(10.0)
    assert calculate_signed_pnl_pct(100.0, 90.0, "short") == pytest.approx(10.0)


def test_calculate_signed_pnl_pct_mirrors_long_and_short_loss() -> None:
    assert calculate_signed_pnl_pct(100.0, 90.0, "long") == pytest.approx(-10.0)
    assert calculate_signed_pnl_pct(100.0, 110.0, "short") == pytest.approx(-10.0)


def test_calculate_signed_pnl_pct_rejects_invalid_entry() -> None:
    with pytest.raises(ValueError):
        calculate_signed_pnl_pct(0.0, 100.0, "long")


def test_is_stop_loss_hit_mirrors_long_and_short() -> None:
    assert is_stop_loss_hit(90.0, 95.0, "long") is True
    assert is_stop_loss_hit(96.0, 95.0, "long") is False
    assert is_stop_loss_hit(110.0, 105.0, "short") is True
    assert is_stop_loss_hit(104.0, 105.0, "short") is False


def test_long_trailing_stop_ratchets_up_only() -> None:
    assert calculate_new_trailing_stop(110.0, 95.0, "long", 5.0) == pytest.approx(105.0)
    assert calculate_new_trailing_stop(100.0, 105.0, "long", 5.0) == pytest.approx(105.0)


def test_short_trailing_stop_ratchets_down_only() -> None:
    assert calculate_new_trailing_stop(90.0, 105.0, "short", 5.0) == pytest.approx(95.0)
    assert calculate_new_trailing_stop(100.0, 95.0, "short", 5.0) == pytest.approx(95.0)


def test_trailing_stop_initializes_from_current_price() -> None:
    assert calculate_new_trailing_stop(100.0, None, "long", 5.0) == pytest.approx(95.0)
    assert calculate_new_trailing_stop(100.0, None, "short", 5.0) == pytest.approx(105.0)
