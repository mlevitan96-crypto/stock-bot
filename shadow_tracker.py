#!/usr/bin/env python3
"""
Shadow Trade Tracker
Tracks virtual positions for rejected signals > 2.3 to identify missed profit opportunities.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

STATE_FILE = Path("state/shadow_positions.json")
SHADOW_MIN_SCORE = 2.3  # Minimum score to create shadow position
SHADOW_DURATION_SEC = 3600  # Track for 60 minutes
SHADOW_STOP_PCT = 0.02  # 2% stop loss
SHADOW_PROFIT_PCT = 0.05  # 5% profit target

class ShadowPosition:
    """Represents a virtual position for a rejected signal."""
    
    def __init__(self, symbol: str, direction: str, entry_price: float, entry_score: float,
                 entry_time: float, stop_pct: float = SHADOW_STOP_PCT, 
                 profit_pct: float = SHADOW_PROFIT_PCT):
        self.symbol = symbol
        self.direction = direction  # "bullish" or "bearish"
        self.entry_price = entry_price
        self.entry_score = entry_score
        self.entry_time = entry_time
        self.stop_pct = stop_pct
        self.profit_pct = profit_pct
        self.max_profit_pct = 0.0
        self.max_loss_pct = 0.0
        self.current_price = entry_price
        self.last_update_time = entry_time
        self.closed = False
        self.close_reason = None
        self.close_time = None
        
        # Calculate stop and profit levels
        if direction == "bullish":
            self.stop_price = entry_price * (1 - stop_pct)
            self.profit_price = entry_price * (1 + profit_pct)
        else:  # bearish
            self.stop_price = entry_price * (1 + stop_pct)
            self.profit_price = entry_price * (1 - profit_pct)
    
    def update_price(self, current_price: float, current_time: float) -> Dict[str, Any]:
        """
        Update shadow position with current price.
        
        Returns:
            Dict with update status and P&L info
        """
        if self.closed:
            return {"closed": True, "reason": self.close_reason}
        
        self.current_price = current_price
        self.last_update_time = current_time
        
        # Calculate current P&L
        if self.direction == "bullish":
            pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        else:  # bearish
            pnl_pct = ((self.entry_price - current_price) / self.entry_price) * 100
        
        # Track max profit and max loss
        if pnl_pct > self.max_profit_pct:
            self.max_profit_pct = pnl_pct
        if pnl_pct < self.max_loss_pct:
            self.max_loss_pct = pnl_pct
        
        # Check if stop or profit hit
        if self.direction == "bullish":
            if current_price <= self.stop_price:
                self.closed = True
                self.close_reason = "stop_loss"
                self.close_time = current_time
            elif current_price >= self.profit_price:
                self.closed = True
                self.close_reason = "profit_target"
                self.close_time = current_time
        else:  # bearish
            if current_price >= self.stop_price:
                self.closed = True
                self.close_reason = "stop_loss"
                self.close_time = current_time
            elif current_price <= self.profit_price:
                self.closed = True
                self.close_reason = "profit_target"
                self.close_time = current_time
        
        # Check if duration expired
        if current_time - self.entry_time >= SHADOW_DURATION_SEC:
            self.closed = True
            self.close_reason = "duration_expired"
            self.close_time = current_time
        
        return {
            "closed": self.closed,
            "pnl_pct": pnl_pct,
            "max_profit_pct": self.max_profit_pct,
            "max_loss_pct": self.max_loss_pct,
            "close_reason": self.close_reason
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "entry_score": self.entry_score,
            "entry_time": self.entry_time,
            "current_price": self.current_price,
            "max_profit_pct": self.max_profit_pct,
            "max_loss_pct": self.max_loss_pct,
            "closed": self.closed,
            "close_reason": self.close_reason,
            "close_time": self.close_time,
            "last_update_time": self.last_update_time
        }

class ShadowTracker:
    """Tracks shadow positions for rejected signals."""
    
    def __init__(self):
        self.positions: Dict[str, ShadowPosition] = {}  # symbol -> ShadowPosition
        self._load_state()
    
    def _load_state(self):
        """Load shadow positions from disk."""
        try:
            if STATE_FILE.exists():
                data = json.loads(STATE_FILE.read_text())
                current_time = time.time()
                
                for symbol, pos_data in data.get("positions", {}).items():
                    # Only load positions that haven't expired
                    entry_time = pos_data.get("entry_time", 0)
                    if current_time - entry_time < SHADOW_DURATION_SEC:
                        pos = ShadowPosition(
                            symbol=pos_data["symbol"],
                            direction=pos_data["direction"],
                            entry_price=pos_data["entry_price"],
                            entry_score=pos_data["entry_score"],
                            entry_time=entry_time,
                            stop_pct=pos_data.get("stop_pct", SHADOW_STOP_PCT),
                            profit_pct=pos_data.get("profit_pct", SHADOW_PROFIT_PCT)
                        )
                        pos.max_profit_pct = pos_data.get("max_profit_pct", 0.0)
                        pos.max_loss_pct = pos_data.get("max_loss_pct", 0.0)
                        pos.closed = pos_data.get("closed", False)
                        pos.close_reason = pos_data.get("close_reason")
                        pos.close_time = pos_data.get("close_time")
                        pos.current_price = pos_data.get("current_price", pos.entry_price)
                        pos.last_update_time = pos_data.get("last_update_time", entry_time)
                        self.positions[symbol] = pos
        except Exception:
            pass  # Start fresh on error
    
    def _save_state(self):
        """Save shadow positions to disk."""
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "positions": {
                    symbol: pos.to_dict()
                    for symbol, pos in self.positions.items()
                }
            }
            STATE_FILE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass  # Fail silently
    
    def create_shadow_position(self, symbol: str, direction: str, entry_price: float,
                               entry_score: float, entry_time: Optional[float] = None) -> bool:
        """
        Create a shadow position for a rejected signal.
        
        Args:
            symbol: Ticker symbol
            direction: "bullish" or "bearish"
            entry_price: Entry price at rejection time
            entry_score: Score that was rejected
            entry_time: Unix timestamp (defaults to now)
        
        Returns:
            True if shadow position created, False if score too low or already exists
        """
        if entry_score < SHADOW_MIN_SCORE:
            return False  # Only track signals > 2.3
        
        if entry_time is None:
            entry_time = time.time()
        
        # Replace existing position if score is higher
        if symbol in self.positions:
            existing = self.positions[symbol]
            if entry_score <= existing.entry_score:
                return False  # Don't replace with lower score
            # Close existing position
            existing.closed = True
            existing.close_reason = "replaced"
            existing.close_time = entry_time
        
        # Create new shadow position
        pos = ShadowPosition(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            entry_score=entry_score,
            entry_time=entry_time
        )
        self.positions[symbol] = pos
        self._save_state()
        return True
    
    def update_position(self, symbol: str, current_price: float, 
                       current_time: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Update shadow position with current price.
        
        Returns:
            Update result dict or None if position doesn't exist
        """
        if symbol not in self.positions:
            return None
        
        if current_time is None:
            current_time = time.time()
        
        pos = self.positions[symbol]
        result = pos.update_price(current_price, current_time)
        
        # Remove closed positions after a delay
        if pos.closed and (current_time - pos.close_time) > 300:  # Keep for 5 min after close
            del self.positions[symbol]
        
        self._save_state()
        return result
    
    def get_position(self, symbol: str) -> Optional[ShadowPosition]:
        """Get shadow position for symbol."""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, ShadowPosition]:
        """Get all active shadow positions."""
        return self.positions.copy()
    
    def cleanup_expired(self):
        """Remove expired positions."""
        current_time = time.time()
        expired = []
        for symbol, pos in self.positions.items():
            if pos.closed and (current_time - pos.close_time) > 300:
                expired.append(symbol)
        
        for symbol in expired:
            del self.positions[symbol]
        
        if expired:
            self._save_state()

# Global singleton instance
_tracker_instance: Optional[ShadowTracker] = None

def get_shadow_tracker() -> ShadowTracker:
    """Get global shadow tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ShadowTracker()
    return _tracker_instance
