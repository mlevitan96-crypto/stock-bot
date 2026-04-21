import pytest

from src.telemetry.equity_price_precision import (
    quantize_telemetry_price,
    quantize_telemetry_pnl_pct,
    quantize_telemetry_pnl_usd,
)


def test_sub_five_price_four_decimals():
    assert quantize_telemetry_price(1.23456) == pytest.approx(1.2346)


def test_five_plus_price_six_decimals():
    assert quantize_telemetry_price(50.123456789) == pytest.approx(50.123457)


def test_pnl_pct_tier_follows_entry():
    assert quantize_telemetry_pnl_pct(0.01234, ref_price=2.0) == pytest.approx(0.0123)
    assert quantize_telemetry_pnl_pct(0.0123456, ref_price=100.0) == pytest.approx(0.012346)


def test_pnl_usd_tier():
    assert quantize_telemetry_pnl_usd(12.3456, ref_price=3.0) == pytest.approx(12.3456)
    assert quantize_telemetry_pnl_usd(12.3456, ref_price=50.0) == pytest.approx(12.35)
