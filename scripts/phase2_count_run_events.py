#!/usr/bin/env python3
"""Count trade_intent and exit_intent in logs/run.jsonl. Prints 'ti ex'."""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
path = REPO / "logs" / "run.jsonl"
ti = ex = 0
if path.exists():
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
                e = d.get("event_type", "")
                if e == "trade_intent":
                    ti += 1
                elif e == "exit_intent":
                    ex += 1
            except Exception:
                pass
print(ti, ex)
