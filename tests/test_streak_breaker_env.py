"""Offense streak shield defaults off unless OFFENSE_STREAK_SHIELD_ENABLED=1."""
from __future__ import annotations

import pytest

from src.offense import streak_breaker as sb


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("OFFENSE_STREAK_SHIELD_ENABLED", raising=False)
    yield


def test_streak_disabled_by_default(monkeypatch):
    monkeypatch.setattr(sb, "_load", lambda: {"entry_block_until_utc": "2099-01-01T00:00:00+00:00"})
    blocked, reason = sb.entry_blocked_by_streak()
    assert blocked is False
    assert reason == ""


def test_streak_enabled_respects_block(monkeypatch):
    monkeypatch.setenv("OFFENSE_STREAK_SHIELD_ENABLED", "1")
    monkeypatch.setattr(sb, "_load", lambda: {"entry_block_until_utc": "2099-01-01T00:00:00+00:00"})
    blocked, reason = sb.entry_blocked_by_streak()
    assert blocked is True
    assert reason == "offense_streak_two_losses_30m"
