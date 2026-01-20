#!/usr/bin/env python3
"""
Shadow A/B Telemetry (Structural Upgrade)
========================================

Append-only JSONL stream for shadow trading comparisons:
- logs/shadow.jsonl (see config.registry.LogFiles.SHADOW)

Contract:
- Never raise; never block trading.
- Also emits system_events (subsystem="shadow") when requested by caller.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from config.registry import LogFiles
except Exception:  # pragma: no cover
    LogFiles = None  # type: ignore

try:
    from utils.system_events import log_system_event
except Exception:  # pragma: no cover
    def log_system_event(*args, **kwargs):  # type: ignore
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_shadow_event(event_type: str, *, symbol: Optional[str] = None, **fields: Any) -> None:
    """
    Append a shadow A/B event to logs/shadow.jsonl.
    """
    try:
        rec: Dict[str, Any] = {
            "ts": _now_iso(),
            "_ts": int(time.time()),
            "event_type": str(event_type),
        }
        if symbol:
            rec["symbol"] = str(symbol)
        rec.update(fields)

        if LogFiles is None or not hasattr(LogFiles, "SHADOW"):
            return
        path = LogFiles.SHADOW  # type: ignore[attr-defined]
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
    except Exception:
        return None


def log_shadow_divergence(
    *,
    symbol: str,
    v1_score: float,
    v2_score: float,
    v1_pass: bool,
    v2_pass: bool,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Convenience logger for v1 vs v2 divergence events.
    """
    try:
        det = details or {}
        log_shadow_event(
            "divergence",
            symbol=symbol,
            v1_score=float(v1_score),
            v2_score=float(v2_score),
            v1_pass=bool(v1_pass),
            v2_pass=bool(v2_pass),
            details=det,
        )
        # Also emit a compact system event for dashboard visibility.
        try:
            log_system_event(
                subsystem="shadow",
                event_type="divergence",
                severity="INFO",
                symbol=symbol,
                details={
                    "v1_score": float(v1_score),
                    "v2_score": float(v2_score),
                    "v1_pass": bool(v1_pass),
                    "v2_pass": bool(v2_pass),
                    **det,
                },
            )
        except Exception:
            pass
    except Exception:
        return None

