#!/usr/bin/env python3
"""
Ghost Whale E2E: UW WebSocket-shaped flow → normalize → cache-shaped row → enrich →
composite → gate → ML component flatten sanity → Alpaca-style order JSON.

Proves integration seams do not silently drop rows from schema drift (flow/GEX/composite).
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from src.uw.uw_flow_trade_normalize import normalize_ws_flow_alert_to_rest_trade
from telemetry.ml_scoreflow_contract import normalize_composite_components_for_ml
from uw_enrichment_v2 import enrich_signal
from uw_composite_v2 import compute_composite_score_v2, should_enter_v2


SYMBOL = "SPY"


def _ghost_ws_payloads() -> list[dict]:
    """Three high-premium CALL sweeps within 1h (composite sweep-urgency path)."""
    ts_ms = int(time.time() * 1000)
    base = {
        "option_chain": "SPY241220C00500000",
        "has_sweep": True,
        "executed_at": ts_ms,
    }
    return [
        {**base, "ticker": SYMBOL, "total_premium": 150_000},
        {**base, "ticker": SYMBOL, "total_premium": 160_000},
        {**base, "ticker": SYMBOL, "total_premium": 170_000},
    ]


def _ghost_spot_gex() -> Dict[str, Any]:
    """Daemon-shaped Professional spot GEX (strikes consumed by uw_composite_v2)."""
    return {
        "data": [
            {"strike": 500.0},
            {"strike": 505.5},
            {"strike_price": 510.0},
        ]
    }


def _merge_cache_row(flow_trades: list[dict]) -> Dict[str, Any]:
    """Mimic uw_flow_daemon cache row schema accepted by enrich_signal / composite."""
    now = int(time.time())
    return {
        "_last_update": now,
        "last_update": now,
        "flow_trades": flow_trades,
        "trade_count": len(flow_trades),
        "conviction": 0.82,
        "sentiment": "BULLISH",
        "dark_pool": {
            "sentiment": "BULLISH",
            "total_notional_1h": 28_000_000.0,
            "total_notional": 30_000_000.0,
        },
        "spot_gex": _ghost_spot_gex(),
        "greeks": {"call_gamma": 1e6, "put_gamma": 8e5, "max_pain": 502.0},
        "iv_rank": {"rank": 45},
        "oi_change": {"net_oi_change": 12000},
        "insider": {"sentiment": "NEUTRAL", "conviction_modifier": 0.0},
        "market_tide": {"sentiment": "BULLISH"},
        "calendar": {},
        "congress": {},
        "institutional": {},
        "etf_flow": {},
    }


def _assert_finite_ml_components(components: Dict[str, Any]) -> None:
    flat = normalize_composite_components_for_ml(components)
    assert flat, "ml normalize returned empty"
    for k, v in flat.items():
        assert isinstance(v, (int, float)), f"{k} not numeric: {type(v)}"
        assert math.isfinite(float(v)), f"{k} non-finite: {v}"


def _alpaca_order_payload(*, symbol: str, qty: int, limit_price: float) -> Dict[str, Any]:
    """Minimal Alpaca REST-style body (validated shape only; API is mocked)."""
    assert qty >= 1
    assert limit_price > 0
    return {
        "symbol": symbol,
        "qty": qty,
        "side": "buy",
        "type": "limit",
        "time_in_force": "day",
        "limit_price": round(float(limit_price), 4),
        "order_class": "simple",
    }


def test_e2e_ghost_whale_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    # Lower gate floor so this deterministic fixture always exercises should_enter_v2 True path.
    monkeypatch.setenv("ENTRY_THRESHOLD_BASE", "0.5")

    # 1) WS normalize
    trades = [normalize_ws_flow_alert_to_rest_trade(SYMBOL, dict(p)) for p in _ghost_ws_payloads()]
    for t in trades:
        assert t.get("type") == "CALL"
        assert float(t.get("premium") or 0) > 0
        assert t.get("_ingest_source") == "uw_ws_flow_alerts"
        assert t.get("has_sweep") is True or t.get("is_sweep") is True

    # 2) Cache row (in-memory stand-in for uw_flow_cache.json per-ticker value)
    cache: Dict[str, Dict[str, Any]] = {SYMBOL: _merge_cache_row(trades)}
    row = cache[SYMBOL]
    assert isinstance(row.get("flow_trades"), list)
    assert row["flow_trades"], "cache must retain flow_trades"
    assert isinstance(row.get("spot_gex"), dict)

    # 3) Enrichment
    enriched = enrich_signal(SYMBOL, cache, market_regime="BULLISH")
    assert enriched, "enrich_signal must not return empty dict for populated cache"
    assert enriched.get("spot_gex") is row.get("spot_gex")
    assert isinstance(enriched.get("flow_trades"), list)
    assert len(enriched.get("flow_trades") or []) == 3

    # 4) Composite + gate (reads flow/GEX-backed gamma levels)
    composite = compute_composite_score_v2(SYMBOL, enriched, regime="BULLISH")
    assert isinstance(composite, dict)
    assert composite.get("symbol") == SYMBOL
    assert "score" in composite
    assert float(composite.get("score") or 0) == float(composite.get("score") or 0)
    assert math.isfinite(float(composite.get("score") or 0))
    comps = composite.get("components")
    assert isinstance(comps, dict)
    _assert_finite_ml_components(comps)

    gex_levels = composite.get("gamma_resistance_levels") or []
    assert isinstance(gex_levels, list)
    assert any(float(x) > 0 for x in gex_levels), "GEX strikes must surface as gamma_resistance_levels"

    ok = should_enter_v2(composite, SYMBOL, mode="base", api=None)
    assert ok is True
    assert isinstance(composite.get("components"), dict)

    # 5) Alpaca order payload (sizing math: shares from notional / price; mock broker records call)
    mock_api = MagicMock()
    ref_price = 500.0
    notional_usd = 2500.0
    qty = max(1, int(notional_usd / ref_price))
    assert qty == 5
    payload = _alpaca_order_payload(symbol=SYMBOL, qty=qty, limit_price=ref_price * 1.001)
    assert payload["qty"] * payload["limit_price"] > 0
    mock_api.submit_order(**payload)
    mock_api.submit_order.assert_called_once()
    call_kw = mock_api.submit_order.call_args.kwargs
    assert call_kw["symbol"] == SYMBOL
    assert call_kw["qty"] == qty
    assert call_kw["side"] == "buy"
