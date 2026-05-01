"""V2 live gate + OFI VPIN-style toxicity (``src/alpaca/flow_toxicity_gate``)."""
from __future__ import annotations

import pytest

from src.alpaca.flow_toxicity_gate import entry_blocked_by_vpin_ofi


@pytest.fixture
def row_toxic() -> dict:
    return {
        "ofi_l1_roll_60s_sum": 1e6,
        "ofi_l1_roll_300s_sum": 1.0,
        "hour_of_day": 10.0,
    }


@pytest.fixture
def row_calm() -> dict:
    return {
        "ofi_l1_roll_60s_sum": 100.0,
        "ofi_l1_roll_300s_sum": 5000.0,
        "hour_of_day": 10.0,
    }


def test_entry_blocked_by_vpin_ofi_toxic_row(row_toxic: dict) -> None:
    blocked, reason, spike = entry_blocked_by_vpin_ofi(row_toxic)
    assert blocked is True
    assert spike is not None and spike > 5.0
    assert "vpin" in reason.lower()


def test_entry_blocked_by_vpin_ofi_calm_row(row_calm: dict) -> None:
    blocked, reason, spike = entry_blocked_by_vpin_ofi(row_calm)
    assert blocked is False
    assert "pass" in reason.lower()
    assert spike is not None


def test_evaluate_v2_passes_calm_ofi(monkeypatch: pytest.MonkeyPatch, row_calm: dict):
    import telemetry.vanguard_ml_runtime as vmr

    def fake_predict(*a, **k):
        return 0.99, None

    monkeypatch.setattr(vmr, "predict_v2_probability", fake_predict)
    monkeypatch.setattr(
        vmr,
        "_load_pair",
        lambda *a, **k: (object(), {"feature_names": ["hour_of_day"], "symbol_classes": [], "side_classes": []}, None),
    )

    ok, p, reason = vmr.evaluate_v2_live_gate(symbol="AAPL", side="LONG", row=row_calm, threshold=0.1)
    assert ok is True
    assert reason == "v2_gate_pass"
