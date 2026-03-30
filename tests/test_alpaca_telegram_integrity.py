"""Tests for Alpaca Telegram integrity package (no Telegram HTTP)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from telemetry.alpaca_telegram_integrity.milestone import (
    count_since_session_open,
    should_fire_milestone,
)
from telemetry.alpaca_telegram_integrity.session_clock import effective_regular_session_open_utc
from telemetry.alpaca_telegram_integrity.templates import format_integrity_alert, format_milestone_250
from telemetry.alpaca_telegram_integrity.warehouse_summary import parse_coverage_markdown


def test_parse_coverage_markdown_extracts_pct():
    text = """
# cov
- execution join coverage: **99.10%**
- fee computable (fills basis): **100.00%**
- slippage computable (exits with context+exit px): **92.00%**
- signal snapshot near exit: **91.00%**
DATA_READY: YES
"""
    d = parse_coverage_markdown(text)
    assert d["execution_join_pct"] == 99.1
    assert d["fee_pct"] == 100.0
    assert d["slippage_pct"] == 92.0
    assert d["signal_snap_pct"] == 91.0
    assert d["data_ready_yes"] is True


def test_format_milestone_250_no_crash():
    from telemetry.alpaca_telegram_integrity.milestone import MilestoneSnapshot

    snap = MilestoneSnapshot(
        session_open_utc_iso="2026-03-30T13:30:00+00:00",
        session_anchor_et="2026-03-30",
        unique_closed_trades=250,
        realized_pnl_sum_usd=-12.5,
        sample_trade_keys=["AAPL|LONG|1710000000"],
    )
    s = format_milestone_250(
        test=True,
        snap=snap,
        data_ready=None,
        strict_status=None,
        spi_rel=None,
        reports_hint="reports/",
    )
    assert "TEST" in s
    assert "250" in s


def test_format_integrity_alert_no_crash():
    s = format_integrity_alert(
        test=True,
        reasons=["a", "b"],
        last_good={"x": 1},
        action="check logs",
    )
    assert "TEST" in s
    assert "a" in s


def test_should_fire_milestone_once_per_session(tmp_path: Path):
    root = tmp_path
    (root / "logs").mkdir()
    open_iso = effective_regular_session_open_utc(
        datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc)
    )
    # minimal exit row: need valid trade_key parts
    line = json.dumps(
        {
            "symbol": "ZZZ",
            "side": "LONG",
            "entry_ts": "2026-03-30T14:00:00+00:00",
            "exit_ts": open_iso.isoformat(),
            "trade_id": "open_ZZZ_2026-03-30T14:00:00+00:00",
            "pnl": "1.0",
        }
    )
    (root / "logs" / "exit_attribution.jsonl").write_text(line + "\n", encoding="utf-8")
    snap = count_since_session_open(root, now=datetime(2026, 3, 30, 15, 0, tzinfo=timezone.utc))
    st_path = root / "state" / "milestone.json"
    fire, st = should_fire_milestone(root, 1, snap, st_path)
    assert fire is True
    from telemetry.alpaca_telegram_integrity.milestone import mark_milestone_fired, save_milestone_state

    save_milestone_state(st_path, st)
    mark_milestone_fired(st_path, st)
    fire2, st2 = should_fire_milestone(root, 1, snap, st_path)
    assert fire2 is False
