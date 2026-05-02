"""Wheel risk gates: sector cap, cash-secured, dividend ex-zone (UW-backed)."""

from __future__ import annotations

import pytest

from src.wheel_risk_gates import (
    sector_cap_allows_new_csp,
    should_skip_dividend_ex_zone,
    strict_cash_secured_put_ok,
)


def _sector_tech(sym: str) -> str:
    return "Technology"


def test_sector_cap_blocks_when_projected_exceeds_fraction():
    open_csps = {
        "AAPL": [{"strike": 200.0, "qty": 1}],
    }
    ok, reason, _by = sector_cap_allows_new_csp(
        open_csps,
        "MSFT",
        10000.0,
        account_equity=100_000.0,
        max_sector_fraction=0.25,
        get_sector=_sector_tech,
    )
    assert ok is False
    assert "sector_cap" in reason


def test_sector_cap_allows_when_under_cap():
    open_csps = {}
    ok, reason, _by = sector_cap_allows_new_csp(
        open_csps,
        "AAPL",
        10_000.0,
        account_equity=100_000.0,
        max_sector_fraction=0.25,
        get_sector=_sector_tech,
    )
    assert ok is True
    assert reason == "ok"


def test_strict_cash_secured_rejects_margin_multiplier():
    ok, reason = strict_cash_secured_put_ok(
        cash=1_000_000.0,
        multiplier=2.0,
        csp_notional=5000.0,
        allow_margin_account=False,
    )
    assert ok is False
    assert reason == "margin_multiplier_gt_1"


def test_strict_cash_secured_rejects_insufficient_cash():
    ok, reason = strict_cash_secured_put_ok(
        cash=1000.0,
        multiplier=1.0,
        csp_notional=50_000.0,
        allow_margin_account=False,
    )
    assert ok is False
    assert "insufficient_cash" in reason


def test_strict_cash_secured_ok_cash_account():
    ok, reason = strict_cash_secured_put_ok(
        cash=60_000.0,
        multiplier=1.0,
        csp_notional=50_000.0,
        allow_margin_account=False,
    )
    assert ok is True
    assert reason == "ok"


def test_dividend_gate_skips_when_disabled():
    assert should_skip_dividend_ex_zone("AAPL", 0) is False


def test_dividend_gate_fail_closed_on_uw_blocked(monkeypatch):
    import src.wheel_risk_gates as wg

    def fake_get(_path, cache_policy=None):
        return (200, {"_blocked": True, "data": []}, None)

    monkeypatch.setattr(wg, "uw_http_get", fake_get)
    assert wg.should_skip_dividend_ex_zone("AAPL", 3) is True


def test_dividend_gate_skips_when_ex_outside_window(monkeypatch):
    import src.wheel_risk_gates as wg
    from datetime import date, timedelta

    far = (date.today() + timedelta(days=90)).isoformat()

    def fake_get(_path, cache_policy=None):
        return (200, {"data": [{"ex_date": far}]}, None)

    monkeypatch.setattr(wg, "uw_http_get", fake_get)
    assert wg.should_skip_dividend_ex_zone("AAPL", 3) is False


def test_dividend_gate_triggers_near_ex(monkeypatch):
    import src.wheel_risk_gates as wg
    from datetime import date, timedelta

    soon = (date.today() + timedelta(days=1)).isoformat()

    def fake_get(_path, cache_policy=None):
        return (200, {"data": [{"ex_date": soon}]}, None)

    monkeypatch.setattr(wg, "uw_http_get", fake_get)
    assert wg.should_skip_dividend_ex_zone("AAPL", 3) is True
