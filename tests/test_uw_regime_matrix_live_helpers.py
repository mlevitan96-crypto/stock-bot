"""Helpers for UW regime matrix live parsing (no network)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.market_intelligence import uw_regime_matrix as urm


@pytest.fixture(autouse=True)
def _reset_matrix_singleton():
    urm.reset_uw_regime_matrix_for_tests()
    yield
    urm.reset_uw_regime_matrix_for_tests()


def test_net_gamma_sign_positive() -> None:
    rows = [{"date": "2024-01-02", "call_gamma": "100", "put_gamma": "20"}]
    assert urm._net_gamma_sign_from_greek_rows(rows) == "positive"


def test_net_gamma_sign_negative() -> None:
    rows = [{"date": "2024-01-02", "call_gamma": "1", "put_gamma": "-500"}]
    assert urm._net_gamma_sign_from_greek_rows(rows) == "negative"


def test_net_gamma_picks_latest_date() -> None:
    rows = [
        {"date": "2024-01-01", "call_gamma": "999", "put_gamma": "0"},
        {"date": "2024-01-03", "call_gamma": "1", "put_gamma": "-5"},
    ]
    assert urm._net_gamma_sign_from_greek_rows(rows) == "negative"


def test_dark_pool_aggregate_top_prices() -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    trades = [
        {"ticker": "XX", "price": "10", "volume": "100", "executed_at": now},
        {"ticker": "XX", "price": "10.0", "volume": "50", "executed_at": now},
        {"ticker": "XX", "price": "20", "volume": "1000", "executed_at": now},
    ]
    agg = urm._aggregate_dark_pool_levels(trades, max_levels=2, max_age_hours=2000)
    assert agg.get("XX") == [20.0, 10.0]


def test_refresh_live_empty_on_uw_failure(monkeypatch) -> None:
    monkeypatch.setenv("UW_REGIME_USE_LIVE_API", "true")

    def _fail(*_a, **_k):
        return {"data": [], "_uw_api_failure": True}

    monkeypatch.setattr(urm, "_uw_get_regime", _fail)
    m = urm.UWRegimeMatrix()
    assert m.gex_profile == {}
    assert m.dark_pool_levels == {}
    assert m.recent_sweeps == {}
    assert m._source == "live_uw_daily_refresh"
