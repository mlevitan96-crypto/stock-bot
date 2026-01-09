#!/usr/bin/env python3
"""
Signal History Storage Module
Maintains a high-speed buffer of the last 50 signal processing events for dashboard rendering.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
from collections import deque

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
        
        # Add timestamp if not present
        if "timestamp" not in signal_data:
            signal_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Append to file
        with SIGNAL_HISTORY_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(signal_data) + "\n")
        
        # Maintain buffer size: Read all, keep last MAX_SIGNALS
        if SIGNAL_HISTORY_FILE.exists():
            try:
                with SIGNAL_HISTORY_FILE.open("r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                # Keep only last MAX_SIGNALS lines
                if len(lines) > MAX_SIGNALS:
                    with SIGNAL_HISTORY_FILE.open("w", encoding="utf-8") as f:
                        f.writelines(lines[-MAX_SIGNALS:])
            except Exception:
                pass  # If buffer maintenance fails, continue anyway
        
    except Exception as e:
        # Fail silently - don't break trading if history logging fails
        pass

def get_signal_history(limit: int = MAX_SIGNALS) -> List[Dict[str, Any]]:
    """
    Read the last N signals from history.
    
    Args:
        limit: Maximum number of signals to return (default: MAX_SIGNALS)
    
    Returns:
        List of signal dictionaries, most recent first
    """
    if not SIGNAL_HISTORY_FILE.exists():
        return []
    
    try:
        signals = []
        with SIGNAL_HISTORY_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        signal = json.loads(line)
                        signals.append(signal)
                    except json.JSONDecodeError:
                        continue
        
        # Return most recent first, limited to requested count
        return list(reversed(signals[-limit:]))
    
    except Exception as e:
        return []

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
