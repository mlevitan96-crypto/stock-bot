from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from telemetry import wash_reentry_policy


def test_wash_defer_same_ny_day(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "state"
    state.mkdir(parents=True)
    now = datetime.now(timezone.utc)
    snap = {
        "wash_risk_watchlist": [
            {
                "symbol": "LOSS",
                "last_loss_exit_ts": now.isoformat(),
                "last_realized_pnl_usd": -10.0,
                "loss_exit_count_in_window": 1,
            }
        ]
    }
    p = state / "alpaca_account_snapshot.json"
    p.write_text(json.dumps(snap), encoding="utf-8")
    monkeypatch.setattr(wash_reentry_policy, "_repo_root", lambda: tmp_path)
    act, mult = wash_reentry_policy.wash_reentry_action("LOSS", snapshot_path=p)
    assert act == "defer_session"
    assert mult == 0.0


def test_wash_half_after_prior_day(tmp_path: Path, monkeypatch) -> None:
    state = tmp_path / "state"
    state.mkdir(parents=True)
    old = datetime.now(timezone.utc) - timedelta(days=3)
    snap = {
        "wash_risk_watchlist": [
            {
                "symbol": "OLD",
                "last_loss_exit_ts": old.isoformat(),
                "last_realized_pnl_usd": -5.0,
                "loss_exit_count_in_window": 1,
            }
        ]
    }
    p = state / "alpaca_account_snapshot.json"
    p.write_text(json.dumps(snap), encoding="utf-8")
    monkeypatch.setattr(wash_reentry_policy, "_repo_root", lambda: tmp_path)
    act, mult = wash_reentry_policy.wash_reentry_action("OLD", snapshot_path=p)
    assert act == "half_size"
    assert mult == 0.5
