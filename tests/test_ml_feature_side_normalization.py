import json
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from telemetry import vanguard_ml_runtime

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def flattener_mod():
    path = REPO / "scripts" / "telemetry" / "alpaca_ml_flattener.py"
    spec = importlib.util.spec_from_file_location("alpaca_ml_flattener_side_norm_test", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_normalize_features_for_side_inverts_only_directional_features() -> None:
    from src.core.ml_feature_normalization import normalize_features_for_side

    row = {
        "mlf_entry_uw_flow_strength": 2.0,
        "mlf_scoreflow_components_flow": 1.5,
        "mlf_direction_intel_embed_intel_snapshot_entry_sector_intel_sector_momentum": -0.25,
        "mlf_scoreflow_components_iv_rank": 77.0,
        "mlf_direction_intel_embed_intel_snapshot_entry_premarket_intel_premarket_volume_ratio": 3.0,
        "hour_of_day": 10.0,
        "side_enc": 1.0,
    }

    out = normalize_features_for_side(row, "short")

    assert out["mlf_entry_uw_flow_strength"] == pytest.approx(-2.0)
    assert out["mlf_scoreflow_components_flow"] == pytest.approx(-1.5)
    assert out["mlf_direction_intel_embed_intel_snapshot_entry_sector_intel_sector_momentum"] == pytest.approx(0.25)
    assert out["mlf_scoreflow_components_iv_rank"] == pytest.approx(77.0)
    assert out["mlf_direction_intel_embed_intel_snapshot_entry_premarket_intel_premarket_volume_ratio"] == pytest.approx(3.0)
    assert out["hour_of_day"] == pytest.approx(10.0)
    assert out["side_enc"] == pytest.approx(1.0)


def test_v2_manifest_features_are_classified_directional_or_absolute() -> None:
    from src.core.ml_feature_normalization import DIRECTIONAL_FEATURE_NAMES, ABSOLUTE_FEATURE_NAMES

    manifest = json.loads((REPO / "models" / "vanguard_v2_profit_agent_features.json").read_text(encoding="utf-8"))
    feature_names = {str(name).lower() for name in manifest["feature_names"]}
    classified = set(DIRECTIONAL_FEATURE_NAMES) | set(ABSOLUTE_FEATURE_NAMES)

    assert feature_names - classified == set()


def test_live_v2_vector_uses_side_normalized_features() -> None:
    x = vanguard_ml_runtime._vec_for_order(
        ["mlf_scoreflow_components_flow", "mlf_scoreflow_components_iv_rank", "hour_of_day", "side_enc"],
        {"mlf_scoreflow_components_flow": 2.0, "mlf_scoreflow_components_iv_rank": 80.0, "hour_of_day": 11.0},
        "AAPL",
        "short",
        ["AAPL"],
        ["long", "short"],
    )

    assert np.asarray(x).reshape(-1).tolist() == pytest.approx([-2.0, 80.0, 11.0, 1.0])


def test_live_v2_gate_quarantines_shorts_before_model_load(monkeypatch) -> None:
    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("short quarantine must not load radioactive V2 model")

    monkeypatch.setattr(vanguard_ml_runtime, "_load_pair", fail_if_called)

    ok, proba, reason = vanguard_ml_runtime.evaluate_v2_live_gate(symbol="AAPL", side="sell", row={})

    assert ok is True
    assert proba is None
    assert reason == "v2_short_gate_quarantined_until_retrain"


def test_flattener_rows_use_same_side_normalization(flattener_mod, tmp_path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    row = {
        "symbol": "AAPL",
        "position_side": "short",
        "trade_id": "open_AAPL_2026-04-24T14:30:00+00:00",
        "entry_ts": "2026-04-24T14:30:00+00:00",
        "exit_ts": "2026-04-24T15:00:00+00:00",
        "entry_price": 100.0,
        "exit_price": 99.0,
        "qty": 1,
        "pnl": 1.0,
        "entry_uw": {
            "flow_strength": 2.0,
            "earnings_proximity": 4.0,
        },
    }
    (logs / "exit_attribution.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")

    rows = flattener_mod.build_rows(tmp_path, 0.0, None)

    assert rows[0]["mlf_entry_uw_flow_strength"] == pytest.approx(-2.0)
    assert rows[0]["mlf_entry_uw_earnings_proximity"] == pytest.approx(4.0)
