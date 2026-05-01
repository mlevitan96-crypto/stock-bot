from __future__ import annotations

import json

import pytest

from src.telemetry.post_epoch_milestone_tracker import strict_integrity_verdict_last_n


def _good_snap() -> dict:
    return {
        "net_premium": 1000.0,
        "ofi_l1_roll_60s_sum": 10.0,
        "ofi_l1_roll_300s_sum": 5000.0,
        "sip_feed": "sip",
    }


def test_integrity_green(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    runp = tmp_path / "run.jsonl"
    monkeypatch.setenv("RUN_JSONL_PATH", str(runp))
    lines = []
    for i in range(10):
        rec = {
            "event_type": "exit_decision_made",
            "trade_id": f"open_X_{i}",
            "feature_snapshot_at_exit": _good_snap(),
        }
        lines.append(json.dumps(rec))
    runp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    v, fails = strict_integrity_verdict_last_n(n=10)
    assert v == "GREEN"
    assert fails == []


def test_integrity_red_missing_ofi(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    runp = tmp_path / "run.jsonl"
    monkeypatch.setenv("RUN_JSONL_PATH", str(runp))
    bad = dict(_good_snap())
    del bad["ofi_l1_roll_60s_sum"]
    lines = [json.dumps({"event_type": "exit_decision_made", "trade_id": f"t{i}", "feature_snapshot_at_exit": bad}) for i in range(10)]
    runp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    v, fails = strict_integrity_verdict_last_n(n=10)
    assert v == "RED"
    assert any("ofi" in x for x in fails)
