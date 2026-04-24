import pytest

from main import AlpacaExecutor, Config
from src.execution.touch_pricing import (
    slippage_bps_vs_touch,
    touch_price_for_order_side,
)


def test_buy_orders_cross_at_ask() -> None:
    assert touch_price_for_order_side("buy", bid=99.5, ask=100.0) == pytest.approx(100.0)


def test_sell_orders_cross_at_bid() -> None:
    assert touch_price_for_order_side("sell", bid=99.5, ask=100.0) == pytest.approx(99.5)


def test_short_entry_sell_is_priced_at_bid() -> None:
    assert touch_price_for_order_side("short", bid=49.95, ask=50.05) == pytest.approx(49.95)


def test_short_cover_buy_is_priced_at_ask() -> None:
    assert touch_price_for_order_side("cover", bid=49.95, ask=50.05) == pytest.approx(50.05)


def test_slippage_vs_touch_uses_ask_for_buy() -> None:
    bps, ref = slippage_bps_vs_touch(ref_bid=99.5, ref_ask=100.0, fill_price=100.1, side="buy")
    assert bps == pytest.approx(10.0)
    assert ref == "decision_time_ask"


def test_slippage_vs_touch_uses_bid_for_sell() -> None:
    bps, ref = slippage_bps_vs_touch(ref_bid=99.5, ref_ask=100.0, fill_price=99.4, side="sell")
    assert bps == pytest.approx(10.0503)
    assert ref == "decision_time_bid"


def test_market_fallback_entry_price_uses_bid_for_short_entry(monkeypatch) -> None:
    executor = object.__new__(AlpacaExecutor)
    monkeypatch.setattr(Config, "ENTRY_MODE", "MARKET_FALLBACK")
    monkeypatch.setattr(executor, "get_nbbo", lambda _symbol: (99.5, 100.0))

    assert executor.compute_entry_price("AAPL", "sell") == pytest.approx(99.5)


def test_market_fallback_entry_price_uses_ask_for_buy_or_cover(monkeypatch) -> None:
    executor = object.__new__(AlpacaExecutor)
    monkeypatch.setattr(Config, "ENTRY_MODE", "MARKET_FALLBACK")
    monkeypatch.setattr(executor, "get_nbbo", lambda _symbol: (99.5, 100.0))

    assert executor.compute_entry_price("AAPL", "buy") == pytest.approx(100.0)
