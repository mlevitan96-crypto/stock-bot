"""
Contract tests for attribution schema (Phase 1).
Fail hard if: total_score != sum(contributions), missing entry/exit snapshot, missing exit_reason_code.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import pytest
from schema.contract_validation import (
    validate_snapshot_score,
    validate_trade_attribution,
    _sum_contributions,
)


def test_sum_contributions():
    components = [
        {"contribution_to_score": 0.5},
        {"contribution_to_score": -0.2},
        {"contribution_to_score": 0.1},
    ]
    assert _sum_contributions(components) == pytest.approx(0.4)


def test_sum_contributions_with_sub():
    components = [
        {"contribution_to_score": 0.5},
        {"contribution_to_score": 0.1, "sub_components": [{"contribution_to_score": 0.2}]},
    ]
    assert _sum_contributions(components) == pytest.approx(0.8)


def test_validate_snapshot_score_ok():
    snapshot = {
        "total_score": 1.0,
        "components": [
            {"contribution_to_score": 0.6},
            {"contribution_to_score": 0.4},
        ],
    }
    ok, msg = validate_snapshot_score(snapshot)
    assert ok, msg
    assert msg == ""


def test_validate_snapshot_score_fail():
    snapshot = {
        "total_score": 1.0,
        "components": [
            {"contribution_to_score": 0.5},
            {"contribution_to_score": 0.3},
        ],
    }
    ok, msg = validate_snapshot_score(snapshot)
    assert not ok
    assert "total_score" in msg and "sum" in msg


def test_validate_trade_attribution_ok():
    record = {
        "trade_id": "T1",
        "symbol": "AAPL",
        "exit_reason_code": "time_exit",
        "entry_snapshot": {"total_score": 3.0, "components": [{"contribution_to_score": 3.0}]},
        "exit_snapshot": {"total_score": 2.0, "components": [{"contribution_to_score": 2.0}]},
    }
    ok, errors = validate_trade_attribution(record)
    assert ok, errors
    assert len(errors) == 0


def test_validate_trade_attribution_missing_exit_reason():
    record = {
        "trade_id": "T1",
        "symbol": "AAPL",
        "exit_snapshot": {"total_score": 2.0, "components": [{"contribution_to_score": 2.0}]},
    }
    ok, errors = validate_trade_attribution(record)
    assert not ok
    assert any("exit_reason_code" in e for e in errors)


def test_validate_trade_attribution_entry_score_mismatch():
    record = {
        "trade_id": "T1",
        "symbol": "AAPL",
        "exit_reason_code": "trail_stop",
        "entry_snapshot": {"total_score": 5.0, "components": [{"contribution_to_score": 1.0}]},
    }
    ok, errors = validate_trade_attribution(record)
    assert not ok
    assert any("entry_snapshot" in e for e in errors)
