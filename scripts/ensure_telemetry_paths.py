#!/usr/bin/env python3
"""
Phase 1 — Telemetry surface bootstrap.
Ensures all required log/state paths exist (creates dirs and empty files if missing).
Run on droplet or locally; no live behavior, no writes to existing content.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Paths to verify (relative to repo root)
TELEMETRY_PATHS = [
    "logs/attribution.jsonl",
    "logs/exit_attribution.jsonl",
    "logs/master_trade_log.jsonl",
    "state/blocked_trades.jsonl",
    "logs/run.jsonl",
    "logs/score_snapshot.jsonl",
    "logs/signal_score_breakdown.jsonl",
    "logs/expectancy_gate_truth.jsonl",
    "logs/exit_truth.jsonl",
    "state/daily_universe_v2.json",
    "state/signal_weights.json",
    "logs/signal_history.jsonl",
    "logs/exit_signal_snapshot.jsonl",
    "logs/exit_event.jsonl",
]


def main() -> None:
    created: list[str] = []
    for rel in TELEMETRY_PATHS:
        p = REPO / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.touch()
            created.append(rel)
    if created:
        print("Created (empty):", " ".join(created))
    else:
        print("All telemetry paths present.")
    return None


if __name__ == "__main__":
    main()
