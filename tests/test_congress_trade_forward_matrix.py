"""Unit tests for filing-date–anchored congress forward-return helpers."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.research.congress_trade_forward_matrix import (
    close_on_or_after,
    compute_forward_returns_from_filing,
    is_small_mid_equity,
    parse_amount_range_midpoint_usd,
    reporting_lag_days,
    trade_dedupe_key,
    TradeRow,
)


def test_parse_amount_midpoint() -> None:
    assert parse_amount_range_midpoint_usd("$15,001 - $50,000") == pytest.approx(32500.5)
    assert parse_amount_range_midpoint_usd("$1,000 - $15,000") == pytest.approx(8000.0)
    assert parse_amount_range_midpoint_usd("1000-5000") == pytest.approx(3000.0)


def test_reporting_lag() -> None:
    assert reporting_lag_days(date(2023, 2, 1), date(2023, 2, 13)) == 12


def test_close_on_or_after() -> None:
    bars = [
        (date(2023, 2, 3), 10.0),
        (date(2023, 2, 6), 11.0),
        (date(2023, 2, 7), 12.0),
    ]
    d, c = close_on_or_after(bars, date(2023, 2, 4))  # weekend -> 6th
    assert d == date(2023, 2, 6)
    assert c == 11.0


def test_forward_returns_filing_anchor() -> None:
    # Filing Friday 2023-02-03; next bar Monday 6th at 100
    bars = [
        (date(2023, 2, 6), 100.0),
        (date(2023, 3, 15), 110.0),  # on/after 2023-03-05 (filing+30)
        (date(2023, 5, 10), 120.0),  # on/after +90
        (date(2023, 8, 5), 130.0),  # on/after +180 from 2023-02-03 -> 2023-08-01
    ]
    filing = date(2023, 2, 3)
    row = compute_forward_returns_from_filing(bars, filing)
    assert row["p_filing_anchor"] == 100.0
    assert row["r_1m"] == pytest.approx(0.10)
    assert row["r_3m"] == pytest.approx(0.20)
    assert row["r_6m"] == pytest.approx(0.30)


def test_small_mid_cap_filter() -> None:
    assert is_small_mid_equity(marketcap_usd=1e9, marketcap_size=None, issue_type="Common Stock") is True
    assert is_small_mid_equity(marketcap_usd=20e9, marketcap_size=None, issue_type="Common Stock") is False
    assert is_small_mid_equity(marketcap_usd=None, marketcap_size="small", issue_type="Common Stock") is True
    assert is_small_mid_equity(marketcap_usd=None, marketcap_size="big", issue_type="Common Stock") is False
    assert is_small_mid_equity(marketcap_usd=1e9, marketcap_size=None, issue_type="ETF") is False


def test_trade_dedupe_key_stable() -> None:
    t = TradeRow(
        ticker="ABC",
        transaction_date=date(2023, 1, 1),
        filing_date=date(2023, 2, 1),
        amounts_raw="$1k - $15k",
        amount_mid_usd=8000.0,
        txn_type="Buy",
        member_name="X",
        politician_id="p1",
        raw={},
    )
    assert trade_dedupe_key(t) == trade_dedupe_key(t)
