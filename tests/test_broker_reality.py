from types import SimpleNamespace

import pytest

from risk_management import validate_order_size
from src.core.broker_math import validate_short_asset
from trade_guard import TradeGuard


def test_short_asset_requires_shortable_and_easy_to_borrow() -> None:
    ok, reason = validate_short_asset(SimpleNamespace(shortable=True, easy_to_borrow=False))
    assert ok is False
    assert reason == "asset_hard_to_borrow"


def test_short_asset_override_allows_hard_to_borrow() -> None:
    ok, reason = validate_short_asset(
        SimpleNamespace(shortable=True, easy_to_borrow=False),
        htb_override=True,
    )
    assert ok is True
    assert reason == "short_asset_ok_htb_override"


def test_short_asset_blocks_not_shortable_even_with_override() -> None:
    ok, reason = validate_short_asset(
        SimpleNamespace(shortable=False, easy_to_borrow=True),
        htb_override=True,
    )
    assert ok is False
    assert reason == "asset_not_shortable"


def test_validate_order_size_fails_closed_on_invalid_buying_power() -> None:
    ok, reason = validate_order_size("AAPL", 1, "buy", 100.0, 0.0)
    assert ok is False
    assert "invalid buying power" in str(reason).lower()


def test_validate_order_size_applies_margin_to_short_sells() -> None:
    ok, reason = validate_order_size("AAPL", 10, "sell", 100.0, 1200.0)
    assert ok is False
    assert "exceeds" in str(reason).lower()


def test_trade_guard_buying_power_applies_to_shorts() -> None:
    guard = TradeGuard(
        {
            "max_notional_per_order": 100_000.0,
            "max_position_size_usd": 100_000.0,
            "max_portfolio_exposure_pct": 1.0,
            "max_concentration_per_symbol_pct": 1.0,
        }
    )
    ok, reason = guard.evaluate_order(
        {
            "symbol": "AAPL",
            "side": "sell",
            "qty": 10,
            "intended_price": 100.0,
            "current_positions": {},
            "account_equity": 100_000.0,
            "account_buying_power": 1200.0,
        }
    )
    assert ok is False
    assert "insufficient_buying_power" in reason
