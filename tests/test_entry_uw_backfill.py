"""entry_uw backfill helpers (no live UW call required)."""
from __future__ import annotations

from src.exit.entry_uw_backfill import entry_uw_has_finite_ml_telemetry


def test_entry_uw_empty_fails():
    assert entry_uw_has_finite_ml_telemetry({}) is False
    assert entry_uw_has_finite_ml_telemetry(None) is False


def test_entry_uw_finite_core_passes():
    assert (
        entry_uw_has_finite_ml_telemetry(
            {"earnings_proximity": 999, "sentiment_score": 1.0, "flow_strength": 0.5}
        )
        is True
    )


def test_entry_uw_missing_eps_fails():
    assert entry_uw_has_finite_ml_telemetry({"sentiment_score": 0.0}) is False
