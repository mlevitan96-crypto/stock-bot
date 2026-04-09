"""Alpaca stream feed resolution and SIP→IEX failover helpers."""
from __future__ import annotations

import json

from src.alpaca.stream_feed import (
    auth_error_triggers_sip_to_iex_failover,
    preferred_feed_from_data_tier,
    stream_data_ws_url,
)


def test_preferred_feed_basic_vs_premium():
    assert preferred_feed_from_data_tier("basic") == "iex"
    assert preferred_feed_from_data_tier("premium") == "sip"
    assert preferred_feed_from_data_tier("Premium") == "sip"
    assert preferred_feed_from_data_tier(None) is None
    assert preferred_feed_from_data_tier("weird_unknown") is None


def test_stream_data_ws_url():
    assert stream_data_ws_url(paper=False, feed="sip").endswith("/v2/sip")
    assert stream_data_ws_url(paper=True, feed="iex").endswith("/v2/iex")
    assert "sandbox" in stream_data_ws_url(paper=True, feed="sip")


def test_auth_error_triggers_failover_sip_only():
    raw = json.dumps([{"T": "error", "code": 402, "msg": "auth failed"}])
    assert auth_error_triggers_sip_to_iex_failover(raw, current_feed="sip") is True
    assert auth_error_triggers_sip_to_iex_failover(raw, current_feed="iex") is False


def test_auth_error_409_insufficient():
    raw = json.dumps([{"T": "error", "code": 409, "msg": "insufficient subscription"}])
    assert auth_error_triggers_sip_to_iex_failover(raw, current_feed="sip") is True
