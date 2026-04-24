"""Tests for governance Telegram quiet-hours gating (America/New_York)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest import mock

from scripts.alpaca_telegram import should_suppress_governance_telegram_send


def test_respect_off_never_suppresses():
    wed_15_et = datetime(2026, 3, 25, 19, 30, tzinfo=timezone.utc)  # 15:30 EDT
    with mock.patch.dict(os.environ, {"TELEGRAM_GOVERNANCE_RESPECT_MARKET_HOURS": "0"}, clear=False):
        assert should_suppress_governance_telegram_send(wed_15_et) is False


def test_weekend_suppresses():
    sat = datetime(2026, 3, 28, 16, 0, tzinfo=timezone.utc)  # Saturday ET
    with mock.patch.dict(os.environ, {"TELEGRAM_GOVERNANCE_RESPECT_MARKET_HOURS": "1"}, clear=False):
        assert should_suppress_governance_telegram_send(sat) is True


def test_weekday_inside_window_not_suppressed():
    # 2026-03-25 Wednesday 18:00 UTC ≈ 14:00 Eastern (EDT)
    wed_14_et = datetime(2026, 3, 25, 18, 0, tzinfo=timezone.utc)
    with mock.patch.dict(
        os.environ,
        {"TELEGRAM_GOVERNANCE_RESPECT_MARKET_HOURS": "1"},
        clear=False,
    ):
        assert should_suppress_governance_telegram_send(wed_14_et) is False


def test_weekday_before_start_suppressed():
    wed_06_et = datetime(2026, 3, 25, 11, 0, tzinfo=timezone.utc)  # 07:00 EDT
    with mock.patch.dict(
        os.environ,
        {
            "TELEGRAM_GOVERNANCE_RESPECT_MARKET_HOURS": "1",
            "TELEGRAM_GOVERNANCE_ET_SEND_START_HOUR": "8",
        },
        clear=False,
    ):
        assert should_suppress_governance_telegram_send(wed_06_et) is True


def test_weekday_at_or_after_end_suppressed():
    wed_22_et = datetime(2026, 3, 26, 2, 0, tzinfo=timezone.utc)  # 22:00 EDT Mar 25
    with mock.patch.dict(os.environ, {"TELEGRAM_GOVERNANCE_RESPECT_MARKET_HOURS": "1"}, clear=False):
        assert should_suppress_governance_telegram_send(wed_22_et) is True


def test_zoneinfo_available():
    assert should_suppress_governance_telegram_send(datetime.now(timezone.utc)) in (True, False)
