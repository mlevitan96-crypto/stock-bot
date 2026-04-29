import pytest

from uw_flow_ws import _build_uri, extract_flow_symbol, uw_ws_connect_config


def test_extract_flow_symbol_common_keys():
    assert extract_flow_symbol({"symbol": "nvda"}) == "NVDA"
    assert extract_flow_symbol({"underlying_symbol": "AAPL"}) == "AAPL"
    assert extract_flow_symbol({"ticker": " SPY "}) == "SPY"
    assert extract_flow_symbol({}) is None
    assert extract_flow_symbol("not-a-dict") is None


def test_uw_ws_connect_config_bearer_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UW_WS_AUTH_MODE", raising=False)
    monkeypatch.delenv("UW_WS_BASE", raising=False)
    uri, hdrs = uw_ws_connect_config("secret-token")
    assert "token=" not in uri
    assert hdrs == [("Authorization", "Bearer secret-token")]


def test_uw_ws_connect_config_query(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UW_WS_AUTH_MODE", "query")
    monkeypatch.delenv("UW_WS_BASE", raising=False)
    uri, hdrs = uw_ws_connect_config("x/y")
    assert "token=" in uri
    assert hdrs is None


def test_uw_ws_connect_config_both(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UW_WS_AUTH_MODE", "both")
    monkeypatch.delenv("UW_WS_BASE", raising=False)
    uri, hdrs = uw_ws_connect_config("abc")
    assert "token=" in uri
    assert hdrs == [("Authorization", "Bearer abc")]


def test_build_uri_always_has_query_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UW_WS_BASE", raising=False)
    u = _build_uri("mykey")
    assert u.startswith("wss://")
    assert "token=" in u
