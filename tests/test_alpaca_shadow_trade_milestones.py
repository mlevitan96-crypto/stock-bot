"""Canonical trade milestone Telegram — persisted state, no double-fire."""
from __future__ import annotations

import json
from pathlib import Path


def test_milestone_600_fires_once_and_persists(tmp_path: Path, monkeypatch) -> None:
    sent: list[tuple[str, str]] = []

    def fake_send(text: str, log_path=None, script_name: str = "governance") -> bool:
        sent.append((script_name, text))
        return True

    n_holder = {"n": 599}

    def fake_count(root, floor_epoch=None):
        return {"total_trades_post_era": n_holder["n"]}

    monkeypatch.setattr("scripts.alpaca_telegram.send_governance_telegram", fake_send)
    monkeypatch.setattr(
        "src.governance.canonical_trade_count.compute_canonical_trade_count",
        fake_count,
    )

    from telemetry.alpaca_shadow_trade_milestones import maybe_notify_canonical_trade_milestones

    maybe_notify_canonical_trade_milestones(tmp_path)
    assert sent == []

    n_holder["n"] = 600
    maybe_notify_canonical_trade_milestones(tmp_path)
    assert len(sent) == 1
    assert sent[0][0] == "alpaca_shadow_milestone_600"
    assert "600" in sent[0][1]

    sent.clear()
    maybe_notify_canonical_trade_milestones(tmp_path)
    assert sent == []

    st_path = tmp_path / "state" / "alpaca_shadow_trade_milestones.json"
    assert st_path.is_file()
    data = json.loads(st_path.read_text(encoding="utf-8"))
    assert data.get("fired", {}).get("600") is True
    assert data.get("last_total") == 600


def test_milestone_catch_up_all_three(tmp_path: Path, monkeypatch) -> None:
    sent: list[str] = []

    def fake_send(text: str, log_path=None, script_name: str = "governance") -> bool:
        sent.append(script_name)
        return True

    monkeypatch.setattr("scripts.alpaca_telegram.send_governance_telegram", fake_send)
    monkeypatch.setattr(
        "src.governance.canonical_trade_count.compute_canonical_trade_count",
        lambda root, floor_epoch=None: {"total_trades_post_era": 1000},
    )
    from telemetry.alpaca_shadow_trade_milestones import maybe_notify_canonical_trade_milestones

    maybe_notify_canonical_trade_milestones(tmp_path)
    assert set(sent) == {
        "alpaca_shadow_milestone_600",
        "alpaca_shadow_milestone_750",
        "alpaca_shadow_milestone_1000",
    }


def test_milestone_retry_if_telegram_fails(tmp_path: Path, monkeypatch) -> None:
    calls = {"i": 0}

    def flaky_send(text: str, log_path=None, script_name: str = "governance") -> bool:
        calls["i"] += 1
        return calls["i"] >= 2

    monkeypatch.setattr("scripts.alpaca_telegram.send_governance_telegram", flaky_send)
    monkeypatch.setattr(
        "src.governance.canonical_trade_count.compute_canonical_trade_count",
        lambda root, floor_epoch=None: {"total_trades_post_era": 600},
    )
    from telemetry.alpaca_shadow_trade_milestones import maybe_notify_canonical_trade_milestones

    maybe_notify_canonical_trade_milestones(tmp_path)
    st_path = tmp_path / "state" / "alpaca_shadow_trade_milestones.json"
    data = json.loads(st_path.read_text(encoding="utf-8"))
    assert data.get("fired", {}).get("600") is not True

    maybe_notify_canonical_trade_milestones(tmp_path)
    data2 = json.loads(st_path.read_text(encoding="utf-8"))
    assert data2.get("fired", {}).get("600") is True
