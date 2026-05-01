"""VPIN-ofi proxy gate from L1 OFI telemetry fields."""
from __future__ import annotations

import pytest

from src.alpaca.flow_toxicity_gate import entry_blocked_by_vpin_ofi, load_vpin_ofi_gate_config


def test_load_vpin_cfg_from_repo_profile():
    cfg = load_vpin_ofi_gate_config()
    assert isinstance(cfg, dict)


def test_fail_open_when_ofi_missing():
    blocked, reason, spike = entry_blocked_by_vpin_ofi({}, cfg={"enabled": True, "failure_mode": "fail_open"})
    assert blocked is False
    assert "fail_open" in reason
    assert spike is None


def test_toxic_when_spike_exceeds_max():
    cfg = {
        "enabled": True,
        "failure_mode": "fail_open",
        "toxic_spike_ratio_max": 2.0,
        "abs_ofi_300_floor": 100.0,
    }
    blocked, reason, spike = entry_blocked_by_vpin_ofi(
        {"ofi_l1_roll_60s_sum": 900.0, "ofi_l1_roll_300s_sum": 100.0},
        cfg=cfg,
    )
    assert blocked is True
    assert reason == "vpin_ofi_toxicity_veto"
    assert spike is not None and spike > 2.0


def test_pass_when_spike_below_max():
    cfg = {
        "enabled": True,
        "failure_mode": "fail_open",
        "toxic_spike_ratio_max": 10.0,
        "abs_ofi_300_floor": 500.0,
    }
    blocked, reason, spike = entry_blocked_by_vpin_ofi(
        {"ofi_l1_roll_60s_sum": 100.0, "ofi_l1_roll_300s_sum": 200.0},
        cfg=cfg,
    )
    assert blocked is False
    assert reason == "vpin_ofi_pass"
    assert spike is not None
