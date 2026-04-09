"""Canonical Alpaca credential resolution (registry)."""
from __future__ import annotations

import os

from config.registry import get_alpaca_trading_credentials, normalize_alpaca_key_secret


def test_strip_surrounding_quotes(monkeypatch):
    monkeypatch.setenv("ALPACA_KEY", '"PK123"')
    monkeypatch.setenv("ALPACA_SECRET", "'sec123'")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    k, s, _ = get_alpaca_trading_credentials()
    assert k == "PK123"
    assert s == "sec123"


def test_alias_precedence_alpaca_key_wins(monkeypatch):
    monkeypatch.delenv("ALPACA_KEY", raising=False)
    monkeypatch.setenv("ALPACA_API_KEY", "from_api")
    monkeypatch.setenv("ALPACA_SECRET", "sec")
    monkeypatch.setenv("ALPACA_BASE_URL", "https://api.alpaca.markets")
    k, _, b = get_alpaca_trading_credentials()
    assert k == "from_api"
    assert "api.alpaca" in b


def test_normalize_alpaca_key_secret_tuple():
    k, s = normalize_alpaca_key_secret(' "abc" ', "  xyz  ")
    assert k == "abc"
    assert s == "xyz"
