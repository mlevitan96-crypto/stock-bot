"""
Cross-process Tier-1 wake signal (UW WebSocket ingest -> trading worker).

``uw_flow_daemon`` runs in a separate process from ``main.py``, so a
``threading.Event`` cannot bridge them. The daemon atomically replaces
``state/tier1_wake.json``; ``Watchdog`` polls mtime in short slices while sleeping.

Override path for tests: ``TIER1_WAKE_JSON_PATH``.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

_TIER1_WAKE_POLL_SEC = float(os.environ.get("TIER1_WAKE_POLL_SEC", "0.25") or 0.25)
if _TIER1_WAKE_POLL_SEC < 0.05:
    _TIER1_WAKE_POLL_SEC = 0.05
if _TIER1_WAKE_POLL_SEC > 5.0:
    _TIER1_WAKE_POLL_SEC = 5.0


def tier1_wake_poll_seconds() -> float:
    return _TIER1_WAKE_POLL_SEC


def _wake_path() -> Path:
    raw = os.environ.get("TIER1_WAKE_JSON_PATH", "").strip()
    if raw:
        return Path(raw)
    from config.registry import StateFiles

    return StateFiles.TIER1_WAKE_SIGNAL


def tier1_wake_mtime() -> float:
    p = _wake_path()
    try:
        return float(p.stat().st_mtime)
    except OSError:
        return 0.0


def signal_tier1_wake(source: str, symbol: Optional[str] = None, **extra: Any) -> None:
    """Best-effort atomic touch so the trading worker can interrupt its sleep."""
    if str(os.environ.get("TIER1_WAKE_BRIDGE_ENABLED", "1")).strip().lower() in ("0", "false", "no", "off"):
        return
    p = _wake_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        return
    payload: Dict[str, Any] = {
        "ts": time.time(),
        "source": str(source or "")[:80],
        "symbol": str(symbol or "").upper()[:16],
    }
    for k, v in extra.items():
        if v is not None and k not in payload:
            payload[str(k)[:64]] = v
    tmp = p.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(payload, default=str), encoding="utf-8")
        os.replace(str(tmp), str(p))
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink(missing_ok=True)  # type: ignore[arg-type]
        except Exception:
            pass
