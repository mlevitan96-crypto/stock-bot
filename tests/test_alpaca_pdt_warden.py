"""PDT Warden scaffold — risk profile + account equity / rolling count."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.alpaca.pdt_warden import PDTWarden, allow_v2_threshold_relaxation, load_alpaca_risk_profile


def test_load_default_risk_profile():
    p = load_alpaca_risk_profile()
    assert p.pdt_mode == "strict"
    assert p.min_equity_threshold == 25_000
    assert p.rolling_5d_day_trade_limit == 3
    assert p.wash_sale_buffer_days == 31


def test_load_custom_profile(tmp_path: Path):
    f = tmp_path / "rp.json"
    f.write_text(
        json.dumps(
            {
                "pdt_mode": "off",
                "min_equity_threshold": 100,
                "rolling_5d_day_trade_limit": 1,
                "wash_sale_buffer_days": 10,
            }
        ),
        encoding="utf-8",
    )
    p = load_alpaca_risk_profile(f)
    assert p.pdt_mode == "off"
    assert p.rolling_5d_day_trade_limit == 1


@pytest.fixture
def profile_path(tmp_path: Path) -> Path:
    f = tmp_path / "alpaca_risk_profile.json"
    f.write_text(
        json.dumps(
            {
                "pdt_mode": "strict",
                "min_equity_threshold": 25000,
                "rolling_5d_day_trade_limit": 3,
                "wash_sale_buffer_days": 31,
            }
        ),
        encoding="utf-8",
    )
    return f


def test_can_trade_above_equity_threshold(monkeypatch: pytest.MonkeyPatch, profile_path: Path):
    from src.alpaca import pdt_warden as mod

    monkeypatch.setattr(
        mod,
        "fetch_alpaca_account",
        lambda *a, **k: ({"equity": "30000"}, None),
    )
    monkeypatch.setattr(
        mod,
        "resolve_stream_feed",
        lambda *a, **k: ("sip", "iex", {"data_tier": "premium"}),
    )

    w = PDTWarden("k", "s", "https://paper-api.alpaca.markets", risk_profile_path=profile_path)
    assert w.can_trade(rolling_5d_day_trades=99) is True
    assert w.data_tier is None  # no tier key in minimal stub dict; account_data_tier_label returns None


def test_can_trade_below_threshold_respects_rolling(monkeypatch: pytest.MonkeyPatch, profile_path: Path):
    from src.alpaca import pdt_warden as mod

    monkeypatch.setattr(
        mod,
        "fetch_alpaca_account",
        lambda *a, **k: ({"equity": "10000"}, None),
    )
    monkeypatch.setattr(
        mod,
        "resolve_stream_feed",
        lambda *a, **k: ("iex", "sip", {"data_tier": "basic"}),
    )

    w = PDTWarden("k", "s", "https://paper-api.alpaca.markets", risk_profile_path=profile_path)
    assert w.can_trade(rolling_5d_day_trades=2) is True
    assert w.can_trade(rolling_5d_day_trades=3) is False


def test_pdt_mode_off_allows(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    from src.alpaca import pdt_warden as mod

    f = tmp_path / "off.json"
    f.write_text(
        json.dumps(
            {
                "pdt_mode": "off",
                "min_equity_threshold": 25000,
                "rolling_5d_day_trade_limit": 3,
                "wash_sale_buffer_days": 31,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "fetch_alpaca_account",
        lambda *a, **k: ({"equity": "1000"}, None),
    )
    monkeypatch.setattr(
        mod,
        "resolve_stream_feed",
        lambda *a, **k: ("iex", "sip", {}),
    )
    w = PDTWarden("k", "s", "https://paper-api.alpaca.markets", risk_profile_path=f)
    assert w.can_trade(rolling_5d_day_trades=10) is True


def test_allow_v2_relaxation_blocked_when_pdt_tight(monkeypatch: pytest.MonkeyPatch, profile_path: Path):
    from src.alpaca import pdt_warden as mod

    monkeypatch.setattr(
        mod,
        "fetch_alpaca_account",
        lambda *a, **k: ({"equity": "10000"}, None),
    )
    monkeypatch.setattr(
        mod,
        "resolve_stream_feed",
        lambda *a, **k: ("sip", "iex", {}),
    )
    w = PDTWarden("k", "s", "https://paper-api.alpaca.markets", risk_profile_path=profile_path)
    ok, reason = allow_v2_threshold_relaxation(
        current_threshold=0.5,
        proposed_threshold=0.3,
        warden=w,
        rolling_5d_day_trades=3,
    )
    assert ok is False
    assert "pdt" in reason


def test_allow_v2_relaxation_ok_when_above_equity(monkeypatch: pytest.MonkeyPatch, profile_path: Path):
    from src.alpaca import pdt_warden as mod

    monkeypatch.setattr(
        mod,
        "fetch_alpaca_account",
        lambda *a, **k: ({"equity": "100000"}, None),
    )
    monkeypatch.setattr(
        mod,
        "resolve_stream_feed",
        lambda *a, **k: ("sip", "iex", {}),
    )
    w = PDTWarden("k", "s", "https://paper-api.alpaca.markets", risk_profile_path=profile_path)
    ok, reason = allow_v2_threshold_relaxation(
        current_threshold=0.5,
        proposed_threshold=0.3,
        warden=w,
        rolling_5d_day_trades=99,
    )
    assert ok is True


def test_account_fetch_error_blocks(monkeypatch: pytest.MonkeyPatch, profile_path: Path):
    from src.alpaca import pdt_warden as mod

    monkeypatch.setattr(
        mod,
        "fetch_alpaca_account",
        lambda *a, **k: (None, "network"),
    )
    monkeypatch.setattr(
        mod,
        "resolve_stream_feed",
        lambda *a, **k: ("sip", "iex", {}),
    )
    w = PDTWarden("k", "s", "https://paper-api.alpaca.markets", risk_profile_path=profile_path)
    assert w.can_trade(rolling_5d_day_trades=0) is False
