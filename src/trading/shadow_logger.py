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
        now = _now_iso()
        payload: Dict[str, Any] = {"timestamp": now, "ts": now, "_ts": int(time.time())}
        payload.update(rec or {})
        # Guarantee canonical timestamp field for downstream integrity tooling.
        if "timestamp" not in payload:
            payload["timestamp"] = payload.get("ts", now)
        if "ts" not in payload:
            payload["ts"] = payload.get("timestamp", now)
        # Safe placeholders (observability only; no trading logic impact)
        payload.setdefault("entry_price", None)
        payload.setdefault("exit_price", None)
        payload.setdefault("pnl", None)
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, default=str) + "\n")
    except Exception:
        return

