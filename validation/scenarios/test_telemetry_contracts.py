"""
Data-integrity tests: telemetry schema validators and master_trade_log single-append contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def test_validate_master_trade_log():
    from src.contracts.telemetry_schemas import validate_master_trade_log
    ok, issues = validate_master_trade_log({
        "trade_id": "live:AAPL:2026-03-01T12:00:00",
        "symbol": "AAPL",
        "entry_ts": "2026-03-01T12:00:00",
        "exit_ts": "2026-03-01T14:00:00",
        "source": "live",
    })
    assert ok, issues
    ok2, issues2 = validate_master_trade_log({"trade_id": "x"})
    assert not ok2 and any("missing" in i for i in issues2)


def test_validate_exit_attribution_direction_intel_embed():
    from src.contracts.telemetry_schemas import validate_exit_attribution
    ok, _ = validate_exit_attribution({
        "symbol": "AAPL",
        "timestamp": "2026-03-01T14:00:00",
        "entry_timestamp": "2026-03-01T12:00:00",
        "exit_reason": "profit",
        "direction_intel_embed": {"intel_snapshot_entry": {"premarket_intel": {}}, "intel_snapshot_exit": {}},
    })
    assert ok
    ok2, issues2 = validate_exit_attribution({
        "symbol": "AAPL",
        "timestamp": "2026-03-01T14:00:00",
        "entry_timestamp": "2026-03-01T12:00:00",
        "exit_reason": "profit",
        "direction_intel_embed": "not_a_dict",
    })
    assert not ok2 and any("direction_intel_embed" in i for i in issues2)


def test_master_trade_log_single_append_guard_exists():
    from utils import master_trade_log
    assert hasattr(master_trade_log, "_appended_trade_ids")
    assert isinstance(master_trade_log._appended_trade_ids, set)
