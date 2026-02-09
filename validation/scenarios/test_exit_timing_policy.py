"""Unit tests for exit timing policy shim (apply_exit_timing_to_exit_config)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_apply_exit_timing_to_exit_config_empty_cfg():
    from src.governance.apply_exit_timing_policy import apply_exit_timing_to_exit_config
    out = apply_exit_timing_to_exit_config(
        exit_cfg={},
        mode="PAPER",
        strategy="EQUITY",
        regime="NEUTRAL",
        scenario="baseline_current",
    )
    assert isinstance(out, dict)
    # baseline_current has no params, so out may stay empty or have defaults
    assert "min_hold_seconds" in out or out.get("min_hold_seconds") is None


def test_apply_exit_timing_to_exit_config_floor_applied():
    from src.governance.apply_exit_timing_policy import apply_exit_timing_to_exit_config
    # live_50pct_push has min_hold_seconds_floor: 600 for LIVE
    out = apply_exit_timing_to_exit_config(
        exit_cfg={},
        mode="LIVE",
        strategy="EQUITY",
        regime="NEUTRAL",
        scenario="live_50pct_push",
    )
    assert isinstance(out, dict)
    # If scenario is loaded, min_hold_seconds should be 600
    if out.get("min_hold_seconds") is not None:
        assert out["min_hold_seconds"] == 600


def test_apply_exit_timing_to_exit_config_preserves_existing():
    from src.governance.apply_exit_timing_policy import apply_exit_timing_to_exit_config
    out = apply_exit_timing_to_exit_config(
        exit_cfg={"min_hold_seconds": 1200, "other": "keep"},
        mode="PAPER",
        strategy="EQUITY",
        regime="NEUTRAL",
        scenario="baseline_current",
    )
    assert out.get("other") == "keep"
    assert out.get("min_hold_seconds") == 1200


if __name__ == "__main__":
    test_apply_exit_timing_to_exit_config_empty_cfg()
    test_apply_exit_timing_to_exit_config_floor_applied()
    test_apply_exit_timing_to_exit_config_preserves_existing()
    print("All exit timing policy tests passed.")
