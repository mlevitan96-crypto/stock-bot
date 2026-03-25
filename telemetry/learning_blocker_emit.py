"""Append-only learning / completeness signals (no execution impact)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def emit_learning_blocker(reason: str, symbol: str = "", **kwargs: Any) -> None:
    """Emit learning_blocker to logs/run.jsonl. Never raises."""
    try:
        root = Path(__file__).resolve().parents[1]
        path = root / "logs" / "run.jsonl"
        rec: Dict[str, Any] = {
            "event_type": "learning_blocker",
            "reason": str(reason),
            "symbol": str(symbol).upper() if symbol else "",
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        for k, v in kwargs.items():
            if v is not None:
                rec[k] = v
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        pass
