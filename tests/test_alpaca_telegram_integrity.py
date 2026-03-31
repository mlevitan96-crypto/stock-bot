"""Tests for Alpaca Telegram integrity package (no Telegram HTTP)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from telemetry.alpaca_telegram_integrity.milestone import (
    build_milestone_snapshot,
    count_since_session_open,
    should_fire_milestone,
)
from telemetry.alpaca_telegram_integrity.session_clock import effective_regular_session_open_utc
from telemetry.alpaca_telegram_integrity.runner_core import _checkpoint_100_integrity_ok
from telemetry.alpaca_telegram_integrity.templates import (
    format_100trade_checkpoint,
    format_integrity_alert,
    format_milestone_250,
)
from telemetry.alpaca_telegram_integrity.warehouse_summary import CoverageSummary, parse_coverage_markdown


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


def test_checkpoint_100_integrity_ok():
    cov = CoverageSummary(
        path=Path("x.md"),
        execution_join_pct=99.0,
        fee_pct=100.0,
        slippage_pct=90.0,
        signal_snap_pct=90.0,
        data_ready_yes=True,
        age_hours=1.0,
    )
    ok, bad = _checkpoint_100_integrity_ok(cov, {"LEARNING_STATUS": "ARMED"}, [], [], 36.0)
    assert ok and bad == []
    ok2, bad2 = _checkpoint_100_integrity_ok(cov, {"LEARNING_STATUS": "BLOCKED"}, [], [], 36.0)
    assert not ok2


def test_format_100trade_checkpoint():
    from telemetry.alpaca_telegram_integrity.milestone import MilestoneSnapshot

    snap = MilestoneSnapshot(
        session_open_utc_iso="2026-03-30T13:30:00+00:00",
        session_anchor_et="2026-03-30",
        unique_closed_trades=100,
        realized_pnl_sum_usd=0.0,
        sample_trade_keys=[],
    )
    cov = CoverageSummary(None, 100.0, 100.0, 92.0, 91.0, True, [], 2.0)
    s = format_100trade_checkpoint(
        test=True,
        snap=snap,
        cov=cov,
        data_ready="YES",
        strict_status="ARMED",
        exit_probe_ok=True,
        precheck_ok=True,
        utc_iso="2026-03-30T18:00:00Z",
    )
    assert "100-TRADE CHECKPOINT" in s
    assert "250-trade" in s.lower()


def test_format_100trade_checkpoint_no_false_on_track_when_precheck_fails():
    from telemetry.alpaca_telegram_integrity.milestone import MilestoneSnapshot

    snap = MilestoneSnapshot(
        session_open_utc_iso="2026-03-30T13:30:00+00:00",
        session_anchor_et="2026-03-30",
        unique_closed_trades=0,
        realized_pnl_sum_usd=0.0,
        sample_trade_keys=[],
        counting_basis="integrity_armed",
        count_floor_utc_iso="(not armed",
        integrity_armed=False,
    )
    cov = CoverageSummary(None, None, None, None, None, None, [], None)
    s = format_100trade_checkpoint(
        test=True,
        snap=snap,
        cov=cov,
        data_ready="unknown",
        strict_status="BLOCKED",
        exit_probe_ok=True,
        precheck_ok=False,
        utc_iso="2026-03-30T18:00:00Z",
    )
    assert "system is on track" not in s.lower()
    assert "omitted" in s.lower()


def test_integrity_armed_zero_until_arm_epoch(tmp_path: Path):
    root = tmp_path
    (root / "logs").mkdir()
    # Post config/era_cut.json alpaca.era_cut_ts so learning_excluded_for_exit_record keeps the row.
    now = datetime(2026, 3, 31, 15, 0, tzinfo=timezone.utc)
    open_iso = effective_regular_session_open_utc(now)
    line = json.dumps(
        {
            "symbol": "ZZZ",
            "side": "LONG",
            "entry_ts": "2026-03-31T14:00:00+00:00",
            "exit_ts": open_iso.isoformat(),
            "trade_id": "open_ZZZ_2026-03-31T14:00:00+00:00",
            "pnl": "1.0",
        }
    )
    (root / "logs" / "exit_attribution.jsonl").write_text(line + "\n", encoding="utf-8")
    unarmed = build_milestone_snapshot(
        root, counting_basis="integrity_armed", arm_epoch_utc=None, now=now
    )
    assert unarmed.unique_closed_trades == 0
    assert unarmed.integrity_armed is False
    armed = build_milestone_snapshot(
        root,
        counting_basis="integrity_armed",
        arm_epoch_utc=open_iso.timestamp() - 1.0,
        now=now,
    )
    assert armed.unique_closed_trades == 1


def test_should_fire_milestone_once_per_session(tmp_path: Path):
    root = tmp_path
    (root / "logs").mkdir()
    now = datetime(2026, 3, 31, 15, 0, tzinfo=timezone.utc)
    open_iso = effective_regular_session_open_utc(now)
    # minimal exit row: need valid trade_key parts; entry_ts must be >= era_cut.json
    line = json.dumps(
        {
            "symbol": "ZZZ",
            "side": "LONG",
            "entry_ts": "2026-03-31T14:00:00+00:00",
            "exit_ts": open_iso.isoformat(),
            "trade_id": "open_ZZZ_2026-03-31T14:00:00+00:00",
            "pnl": "1.0",
        }
    )
    (root / "logs" / "exit_attribution.jsonl").write_text(line + "\n", encoding="utf-8")
    snap = count_since_session_open(root, now=now)
    st_path = root / "state" / "milestone.json"
    fire, st = should_fire_milestone(root, 1, snap, st_path)
    assert fire is True
    from telemetry.alpaca_telegram_integrity.milestone import mark_milestone_fired, save_milestone_state

    save_milestone_state(st_path, st)
    mark_milestone_fired(st_path, st)
    fire2, st2 = should_fire_milestone(root, 1, snap, st_path)
    assert fire2 is False
