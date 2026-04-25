"""Offline smoke for displacement_counterfactual_lab (subprocess, no live API)."""

from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_displacement_lab_offline_smoke(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir(parents=True)
    data = tmp_path / "data"
    data.mkdir()

    disp = {
        "ts": "2024-06-05T15:00:00+00:00",
        "msg": "no_candidates_found",
        "new_signal_score": 3.1,
        "total_positions": 5,
        "reasons": {"too_young": 2, "in_cooldown": 1},
        "position_details": [
            {"symbol": "AAA", "fail_reason": "too_young", "age_hours": 1, "pnl_pct": 0.1},
            {"symbol": "BBB", "fail_reason": "in_cooldown", "age_hours": 10, "pnl_pct": 0.0},
            {"symbol": "ZZZ", "fail_reason": "score_advantage_insufficient"},
        ],
    }
    (logs / "displacement.jsonl").write_text(json.dumps(disp) + "\n", encoding="utf-8")

    intent = {
        "ts": "2024-06-05T15:00:05+00:00",
        "event_type": "trade_intent",
        "symbol": "CAND",
        "side": "buy",
        "score": 3.1,
        "decision_outcome": "blocked",
        "blocked_reason": "max_positions_reached",
        "feature_snapshot": {"close": 50.0},
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
    for sym, series in (
        (
            "CAND",
            [
                ("2024-06-03T00:00:00Z", 48.0),
                ("2024-06-04T00:00:00Z", 49.0),
                ("2024-06-05T00:00:00Z", 50.0),
                ("2024-06-06T00:00:00Z", 55.0),
                ("2024-06-07T00:00:00Z", 56.0),
            ],
        ),
        (
            "AAA",
            [
                ("2024-06-03T00:00:00Z", 100.0),
                ("2024-06-04T00:00:00Z", 100.0),
                ("2024-06-05T00:00:00Z", 100.0),
                ("2024-06-06T00:00:00Z", 101.0),
                ("2024-06-07T00:00:00Z", 102.0),
            ],
        ),
        (
            "BBB",
            [
                ("2024-06-03T00:00:00Z", 10.0),
                ("2024-06-04T00:00:00Z", 10.0),
                ("2024-06-05T00:00:00Z", 10.0),
                ("2024-06-06T00:00:00Z", 10.5),
                ("2024-06-07T00:00:00Z", 11.0),
            ],
        ),
    ):
        for ts, c in series:
            conn.execute(
                """
                INSERT INTO research_bars (symbol, timeframe, ts_utc, o, h, l, c, v, fetched_at)
                VALUES (?, '1Day', ?, ?, ?, ?, ?, 1, ?)
                """,
                (sym, ts, c, c, c, c, fetched),
            )
    conn.commit()
    conn.close()

    cmd = [
        sys.executable,
        str(REPO / "scripts" / "research" / "displacement_counterfactual_lab.py"),
        "--root",
        str(tmp_path),
        "--skip-api",
        "--bars-db",
        str(db),
        "--join-window-sec",
        "30",
    ]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr + r.stdout

    outs = list((tmp_path / "reports" / "Gemini").glob("displacement_cost_*.csv"))
    assert outs
    with outs[-1].open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    syms = {row["incumbent_symbol"] for row in rows}
    assert syms == {"AAA", "BBB"}
