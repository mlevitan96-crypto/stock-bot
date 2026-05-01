"""Helpers for UW regime matrix live parsing (no network)."""
from __future__ import annotations

import json
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


def test_fetch_live_snapshot_empty_on_uw_failure(monkeypatch) -> None:
    def _fail(*_a, **_k):
        return {"data": [], "_uw_api_failure": True}

    monkeypatch.setattr(urm, "_uw_get_regime", _fail)
    snap = urm.fetch_uw_regime_live_snapshot(tickers=["SPY"])
    assert snap["gex_profile"] == {}
    assert snap["dark_pool_levels"] == {}
    assert snap["recent_sweeps"] == {}


def test_matrix_loads_cache_file(monkeypatch, tmp_path) -> None:
    path = tmp_path / "uw_rm_cache.json"
    path.write_text(
        json.dumps(
            {
                "written_at_utc": "2026-01-01T12:00:00+00:00",
                "source": "test",
                "gex_profile": {"ZZZ": "positive"},
                "dark_pool_levels": {"ZZZ": [100.0]},
                "recent_sweeps": {"ZZZ": True},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UW_REGIME_MATRIX_STATE_PATH", str(path))
    urm.reset_uw_regime_matrix_for_tests()
    m = urm.UWRegimeMatrix()
    assert m.gex_profile.get("ZZZ") == "positive"
    assert m.dark_pool_levels.get("ZZZ") == [100.0]
    assert m.recent_sweeps.get("ZZZ") is True
