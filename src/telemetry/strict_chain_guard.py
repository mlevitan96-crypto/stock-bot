"""
Optional observability hook before economic close rows are persisted.

Set ``ALPACA_STRICT_CHAIN_GUARD=1`` to append one JSON line per close to
``logs/alpaca_strict_chain_guard.jsonl``. **Does not block** closes (fail-open).
Future: extend to preflight scan of run.jsonl when performance budget allows.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def record_econ_close_chain_checkpoint(rec: Dict[str, Any]) -> None:
    if os.environ.get("ALPACA_STRICT_CHAIN_GUARD", "").lower() not in ("1", "true", "yes"):
        return
    try:
        p = Path(os.environ.get("STRICT_CHAIN_GUARD_LOG_PATH", "logs/alpaca_strict_chain_guard.jsonl"))
        p.parent.mkdir(parents=True, exist_ok=True)
        line = {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "event": "econ_close_checkpoint",
            "trade_id": rec.get("trade_id"),
            "symbol": rec.get("symbol"),
            "trade_key": rec.get("trade_key"),
            "canonical_trade_id": rec.get("canonical_trade_id"),
            "note": "fail_open; does not verify entered/exit_intent legs",
        }
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, default=str) + "\n")
    except Exception:
        return
