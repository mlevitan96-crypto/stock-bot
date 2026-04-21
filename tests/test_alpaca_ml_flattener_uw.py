"""ALP-UW-003: first-class UW gamma / tide columns on flattener."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def flattener_mod():
    path = REPO / "scripts" / "telemetry" / "alpaca_ml_flattener.py"
    spec = importlib.util.spec_from_file_location("alpaca_ml_flattener_test", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_uw_gamma_skew_top_level(flattener_mod):
    g, t = flattener_mod._uw_gamma_skew_and_tide({"greeks_gamma": 0.42, "market_tide": -0.17})
    assert g == pytest.approx(0.42)
    assert t == pytest.approx(-0.17)


def test_uw_fallback_iv_skew(flattener_mod):
    g, t = flattener_mod._uw_gamma_skew_and_tide({"iv_skew": 0.11, "market_tide": 0.05})
    assert g == pytest.approx(0.11)
    assert t == pytest.approx(0.05)


def test_uw_nested_components(flattener_mod):
    eu = {"components": {"greeks_gamma": 0.33, "market_tide": 0.44}}
    g, t = flattener_mod._uw_gamma_skew_and_tide(eu)
    assert g == pytest.approx(0.33)
    assert t == pytest.approx(0.44)


def test_uw_missing_defaults_zero(flattener_mod):
    g, t = flattener_mod._uw_gamma_skew_and_tide({})
    assert g == 0.0 and t == 0.0


def test_dedupe_collapses_same_trade_key_distinct_trade_ids(flattener_mod):
    tk = "DEDUPE|LONG|1704067200"
    r1 = {
        "trade_id": "open_DEDUPE_2026-01-01T10:00:00+00:00",
        "trade_key": tk,
        "symbol": "DEDUPE",
        "position_side": "long",
        "exit_ts": "2026-05-01T15:00:00+00:00",
    }
    r2 = {
        "trade_id": "open_DEDUPE_2026-01-01T11:00:00+00:00",
        "trade_key": tk,
        "symbol": "DEDUPE",
        "position_side": "long",
        "exit_ts": "2026-05-01T16:00:00+00:00",
    }
    out = flattener_mod._dedupe_exit_rows([r1, r2])
    assert len(out) == 1
    assert out[0]["trade_id"] == r2["trade_id"]


def test_uw_scoreflow_components_shadows_slim_entry_uw(flattener_mod):
    """entry_uw from exit_attribution is v2_uw_inputs (flow/dp/sentiment) — gamma/tide come from composite."""
    eu = {"flow_strength": 0.5, "sentiment_score": 0.1}
    comp = {"greeks_gamma": 0.21, "market_tide": -0.09}
    merged = {**eu, "components": comp}
    g, t = flattener_mod._uw_gamma_skew_and_tide(merged)
    assert g == pytest.approx(0.21)
    assert t == pytest.approx(-0.09)
