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
