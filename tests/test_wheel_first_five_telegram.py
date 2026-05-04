"""Wheel First-5 submit Telegram state and formatting."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import src.wheel_first_five_telegram as ff


def test_format_message_roundtrip():
    s = ff._format_message(
        phase="CSP",
        underlying="XOM",
        action="sell CSP (cash-secured put)",
        strike=146.0,
        order_id="abc-123",
        iv_rank=62.5,
        underlying_mid=154.33,
        put_wall_strike=140.0,
    )
    assert "XOM" in s and "146" in s and "62.5" in s and "154.33" in s and "140.00" in s


def test_maybe_send_increments_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_file = tmp_path / "wheel_first_five_submit_state.json"
    monkeypatch.setattr(ff, "_state_path", lambda: state_file)
    sent: list[str] = []

    def fake_send(msg: str, log_path=None, script_name: str = "") -> bool:
        sent.append(msg)
        return True

    with patch("scripts.alpaca_telegram.send_governance_telegram", fake_send):
        ff.maybe_telegram_wheel_first_five_submit(
            phase="CSP",
            underlying="TEST",
            action="sell CSP",
            strike=10.0,
            order_id="oid-1",
            iv_rank=55.0,
            underlying_mid=12.0,
            put_wall_strike=9.0,
        )
    assert len(sent) == 1
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert data["sent"] == 1
    assert "oid-1" in data["seen_order_ids"]

    with patch("scripts.alpaca_telegram.send_governance_telegram", fake_send):
        ff.maybe_telegram_wheel_first_five_submit(
            phase="CSP",
            underlying="TEST",
            action="sell CSP",
            strike=10.0,
            order_id="oid-1",
            iv_rank=55.0,
            underlying_mid=12.0,
            put_wall_strike=9.0,
        )
    assert len(sent) == 1
