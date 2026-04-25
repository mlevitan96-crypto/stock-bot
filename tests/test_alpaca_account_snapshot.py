"""Smoke test for run_alpaca_account_snapshot (no broker keys required)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_account_snapshot_wash_watchlist(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir(parents=True)
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=5)).isoformat()
    rows = [
        {"symbol": "LOSS1", "exit_ts": old, "realized_pnl_usd": -2.5},
        {"symbol": "WIN1", "exit_ts": old, "realized_pnl_usd": 1.0},
        {"symbol": "LOSS1", "exit_ts": now.isoformat(), "realized_pnl_usd": -0.5},
    ]
    (logs / "exit_attribution.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )

    cmd = [
        sys.executable,
        str(REPO / "scripts" / "run_alpaca_account_snapshot.py"),
        "--root",
        str(tmp_path),
        "--exit-log",
        str(logs / "exit_attribution.jsonl"),
        "--lookback-days",
        "30",
    ]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr + r.stdout

    snap = tmp_path / "state" / "alpaca_account_snapshot.json"
    data = json.loads(snap.read_text(encoding="utf-8"))
    assert data.get("wash_risk_watchlist_count") == 1
    wl = data.get("wash_risk_watchlist") or []
    assert len(wl) == 1
    assert wl[0]["symbol"] == "LOSS1"
    assert wl[0]["loss_exit_count_in_window"] == 2
