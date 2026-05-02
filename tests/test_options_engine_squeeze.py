"""RV/IV sitter helpers and RSI Wilder."""

from __future__ import annotations

import pytest

from src.options_engine import (
    compute_rsi_wilder,
    fetch_uw_iv_atm_and_rv20d,
    sitter_iv_minus_rv_bonus,
)


def test_compute_rsi_wilder_all_up_trend():
    closes = [100.0 + i for i in range(20)]
    rsi = compute_rsi_wilder(closes, period=14)
    assert rsi is not None
    assert rsi >= 99.0


def test_compute_rsi_wilder_flat():
    closes = [100.0] * 20
    rsi = compute_rsi_wilder(closes, period=14)
    assert rsi is not None
    assert 45.0 <= rsi <= 55.0


def test_fetch_uw_iv_rv_mock(monkeypatch):
    import src.options_engine as oe

    def fake_get(path, cache_policy=None, params=None):
        return (
            200,
            {"data": [{"iv_atm": 0.40, "rv_20d": 0.22}]},
            {},
        )

    monkeypatch.setattr(oe, "uw_http_get", fake_get)
    monkeypatch.setattr(oe, "_uw_mock_soft", lambda: False)
    iv, rv, why = fetch_uw_iv_atm_and_rv20d("AAPL")
    assert why == "ok"
    assert iv == pytest.approx(0.40)
    assert rv == pytest.approx(0.22)
    assert sitter_iv_minus_rv_bonus("AAPL") > 0


def test_sitter_bonus_zero_when_iv_below_rv(monkeypatch):
    import src.options_engine as oe

    def fake_get(path, cache_policy=None, params=None):
        return (200, {"data": [{"iv_atm": 0.15, "rv_20d": 0.35}]}, {})

    monkeypatch.setattr(oe, "uw_http_get", fake_get)
    monkeypatch.setattr(oe, "_uw_mock_soft", lambda: False)
    assert sitter_iv_minus_rv_bonus("MSFT") == 0.0
