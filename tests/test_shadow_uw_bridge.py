"""Shadow layer uses same UW cache + live cluster bridge as live feature snapshots."""
from __future__ import annotations

import math


def test_compute_shadow_uw_density_metrics():
    from telemetry.shadow_evaluator import compute_shadow_uw_density_metrics

    m = compute_shadow_uw_density_metrics(
        {
            "mlf_entry_uw_flow_strength": 0.5,
            "mlf_entry_uw_darkpool_bias": float("nan"),
            "hour_of_day": 14.0,
        }
    )
    assert m["shadow_uw_key_matches"] == 2
    assert m["shadow_uw_finite_count"] == 1
    assert 0.4 < m["shadow_uw_density"] < 0.6


def test_build_vanguard_feature_map_merges_cluster_v2_uw_into_row():
    from telemetry import shadow_evaluator

    if shadow_evaluator._import_flattener() is None:
        return
    row = shadow_evaluator.build_vanguard_feature_map(
        symbol="TESTSYM",
        side="buy",
        now_utc=None,
        feature_snapshot={"symbol": "TESTSYM"},
        comps={},
        cluster={
            "composite_meta": {
                "v2_uw_inputs": {
                    "flow_strength": 0.91,
                    "darkpool_bias": 0.03,
                }
            }
        },
        trade_id=None,
    )
    assert any(k.startswith("mlf_entry_uw") and "flow" in k for k in row), row.keys()
    vals = []
    for k, v in row.items():
        if "flow_strength" not in k.lower():
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(fv):
            vals.append(fv)
    assert vals and max(vals) >= 0.9, row


def test_attach_shadow_telemetry_sets_shadow_uw_density(monkeypatch, tmp_path):
    from telemetry import shadow_evaluator

    monkeypatch.setattr(shadow_evaluator, "_SHADOW_EXECUTIONS_PATH", tmp_path / "shadow_executions.jsonl")
    monkeypatch.setattr(shadow_evaluator, "shadow_chop_block_now", lambda: False)
    monkeypatch.setattr(
        shadow_evaluator,
        "build_vanguard_feature_map",
        lambda **_k: {"mlf_scoreflow_total_score": 1.0, "uw_flow_strength": 0.4},
    )
    monkeypatch.setattr(shadow_evaluator, "_load_booster_and_meta", lambda: (None, None, "missing"))

    rec: dict = {}
    shadow_evaluator.attach_shadow_telemetry(
        rec,
        symbol="SPY",
        side="long",
        feature_snapshot={},
        comps={},
        cluster={},
        engine=None,
    )
    assert "shadow_uw_density" in rec
    assert rec["shadow_uw_finite_count"] >= 1
