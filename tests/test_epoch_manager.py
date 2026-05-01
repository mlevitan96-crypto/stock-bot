from __future__ import annotations

import json

import pytest


def test_anchor_and_increment(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    ep = tmp_path / "epoch_state.json"
    monkeypatch.setenv("EPOCH_STATE_JSON_PATH", str(ep))
    from src.telemetry import epoch_manager as em

    st = em.anchor_new_epoch(epoch_label="t1", epoch_start_ts=1_700_000_000.0)
    assert st["epoch_start_ts"] == 1_700_000_000.0
    assert st["post_epoch_terminal_exit_count"] == 0
    n, hit = em.increment_post_epoch_exit_and_check_milestone()
    assert n == 1
    assert hit is None
    for _ in range(8):
        em.increment_post_epoch_exit_and_check_milestone()
    n10, hit10 = em.increment_post_epoch_exit_and_check_milestone()
    assert n10 == 10
    assert hit10 == 10
    body = json.loads(ep.read_text(encoding="utf-8"))
    assert 10 in (body.get("fired_milestones") or [])
    n11, hit11 = em.increment_post_epoch_exit_and_check_milestone()
    assert n11 == 11
    assert hit11 is None


def test_increment_skipped_when_epoch_unset(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    ep = tmp_path / "epoch_empty.json"
    monkeypatch.setenv("EPOCH_STATE_JSON_PATH", str(ep))
    from src.telemetry import epoch_manager as em

    ep.write_text(json.dumps({"epoch_start_ts": 0.0, "post_epoch_terminal_exit_count": 0}), encoding="utf-8")
    n, hit = em.increment_post_epoch_exit_and_check_milestone()
    assert n == 0
    assert hit is None
