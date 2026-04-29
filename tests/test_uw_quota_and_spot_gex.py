import os

import pytest

from src.uw import uw_client
from uw_composite_v2 import _gamma_strikes_from_spot_gex


def test_uw_effective_daily_cap_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UW_DAILY_LIMIT", raising=False)
    monkeypatch.delenv("UW_SAFETY_BUFFER", raising=False)
    assert uw_client.uw_effective_daily_cap() == int(50000 * 0.95)


def test_gamma_strikes_from_spot_gex_list() -> None:
    spot = {"data": [{"strike": 100.0}, {"strike": 101.5}, {"x": 1}]}
    lv = _gamma_strikes_from_spot_gex(spot)
    assert 100.0 in lv
    assert 101.5 in lv


def test_gamma_strikes_from_spot_gex_empty() -> None:
    assert _gamma_strikes_from_spot_gex({}) == []
    assert _gamma_strikes_from_spot_gex(None) == []
