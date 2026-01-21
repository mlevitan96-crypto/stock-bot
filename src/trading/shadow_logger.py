#!/usr/bin/env python3
"""
Shadow trade logger (v2, shadow-only)
====================================

Contract:
- Append-only log file: logs/shadow_trades.jsonl
- Never raise; never block live trading.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


OUT = Path("logs/shadow_trades.jsonl")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_shadow_trade(rec: Dict[str, Any]) -> None:
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        payload = {"ts": _now_iso(), "_ts": int(time.time())}
        payload.update(rec or {})
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        return

