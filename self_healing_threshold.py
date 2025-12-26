#!/usr/bin/env python3
"""
Self-Healing Threshold System
Raises MIN_EXEC_SCORE by 0.5 points if last 3 trades were losses.
Resets after 24 hours or one winning trade.
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta

STATE_FILE = Path("state/self_healing_threshold.json")

class SelfHealingThreshold:
    """
    Self-healing threshold that adapts MIN_EXEC_SCORE based on recent performance.
    
    Logic:
    - If last 3 trades are losses: raise threshold by 0.5
    - Reset after 24 hours or one winning trade
    """
    
    def __init__(self, base_threshold: float = 2.0):
        self.base_threshold = base_threshold
        self.adjustment = 0.0
        self.activated_at: Optional[int] = None
        self.last_reset_at: Optional[int] = None
        self.consecutive_losses = 0
        self._load_state()
    
    def _load_state(self):
        """Load state from file"""
        if STATE_FILE.exists():
            try:
                with STATE_FILE.open() as f:
                    state = json.load(f)
                self.adjustment = state.get("adjustment", 0.0)
                self.activated_at = state.get("activated_at")
                self.last_reset_at = state.get("last_reset_at")
                self.consecutive_losses = state.get("consecutive_losses", 0)
            except Exception as e:
                print(f"[WARN] Failed to load self-healing threshold state: {e}")
    
    def _save_state(self):
        """Save state to file"""
        STATE_FILE.parent.mkdir(exist_ok=True)
        with STATE_FILE.open("w") as f:
            json.dump({
                "adjustment": self.adjustment,
                "activated_at": self.activated_at,
                "last_reset_at": self.last_reset_at,
                "consecutive_losses": self.consecutive_losses,
                "updated_at": int(time.time())
            }, f, indent=2)
    
    def check_recent_trades(self) -> float:
        """
        Check recent trades and adjust threshold if needed.
        
        Returns:
            Adjusted threshold (base_threshold + adjustment)
        """
        # Check if 24 hours have passed since activation
        if self.activated_at:
            hours_since_activation = (time.time() - self.activated_at) / 3600
            if hours_since_activation >= 24:
                self._reset()
                return self.base_threshold
        
        # Check recent trades from attribution.jsonl
        attribution_file = Path("logs/attribution.jsonl")
        if not attribution_file.exists():
            attribution_file = Path("data/attribution.jsonl")
        
        if not attribution_file.exists():
            return self.base_threshold + self.adjustment
        
        # Read last 3 trades
        recent_trades = []
        try:
            with attribution_file.open() as f:
                lines = f.readlines()
                # Get last 3 trades (most recent first)
                for line in reversed(lines[-10:]):  # Check last 10 lines for safety
                    try:
                        trade = json.loads(line.strip())
                        if trade.get("type") == "attribution":
                            recent_trades.append(trade)
                            if len(recent_trades) >= 3:
                                break
                    except:
                        continue
        except Exception as e:
            print(f"[WARN] Failed to read attribution file: {e}")
            return self.base_threshold + self.adjustment
        
        # Check if last 3 trades are losses
        if len(recent_trades) >= 3:
            all_losses = all(
                (trade.get("pnl_pct", 0) or trade.get("context", {}).get("pnl_pct", 0)) < 0
                for trade in recent_trades[:3]
            )
            
            if all_losses and self.adjustment == 0.0:
                # Activate threshold increase
                self.adjustment = 0.5
                self.activated_at = int(time.time())
                self.consecutive_losses = 3
                self._save_state()
                return self.base_threshold + self.adjustment
            elif not all_losses and self.adjustment > 0.0:
                # Reset if we have a winning trade
                self._reset()
                return self.base_threshold
        
        return self.base_threshold + self.adjustment
    
    def _reset(self):
        """Reset threshold adjustment"""
        self.adjustment = 0.0
        self.activated_at = None
        self.last_reset_at = int(time.time())
        self.consecutive_losses = 0
        self._save_state()
    
    def get_current_threshold(self) -> float:
        """Get current threshold (base + adjustment)"""
        return self.base_threshold + self.adjustment
    
    def is_activated(self) -> bool:
        """Check if threshold is currently raised"""
        return self.adjustment > 0.0
    
    def get_status(self) -> Dict:
        """Get current status for logging"""
        return {
            "base_threshold": self.base_threshold,
            "adjustment": self.adjustment,
            "current_threshold": self.get_current_threshold(),
            "is_activated": self.is_activated(),
            "activated_at": self.activated_at,
            "consecutive_losses": self.consecutive_losses
        }

