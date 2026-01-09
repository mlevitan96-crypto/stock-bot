#!/usr/bin/env python3
"""
Sector Tide Tracker
Tracks rolling 15-minute window of symbols per sector.
Applies +0.3 Sector_Tide boost when Sector_Count >= 3.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Optional
from collections import defaultdict, deque

# Import sector mapping from risk_management
try:
    from risk_management import get_sector, SECTOR_MAP
except ImportError:
    # Fallback sector mapping if risk_management not available
    SECTOR_MAP = {
        "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology",
        "GOOG": "Technology", "META": "Technology", "NVDA": "Technology",
        "AMD": "Technology", "INTC": "Technology", "NFLX": "Technology",
        "TSLA": "Technology",
        "JPM": "Financial", "BAC": "Financial", "GS": "Financial",
        "SPY": "ETF", "QQQ": "ETF", "IWM": "ETF", "DIA": "ETF",
    }
    
    def get_sector(symbol: str) -> str:
        return SECTOR_MAP.get(symbol, "Unknown")

STATE_FILE = Path("state/sector_tide_state.json")
WINDOW_MINUTES = 15  # Rolling 15-minute window
MIN_SECTOR_COUNT = 3  # Minimum symbols in sector to trigger tide
SECTOR_TIDE_BOOST = 0.3  # Boost applied when sector tide detected

class SectorTideTracker:
    """Tracks sector-wide activity in rolling windows."""
    
    def __init__(self):
        self.sector_windows: Dict[str, deque] = defaultdict(lambda: deque())  # sector -> deque of (timestamp, symbol)
        self._load_state()
    
    def _load_state(self):
        """Load state from disk if available."""
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text())
                current_time = time.time()
                window_sec = WINDOW_MINUTES * 60
                
                # Reconstruct deques from saved data
                for sector, events in data.get("sector_windows", {}).items():
                    for event in events:
                        ts = event.get("timestamp", 0)
                        symbol = event.get("symbol", "")
                        # Only keep events within window
                        if current_time - ts < window_sec:
                            self.sector_windows[sector].append((ts, symbol))
        except Exception:
            pass  # Start fresh on error
    
    def _save_state(self):
        """Save state to disk."""
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "sector_windows": {
                    sector: [
                        {"timestamp": ts, "symbol": symbol}
                        for ts, symbol in list(window)
                    ]
                    for sector, window in self.sector_windows.items()
                }
            }
            STATE_FILE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass  # Fail silently
    
    def record_signal(self, symbol: str, timestamp: Optional[float] = None):
        """
        Record a signal for a symbol.
        
        Args:
            symbol: Ticker symbol
            timestamp: Unix timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = time.time()
        
        sector = get_sector(symbol)
        if sector == "Unknown":
            return  # Don't track unknown sectors
        
        # Add to sector window
        self.sector_windows[sector].append((timestamp, symbol))
        
        # Clean old events (outside 15-minute window)
        window_sec = WINDOW_MINUTES * 60
        cutoff_time = timestamp - window_sec
        
        # Remove events older than window
        while self.sector_windows[sector] and self.sector_windows[sector][0][0] < cutoff_time:
            self.sector_windows[sector].popleft()
        
        # Save state periodically (every 10 signals)
        if len(self.sector_windows[sector]) % 10 == 0:
            self._save_state()
    
    def get_sector_count(self, sector: str, current_time: Optional[float] = None) -> int:
        """
        Get count of unique symbols in sector within rolling window.
        
        Args:
            sector: Sector name
            current_time: Current timestamp (defaults to now)
        
        Returns:
            Count of unique symbols
        """
        if current_time is None:
            current_time = time.time()
        
        window_sec = WINDOW_MINUTES * 60
        cutoff_time = current_time - window_sec
        
        # Get unique symbols in window
        symbols_in_window = set()
        for ts, symbol in self.sector_windows[sector]:
            if ts >= cutoff_time:
                symbols_in_window.add(symbol)
        
        return len(symbols_in_window)
    
    def check_sector_tide(self, symbol: str, current_time: Optional[float] = None) -> Dict[str, any]:
        """
        Check if sector tide is active for a symbol.
        
        Args:
            symbol: Ticker symbol
            current_time: Current timestamp (defaults to now)
        
        Returns:
            Dict with:
                - active: bool (True if sector tide active)
                - sector: str (sector name)
                - count: int (symbol count in sector)
                - boost: float (boost to apply, 0.3 if active else 0.0)
        """
        if current_time is None:
            current_time = time.time()
        
        sector = get_sector(symbol)
        if sector == "Unknown":
            return {
                "active": False,
                "sector": sector,
                "count": 0,
                "boost": 0.0
            }
        
        count = self.get_sector_count(sector, current_time)
        active = count >= MIN_SECTOR_COUNT
        
        return {
            "active": active,
            "sector": sector,
            "count": count,
            "boost": SECTOR_TIDE_BOOST if active else 0.0
        }
    
    def get_all_active_tides(self, current_time: Optional[float] = None) -> Dict[str, int]:
        """
        Get all sectors with active tides.
        
        Args:
            current_time: Current timestamp (defaults to now)
        
        Returns:
            Dict mapping sector -> symbol count
        """
        if current_time is None:
            current_time = time.time()
        
        active_tides = {}
        for sector in self.sector_windows.keys():
            count = self.get_sector_count(sector, current_time)
            if count >= MIN_SECTOR_COUNT:
                active_tides[sector] = count
        
        return active_tides

# Global singleton instance
_tracker_instance: Optional[SectorTideTracker] = None

def get_sector_tide_tracker() -> SectorTideTracker:
    """Get global sector tide tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = SectorTideTracker()
    return _tracker_instance
