#!/usr/bin/env python3
"""
Master Trade Log (append-only)
=============================

Contract:
- Append-only output: logs/master_trade_log.jsonl
- Additive / non-destructive: never modifies trading, scoring, or exit logic.
- Must never raise inside execution paths.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


MASTER_TRADE_LOG = Path("logs/master_trade_log.jsonl")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_master_trade(rec: Dict[str, Any]) -> None:
    """
    Append one JSON object line to logs/master_trade_log.jsonl.
    Never raises (safe for live/shadow execution paths).
    """
    try:
        MASTER_TRADE_LOG.parent.mkdir(parents=True, exist_ok=True)
        payload: Dict[str, Any] = dict(rec or {})
        payload.setdefault("timestamp", _now_iso())
        with MASTER_TRADE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        return

