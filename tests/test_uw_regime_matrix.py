"""UW regime matrix (shadow dictionary) — conviction rules and safety."""
from __future__ import annotations

import math

import pytest

from src.market_intelligence.uw_regime_matrix import UWRegimeMatrix, reset_uw_regime_matrix_for_tests


@pytest.fixture(autouse=True)
def _reset():
    reset_uw_regime_matrix_for_tests()
    yield
    reset_uw_regime_matrix_for_tests()


def test_missing_ticker_neutral_no_crash() -> None:
    m = UWRegimeMatrix()
    out = m.evaluate_trade_conviction("NOTINTABLE", "momentum_scalp", 10.0)
    assert out["regime_conviction"] == "neutral"
    assert out["gex_read"] == "neutral"
    assert out["sweeps_recent"] is False


def test_positive_gex_momentum_veto() -> None:
    m = UWRegimeMatrix()
    out = m.evaluate_trade_conviction("MSFT", "momentum_long", 380.0)
    assert out["regime_conviction"] == "veto"
    assert out["momentum_strategy"] is True


def test_negative_gex_sweeps_boost() -> None:
    m = UWRegimeMatrix()
    out = m.evaluate_trade_conviction("AAPL", "mean_reversion", 175.0)
    assert out["regime_conviction"] == "high_conviction_boost"
    assert out["dark_pool_support"] is True


def test_evaluate_never_raises(monkeypatch) -> None:
    m = UWRegimeMatrix()

    def _boom(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(m, "_evaluate_trade_conviction_inner", _boom)
    out = m.evaluate_trade_conviction("AAPL", "x", 1.0)
    assert out["regime_conviction"] == "neutral"
    assert "shadow_uw_regime_error" in out


def test_dp_distance_finite_when_price_tiny() -> None:
    m = UWRegimeMatrix()
    out = m.evaluate_trade_conviction("AAPL", "hold", 1e-15)
    assert out["regime_conviction"] in ("neutral", "high_conviction_boost")
    mf = out.get("dark_pool_min_distance_frac")
    assert mf is None or (isinstance(mf, float) and math.isfinite(mf))
