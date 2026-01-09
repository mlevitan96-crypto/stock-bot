#!/usr/bin/env python3
"""
Persistence Tracker
Tracks ticker appearance frequency in signal history.
If ticker appears > 5 times in 15 minutes, marks as Whale_Motif=True.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, deque

from signal_history_storage import get_signal_history, SIGNAL_HISTORY_FILE

WINDOW_MINUTES = 15  # Rolling 15-minute window
MIN_APPEARANCES = 5  # Minimum appearances to trigger persistence
PERSISTENCE_BOOST = 0.5  # Boost applied when persistence detected (same as whale boost)

class PersistenceTracker:
    """Tracks ticker appearance frequency in signal history."""
    
    def __init__(self):
        self.appearance_windows: Dict[str, deque] = defaultdict(lambda: deque())  # symbol -> deque of timestamps
        self._load_from_history()
    
    def _load_from_history(self):
        """Load recent signal history to initialize appearance windows."""
        try:
            # Get last 50 signals (same as signal_history limit)
            signals = get_signal_history(limit=50)
            current_time = time.time()
            window_sec = WINDOW_MINUTES * 60
            
            for signal in signals:
                symbol = signal.get("symbol", "")
                if not symbol:
                    continue
                
                # Parse timestamp
                timestamp_str = signal.get("timestamp", "")
                if timestamp_str:
                    try:
                        # Parse ISO timestamp
                        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        timestamp = dt.timestamp()
                    except:
                        # Fallback: use current time
                        timestamp = current_time
                else:
                    timestamp = current_time
                
                # Only keep events within window
                if current_time - timestamp < window_sec:
                    self.appearance_windows[symbol].append(timestamp)
            
            # Clean old events
            self._clean_old_events()
        except Exception:
            pass  # Start fresh on error
    
    def _clean_old_events(self, current_time: Optional[float] = None):
        """Remove events outside rolling window."""
        if current_time is None:
            current_time = time.time()
        
        window_sec = WINDOW_MINUTES * 60
        cutoff_time = current_time - window_sec
        
        for symbol in list(self.appearance_windows.keys()):
            # Remove old timestamps
            while self.appearance_windows[symbol] and self.appearance_windows[symbol][0] < cutoff_time:
                self.appearance_windows[symbol].popleft()
            
            # Remove empty entries
            if len(self.appearance_windows[symbol]) == 0:
                del self.appearance_windows[symbol]
    
    def record_signal(self, symbol: str, timestamp: Optional[float] = None):
        """
        Record a signal appearance for a symbol.
        
        Args:
            symbol: Ticker symbol
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()
        
        if not symbol:
            return
        
        # Add to appearance window
        self.appearance_windows[symbol].append(timestamp)
        
        # Clean old events
        self._clean_old_events(timestamp)
    
    def get_appearance_count(self, symbol: str, current_time: Optional[float] = None) -> int:
        """
        Get count of appearances for symbol within rolling window.
        
        Args:
            symbol: Ticker symbol
            current_time: Current timestamp (defaults to now)
        
        Returns:
            Count of appearances
        """
        if current_time is None:
            current_time = time.time()
        
        self._clean_old_events(current_time)
        return len(self.appearance_windows.get(symbol, deque()))
    
    def check_persistence(self, symbol: str, current_time: Optional[float] = None) -> Dict[str, any]:
        """
        Check if persistence is detected for a symbol.
        
        Args:
            symbol: Ticker symbol
            current_time: Current timestamp (defaults to now)
        
        Returns:
            Dict with:
                - active: bool (True if persistence detected)
                - count: int (appearance count)
                - whale_motif: bool (True if count >= MIN_APPEARANCES)
                - boost: float (boost to apply, 0.5 if active else 0.0)
        """
        if current_time is None:
            current_time = time.time()
        
        if not symbol:
            return {
                "active": False,
                "count": 0,
                "whale_motif": False,
                "boost": 0.0
            }
        
        count = self.get_appearance_count(symbol, current_time)
        active = count >= MIN_APPEARANCES
        
        return {
            "active": active,
            "count": count,
            "whale_motif": active,  # Whale motif = persistence detected
            "boost": PERSISTENCE_BOOST if active else 0.0
        }

# Global singleton instance
_tracker_instance: Optional[PersistenceTracker] = None

def get_persistence_tracker() -> PersistenceTracker:
    """Get global persistence tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = PersistenceTracker()
    return _tracker_instance
