"""
Exit decision trace — append-only, per-open-position samples for exit learning.
Runtime-safe: buffered writes, fail-open, configurable sample interval and retention.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

# Path per spec: reports/state/exit_decision_trace.jsonl (repo-root relative when running from cwd)
TRACE_PATH = Path("reports/state/exit_decision_trace.jsonl")
SAMPLE_INTERVAL_SEC = int(os.environ.get("EXIT_TRACE_SAMPLE_INTERVAL_SEC", "60"))
RETENTION_DAYS = int(os.environ.get("EXIT_TRACE_RETENTION_DAYS", "7"))
SCHEMA_VERSION = 1

_lock = threading.Lock()
_last_sample: Dict[str, float] = {}  # trade_id -> last sample ts
_buffer: list = []
_buffer_max = 50


def _should_sample(trade_id: str) -> bool:
    now = time.time()
    with _lock:
        last = _last_sample.get(trade_id, 0)
        if now - last >= SAMPLE_INTERVAL_SEC:
            _last_sample[trade_id] = now
            return True
    return False


def _prune_old(path: Path) -> None:
    try:
        if not path.exists():
            return
        cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
        lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        kept = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ts = rec.get("ts") or rec.get("timestamp") or ""
                if ts and ts >= cutoff:
                    kept.append(line)
            except Exception:
                kept.append(line)
        if len(kept) < len(lines):
            path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    except Exception:
        pass


def _flush_buffer(path: Path) -> None:
    global _buffer
    with _lock:
        to_write = _buffer
        _buffer = []
    if not to_write:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            for line in to_write:
                f.write(line + "\n")
        if len(to_write) >= 20:
            _prune_old(path)
    except Exception:
        pass


def append_exit_decision_trace(
    *,
    trade_id: str,
    symbol: str,
    side: str,
    unrealized_pnl: float,
    price: float,
    hold_minutes: float,
    composite_score: float,
    signal_decay: float,
    exit_eligible: bool,
    exit_conditions: Dict[str, bool],
    signals: Dict[str, Any],
    path: Optional[Path] = None,
) -> None:
    """
    Append one trace record. Non-blocking, buffered, fail-open.
    Call from evaluate_exits BEFORE exit logic fires; sampling is per trade_id every N seconds.
    """
    if not trade_id:
        return
    if not _should_sample(trade_id):
        return
    ts = datetime.now(timezone.utc).isoformat()
    rec = {
        "ts": ts,
        "trade_id": trade_id,
        "symbol": str(symbol).upper(),
        "side": "long" if str(side).lower() in ("long", "buy", "bullish") else "short",
        "unrealized_pnl": round(float(unrealized_pnl), 4),
        "price": round(float(price), 4),
        "hold_minutes": round(float(hold_minutes), 4),
        "composite_score": round(float(composite_score), 4),
        "signal_decay": round(float(signal_decay), 4),
        "exit_eligible": bool(exit_eligible),
        "exit_conditions": {k: bool(v) for k, v in (exit_conditions or {}).items()},
        "signals": signals if isinstance(signals, dict) else {},
        "schema_version": SCHEMA_VERSION,
    }
    line = json.dumps(rec, default=str)
    p = path or TRACE_PATH
    with _lock:
        _buffer.append(line)
        if len(_buffer) >= 10:
            to_flush = _buffer[:]
            _buffer.clear()
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                with p.open("a", encoding="utf-8") as f:
                    for l in to_flush:
                        f.write(l + "\n")
                if len(to_flush) >= 20:
                    _prune_old(p)
            except Exception:
                _buffer[:0] = to_flush


def flush_exit_decision_trace(path: Optional[Path] = None) -> None:
    """Flush any buffered lines. Call at end of cycle if desired."""
    _flush_buffer(path or TRACE_PATH)
