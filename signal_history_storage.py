#!/usr/bin/env python3
"""
Signal History Storage Module
Maintains a high-speed buffer of the last 50 signal processing events for dashboard rendering.
"""

import json
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

SIGNAL_HISTORY_FILE = Path("state/signal_history.jsonl")
MAX_SIGNALS = 50  # Keep last 50 signals

def append_signal_history(signal_data: Dict[str, Any]):
    """
    Append a signal processing event to the history buffer.
    
    Args:
        signal_data: Dict containing:
            - symbol: str
            - direction: str (bullish/bearish)
            - raw_score: float (score before whale boost)
            - whale_boost: float (whale conviction boost applied, typically +0.5)
            - final_score: float (raw_score + whale_boost)
            - atr_multiplier: float (ATR multiplier used, if applicable)
            - momentum_pct: float (actual price change %)
            - momentum_required_pct: float (required threshold %)
            - decision: str (Ordered/Blocked:reason/Rejected:reason)
            - timestamp: str (ISO format)
            - metadata: dict (additional context)
    """
    try:
        # Ensure state directory exists
        SIGNAL_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        if "timestamp" not in signal_data:
            signal_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        safe = _sanitize_for_json(signal_data)
        with SIGNAL_HISTORY_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(safe, allow_nan=False) + "\n")
            f.flush()
        if SIGNAL_HISTORY_FILE.exists():
            try:
                with SIGNAL_HISTORY_FILE.open("r", encoding="utf-8") as f:
                    lines = f.readlines()
                if len(lines) > MAX_SIGNALS:
                    tmp = SIGNAL_HISTORY_FILE.with_suffix(".jsonl.tmp")
                    tmp.write_text("".join(lines[-MAX_SIGNALS:]), encoding="utf-8")
                    tmp.replace(SIGNAL_HISTORY_FILE)
            except Exception:
                pass
    except Exception:
        pass


def _sanitize_for_json(obj: Any) -> Any:
    """Replace NaN/Inf so JSON serialization never fails."""
    if isinstance(obj, float):
        if math.isfinite(obj):
            return obj
        return None
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_for_json(x) for x in obj]
    return obj

def _read_signal_history(limit: int) -> Tuple[List[Dict[str, Any]], int, str]:
    """Read up to limit signals; return (signals, malformed_line_count, last_malformed_ts)."""
    if not SIGNAL_HISTORY_FILE.exists():
        return [], 0, ""
    signals = []
    malformed = 0
    last_malformed_ts = ""
    try:
        with SIGNAL_HISTORY_FILE.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    signals.append(_sanitize_for_json(obj))
                except json.JSONDecodeError:
                    malformed += 1
                    last_malformed_ts = datetime.now(timezone.utc).isoformat()
        return list(reversed(signals[-limit:])), malformed, last_malformed_ts
    except Exception:
        return [], malformed, last_malformed_ts


def get_signal_history(limit: int = MAX_SIGNALS) -> List[Dict[str, Any]]:
    """Read the last N signals, most recent first."""
    signals, _, _ = _read_signal_history(limit)
    return signals


def get_signal_history_with_meta(limit: int = MAX_SIGNALS) -> Tuple[List[Dict[str, Any]], int, str]:
    """Read the last N signals and corruption counters for dashboard."""
    return _read_signal_history(limit)

def get_last_signal_timestamp() -> str:
    """
    Get the timestamp of the most recent signal.
    
    Returns:
        ISO timestamp string, or empty string if no signals
    """
    history = get_signal_history(limit=1)
    if history:
        return history[0].get("timestamp", "")
    return ""
