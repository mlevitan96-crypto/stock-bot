"""Upstream capital-aware max share price (wheel universe selector)."""

from __future__ import annotations

from strategies.wheel_universe_selector import _get_sector, _max_affordable_share_price, _sector_bucket_for_cap


def test_sector_bucket_unknown_symbol_isolated():
    assert _sector_bucket_for_cap("ZZZ", "Unknown") == "Unknown.ZZZ"


def test_max_affordable_sector_headroom_only_binding():
    # 100k equity, 25% sector cap => 25k USD; no open CSPs in Energy => 250 $/share sector leg
    by_sec = {}
    px = _max_affordable_share_price(
        "XOM",
        account_equity=100_000.0,
        max_sector_frac=0.25,
        by_sec=by_sec,
        strategy_available=1_000_000.0,
        per_position_limit=1_000_000.0,
        cash=1_000_000.0,
        multiplier=1.0,
        require_cash_secured=True,
        allow_margin_account=False,
    )
    assert _get_sector("XOM") == "Energy"
    assert abs(px - 250.0) < 1e-6


def test_max_affordable_wheel_available_binding():
    by_sec = {}
    px = _max_affordable_share_price(
        "XOM",
        account_equity=100_000.0,
        max_sector_frac=0.25,
        by_sec=by_sec,
        strategy_available=11_657.82,
        per_position_limit=1_000_000.0,
        cash=1_000_000.0,
        multiplier=1.0,
        require_cash_secured=True,
        allow_margin_account=False,
    )
    assert abs(px - 116.5782) < 1e-3


def test_max_affordable_sector_uses_open_csps_energy():
    # Energy bucket already at 14_600 USD notional (matches wheel telemetry shape).
    by_sec = {"Energy": 14_600.0}
    px = _max_affordable_share_price(
        "XOM",
        account_equity=100_000.0,
        max_sector_frac=0.25,
        by_sec=by_sec,
        strategy_available=1_000_000.0,
        per_position_limit=1_000_000.0,
        cash=1_000_000.0,
        multiplier=1.0,
        require_cash_secured=True,
        allow_margin_account=False,
    )
    # cap 25_000 - 14_600 = 10_400 headroom => 104 $/share
    assert abs(px - 104.0) < 1e-6


def test_max_affordable_skips_cash_when_margin_multiplier_high():
    by_sec = {}
    px = _max_affordable_share_price(
        "XOM",
        account_equity=100_000.0,
        max_sector_frac=0.25,
        by_sec=by_sec,
        strategy_available=250_000.0,
        per_position_limit=250_000.0,
        cash=1_000_000.0,
        multiplier=4.0,
        require_cash_secured=True,
        allow_margin_account=False,
    )
    assert abs(px - 250.0) < 1e-6
