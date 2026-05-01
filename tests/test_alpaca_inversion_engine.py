"""Inversion engine env gating + ML threshold."""
from __future__ import annotations

import pytest

from src.ml import alpaca_inversion_engine as inv


def test_inversion_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ALPACA_INVERSION_ENGINE_ENABLED", raising=False)
    s, meta = inv.try_invert_entry_side(
        executor=object(),
        symbol="SPY",
        side="buy",
        qty=1,
        entry_score=5.0,
        entry_components={},
        market_regime="NEUTRAL",
    )
    assert s == "buy"
    assert meta is None


def test_inversion_flips_when_ml_penalizes(monkeypatch):
    monkeypatch.setenv("ALPACA_INVERSION_ENGINE_ENABLED", "1")
    monkeypatch.setenv("ALPACA_INVERSION_MIN_ENTRY_SCORE", "1.0")
    monkeypatch.setenv("ALPACA_INVERSION_ML_PRED_MAX", "-0.001")

    def _pred(**_kwargs):
        return -0.5

    monkeypatch.setattr("src.ml.alpaca_shadow_scorer.predict_expected_eod_return", _pred)
    s, meta = inv.try_invert_entry_side(
        executor=object(),
        symbol="SPY",
        side="buy",
        qty=1,
        entry_score=3.0,
        entry_components={"flow": 1.0},
        market_regime="NEUTRAL",
    )
    assert s == "sell"
    assert meta is not None
    assert meta.get("new_side") == "sell"
    assert meta.get("ml_expected_eod_return") == -0.5
