"""Unit tests for options wheel gates (SP100, put wall math, dust floor, OCC strike)."""

from __future__ import annotations

import pytest

from src import options_engine as oe


def test_sp100_contains_aapl_and_brk_hyphen() -> None:
    assert oe.is_sp100_wheel_eligible("AAPL")
    assert oe.is_sp100_wheel_eligible("BRK-B")
    assert oe.is_sp100_wheel_eligible("BRK.B")
    assert not oe.is_sp100_wheel_eligible("XLF")


def test_occ_strike_price_put() -> None:
    assert oe.occ_strike_price("MSFT240315P00350000") == pytest.approx(350.0)


def test_premium_meets_min_credit() -> None:
    assert oe.premium_meets_min_credit(2.5, 200) is True
    assert oe.premium_meets_min_credit(2.0, 200) is True
    assert oe.premium_meets_min_credit(1.99, 200) is False
    assert oe.premium_meets_min_credit(1.5, 200) is False
    assert oe.premium_meets_min_credit(0.05, 0) is True


def test_institutional_put_floor_ok_synthetic() -> None:
    spot = 100.0
    rows = [
        {"option_symbol": "TEST260320P00090000", "curr_oi": 12_000},
        {"option_symbol": "TEST260320P00095000", "curr_oi": 3000},
    ]
    body = {"data": rows}

    def fake_get(endpoint: str, params=None, cache_policy=None):
        if "oi-change" in endpoint:
            return 200, body, {}
        return 200, {"data": {}}, {}

    import src.options_engine as mod

    orig = mod.uw_http_get
    mod.uw_http_get = fake_get  # type: ignore
    try:
        snap = mod.compute_put_wall_from_oi_change("TEST", spot, min_wall_oi=5000)
        assert snap.ok_data and snap.wall_strike == 90.0
        ok, _ = mod.institutional_put_floor_ok("TEST", spot, 92.0, min_wall_oi=5000)
        assert ok
        ok2, _ = mod.institutional_put_floor_ok("TEST", spot, 88.0, min_wall_oi=5000)
        assert not ok2
    finally:
        mod.uw_http_get = orig  # type: ignore


def test_iv_rank_monkeypatch() -> None:
    def fake_iv(endpoint: str, params=None, cache_policy=None):
        return 200, {"data": {"iv_rank": 62.5}}, {}

    import src.options_engine as mod

    orig = mod.uw_http_get
    mod.uw_http_get = fake_iv  # type: ignore
    try:
        assert mod.iv_rank_at_least("AAPL", 50) is True
        assert mod.iv_rank_at_least("AAPL", 70) is False
    finally:
        mod.uw_http_get = orig  # type: ignore


def test_circuit_breaker_gap_down() -> None:
    assert oe.circuit_breaker_gap_down(60.0, 100.0, threshold=0.35) is True
    assert oe.circuit_breaker_gap_down(95.0, 100.0, threshold=0.35) is False


def test_resolve_spot_wide_nbbo_uses_mid() -> None:
    from strategies import wheel_strategy as ws

    q = {"ask": 110.0, "bid": 100.0, "last_trade": None, "source_fields_present": []}
    spot, src = ws.resolve_spot_from_market_data(q, None, wide_nbbo_frac=0.05)
    assert src == "mid_nbbo_wide"
    assert spot == pytest.approx(105.0)

    q_tight = {"ask": 100.1, "bid": 100.0, "last_trade": None, "source_fields_present": []}
    spot2, src2 = ws.resolve_spot_from_market_data(q_tight, None, wide_nbbo_frac=0.05)
    assert src2 == "ask"
    assert spot2 == pytest.approx(100.1)


def test_resolve_option_short_sell_limit_uses_bid() -> None:
    from strategies import wheel_strategy as ws

    class _Q:
        ap = 2.5
        bp = 2.1

    class _Api:
        def get_latest_quote(self, sym: str):
            return _Q()

    lim, src, err = ws.resolve_option_short_sell_limit_per_share(_Api(), "FAKE260320P00090000")
    assert err == ""
    assert src == "bid"
    assert lim == pytest.approx(2.1)


def test_submit_wheel_broker_order_uses_guarded_executor_when_present() -> None:
    from unittest.mock import MagicMock

    from strategies import wheel_strategy as ws

    api = MagicMock()
    ex = MagicMock()
    ex._submit_order_guarded.return_value = MagicMock(id="ord-guarded")
    ws.submit_wheel_broker_order(
        api,
        ex,
        symbol="SPY260101C00500000",
        qty=1,
        side="sell",
        order_type="limit",
        time_in_force="day",
        limit_price=1.25,
        client_order_id="wheel-test-cid",
        caller="pytest_wheel",
    )
    ex._submit_order_guarded.assert_called_once()
    kw = ex._submit_order_guarded.call_args.kwargs
    assert kw["symbol"] == "SPY260101C00500000"
    assert kw["qty"] == 1
    assert kw["order_type"] == "limit"
    assert kw["limit_price"] == 1.25
    api.submit_order.assert_not_called()


def test_submit_wheel_broker_order_falls_back_to_raw_api() -> None:
    from unittest.mock import MagicMock

    from strategies import wheel_strategy as ws

    api = MagicMock()
    api.submit_order.return_value = {"id": "raw-1"}
    ws.submit_wheel_broker_order(
        api,
        None,
        symbol="QQQ260101P00400000",
        qty=1,
        side="sell",
        order_type="limit",
        time_in_force="day",
        limit_price=0.5,
        client_order_id=None,
        caller="pytest_wheel",
    )
    api.submit_order.assert_called_once()
    call_kw = api.submit_order.call_args.kwargs
    assert call_kw["type"] == "limit"
    assert call_kw["symbol"] == "QQQ260101P00400000"


def test_wheel_run_fails_closed_on_list_positions_error() -> None:
    from unittest.mock import MagicMock, patch

    from strategies import wheel_strategy as ws

    api = MagicMock()
    api.get_account.return_value = MagicMock(
        equity=100_000.0,
        buying_power=100_000.0,
        cash=50_000.0,
        multiplier=1.0,
    )
    api.list_positions.side_effect = RuntimeError("broker unavailable")
    cfg = {"csp": {}, "cc": {}, "risk": {}, "max_concurrent_positions": 5, "universe_max_candidates": True}

    with patch.object(ws, "_select_wheel_tickers", return_value=([], [], [])):
        r = ws.run(api, cfg)
    assert r.get("csp_placed", 0) == 0
    assert r.get("cc_placed", 0) == 0
    assert any("list_positions" in str(e) for e in r.get("errors", []))
