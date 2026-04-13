"""LiveModelEngine hot_reload and CRITICAL_FAILURE path."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


def test_hot_reload_restores_after_manual_break(tmp_path: Path, monkeypatch) -> None:
    pytest.importorskip("xgboost")
    src = Path(__file__).resolve().parents[1] / "models" / "live_whale_v1.json"
    if not src.is_file():
        pytest.skip("missing live_whale_v1.json")
    dst = tmp_path / "live_whale_v1.json"
    dst.write_bytes(src.read_bytes())

    from src.ml.inference_engine import LiveModelEngine

    eng = LiveModelEngine(dst)
    assert eng.available
    p0 = eng.predict_proba_sync({})
    assert p0 is not None

    dst.unlink()
    assert eng.hot_reload() is False
    assert not eng.available

    dst.write_bytes(src.read_bytes())
    assert eng.hot_reload() is True
    assert eng.status == "OK"
    p1 = eng.predict_proba_sync({})
    assert p1 is not None


def test_predict_critical_on_double_failure(tmp_path: Path, monkeypatch) -> None:
    pytest.importorskip("xgboost")
    src = Path(__file__).resolve().parents[1] / "models" / "live_whale_v1.json"
    if not src.is_file():
        pytest.skip("missing live_whale_v1.json")
    dst = tmp_path / "live_whale_v1.json"
    dst.write_bytes(src.read_bytes())

    from src.ml.inference_engine import LiveModelEngine

    eng = LiveModelEngine(dst)
    assert eng.available

    alerted: list[str] = []

    def cap(detail):
        alerted.append(str(detail))
        return True

    monkeypatch.setattr(
        "telemetry.alpaca_ml_shadow_alerts.notify_ml_engine_critical_failure",
        cap,
    )

    with patch.object(eng, "_predict_once", side_effect=[RuntimeError("boom"), RuntimeError("again")]):
        out = eng.predict_proba_sync({})

    assert out is None
    assert eng.status == "CRITICAL_FAILURE"
    assert not eng.available
    assert len(alerted) == 1
