"""Alpaca stream feed resolution, host inference, and feed failover helpers."""
from __future__ import annotations

import json

from src.alpaca.stream_feed import (
    FEED_IEX,
    FEED_SIP,
    alpaca_trading_environment,
    auth_error_allows_feed_failover,
    auth_error_triggers_sip_to_iex_failover,
    preferred_feed_from_data_tier,
    stream_data_ws_url,
)


def test_preferred_feed_basic_vs_premium():
    assert preferred_feed_from_data_tier("basic") == FEED_IEX
    assert preferred_feed_from_data_tier("premium") == FEED_SIP
    assert preferred_feed_from_data_tier("Premium") == FEED_SIP
    assert preferred_feed_from_data_tier(None) is None
    assert preferred_feed_from_data_tier("weird_unknown") is None


def test_alpaca_trading_environment_from_base_url():
    assert alpaca_trading_environment("https://paper-api.alpaca.markets") == "paper"
    assert alpaca_trading_environment("https://api.alpaca.markets") == "live"
    assert alpaca_trading_environment("") == "unknown"


def test_stream_data_ws_url_from_trading_base_url():
    u_paper = stream_data_ws_url(feed=FEED_SIP, trading_base_url="https://paper-api.alpaca.markets")
    assert u_paper.endswith(f"/v2/{FEED_SIP}")
    assert "sandbox" not in u_paper
    assert "stream.data.alpaca.markets" in u_paper
    u_live = stream_data_ws_url(feed=FEED_IEX, trading_base_url="https://api.alpaca.markets")
    assert u_live.endswith(f"/v2/{FEED_IEX}")
    assert "sandbox" not in u_live


def test_stream_data_ws_url_legacy_paper_flag():
    assert stream_data_ws_url(paper=False, feed=FEED_SIP).endswith(f"/v2/{FEED_SIP}")
    assert stream_data_ws_url(paper=True, feed=FEED_IEX).endswith(f"/v2/{FEED_IEX}")
    assert "sandbox" not in stream_data_ws_url(paper=True, feed=FEED_SIP)


def test_stream_data_ws_url_sandbox_env(monkeypatch):
    monkeypatch.setenv("ALPACA_MARKET_DATA_STREAM_SANDBOX", "1")
    u = stream_data_ws_url(feed=FEED_SIP, trading_base_url="https://paper-api.alpaca.markets")
    assert "sandbox" in u


def test_auth_error_triggers_failover_sip_only():
    raw = json.dumps([{"T": "error", "code": 402, "msg": "auth failed"}])
    assert auth_error_triggers_sip_to_iex_failover(raw, current_feed=FEED_SIP) is True
    assert auth_error_triggers_sip_to_iex_failover(raw, current_feed=FEED_IEX) is False


def test_auth_error_allows_failover_any_feed_when_enabled():
    raw = json.dumps([{"T": "error", "code": 402, "msg": "auth failed"}])
    assert auth_error_allows_feed_failover(raw, can_try_alternate=True) is True
    assert auth_error_allows_feed_failover(raw, can_try_alternate=False) is False


def test_auth_error_409_insufficient():
    raw = json.dumps([{"T": "error", "code": 409, "msg": "insufficient subscription"}])
    assert auth_error_triggers_sip_to_iex_failover(raw, current_feed=FEED_SIP) is True
