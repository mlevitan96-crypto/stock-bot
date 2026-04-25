"""Offline smoke for shadow_challenger_concordance (subprocess, no live API)."""

from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_shadow_challenger_concordance_offline_smoke(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir(parents=True)
    data = tmp_path / "data"
    data.mkdir()

    shadow_row = {
        "ts": "2024-06-05T15:30:00+00:00",
        "event_type": "SHADOW_EXECUTION",
        "model": "vanguard_challenger",
        "symbol": "SPY",
        "side": "buy",
        "entry_price": 100.0,
        "entry_price_source": "row:last_price",
        "challenger_proba": 0.9,
        "challenger_threshold": 0.5,
        "primary_decision_outcome": "blocked",
        "primary_blocked_reason": "capacity_full",
    }
    (logs / "shadow_executions.jsonl").write_text(json.dumps(shadow_row) + "\n", encoding="utf-8")

    intent = {
        "ts": "2024-06-05T15:30:02+00:00",
        "event_type": "trade_intent",
        "symbol": "SPY",
        "side": "buy",
        "score": 3.1,
        "decision_outcome": "blocked",
        "blocked_reason": "capacity_full",
        "challenger_ai_approved": True,
        "challenger_shadow_proba": 0.9,
        "decision_event_id": "dec_test",
        "feature_snapshot": {"v2_score": 3.1, "regime_label": "chop"},
    }
    (logs / "run.jsonl").write_text(json.dumps(intent) + "\n", encoding="utf-8")

    db = data / "research_bars.db"
    conn = sqlite3.connect(str(db))
    conn.execute(
        """
        CREATE TABLE research_bars (
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            ts_utc TEXT NOT NULL,
            o REAL NOT NULL,
            h REAL NOT NULL,
            l REAL NOT NULL,
            c REAL NOT NULL,
            v INTEGER NOT NULL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (symbol, timeframe, ts_utc)
        )
        """
    )
    fetched = "2024-06-10T00:00:00Z"
    days = [
        ("2024-06-03T00:00:00Z", 100.0),
        ("2024-06-04T00:00:00Z", 101.0),
        ("2024-06-05T00:00:00Z", 102.0),
        ("2024-06-06T00:00:00Z", 110.0),
        ("2024-06-07T00:00:00Z", 111.0),
        ("2024-06-10T00:00:00Z", 112.0),
    ]
    for ts, c in days:
        conn.execute(
            """
            INSERT INTO research_bars (symbol, timeframe, ts_utc, o, h, l, c, v, fetched_at)
            VALUES ('SPY', '1Day', ?, ?, ?, ?, ?, 1000000, ?)
            """,
            (ts, c, c, c, c, fetched),
        )
    conn.commit()
    conn.close()

    cmd = [
        sys.executable,
        str(REPO / "scripts" / "research" / "shadow_challenger_concordance.py"),
        "--root",
        str(tmp_path),
        "--skip-api",
        "--bars-db",
        str(db),
        "--join-window-sec",
        "10",
    ]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr + r.stdout

    outs = list((tmp_path / "reports" / "Gemini").glob("shadow_concordance_*.csv"))
    assert outs, "expected CSV output"
    with outs[-1].open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["symbol"] == "SPY"
    # Anchor bar 2024-06-05 close 102; T+1 close 110; long signed vs entry 100 -> 10%
    assert float(rows[0]["fwd_return_1d_signed"]) == pytest.approx(0.1)
    assert rows[0]["missed_profit_1d_flag"].lower() == "true"
