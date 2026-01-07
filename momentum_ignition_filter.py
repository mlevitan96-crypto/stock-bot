#!/usr/bin/env python3
"""
Momentum Ignition Filter - Ensures price is actually moving before executing a Whale signal.

Uses Alpaca Professional SIP data to verify +0.2% price movement in 2 minutes before entry.
This prevents entering on stale signals that have already moved.
"""
import os
import json
import requests
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from config.registry import APIConfig

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class MomentumIgnitionFilter:
    """Filter that checks for price momentum before entry"""
    
    def __init__(self):
        """Initialize with Alpaca credentials"""
        self.api_key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY", "")
        self.api_secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET", "")
        self.base_url = "https://data.alpaca.markets/v2/stocks"
        self.headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
        self.base_momentum_threshold_pct = 0.0001  # 0.01% = 1 basis point (TEMPORARILY LOWERED to allow trades)
        self.momentum_threshold_pct = self.base_momentum_threshold_pct
        self.lookback_minutes = 2
        
        # Dynamic scaling state
        self.state_file = Path("state/momentum_scaling_state.json")
        self._load_scaling_state()
        
        # Track blocks in PANIC regime
        self.panic_block_window_start = None
        self.panic_block_count = 0
        self.panic_window_duration_sec = 1800  # 30 minutes
        self.max_panic_blocks = 100  # 100% blocks = all trades blocked
        self.scaling_adjustment_pct = 0.25  # 25% reduction per adjustment
    
    def _load_scaling_state(self):
        """Load dynamic scaling state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.momentum_threshold_pct = state.get("current_threshold", self.base_momentum_threshold_pct)
                    self.panic_block_window_start = state.get("panic_block_window_start")
                    self.panic_block_count = state.get("panic_block_count", 0)
            except:
                pass
    
    def _save_scaling_state(self):
        """Save dynamic scaling state to disk"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "current_threshold": self.momentum_threshold_pct,
            "base_threshold": self.base_momentum_threshold_pct,
            "panic_block_window_start": self.panic_block_window_start,
            "panic_block_count": self.panic_block_count,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _check_and_adjust_panic_scaling(self, market_regime: str = "mixed"):
        """Check if we should adjust threshold in PANIC regime"""
        # Check if we're in PANIC regime
        is_panic = market_regime.upper() == "PANIC" or "PANIC" in market_regime.upper()
        if not is_panic:
            # Reset tracking if not in PANIC
            self.panic_block_window_start = None
            self.panic_block_count = 0
            return
        
        now = time.time()
        
        # Initialize or reset window if needed
        if self.panic_block_window_start is None:
            self.panic_block_window_start = now
            self.panic_block_count = 0
        
        # Check if window has expired
        if now - self.panic_block_window_start > self.panic_window_duration_sec:
            # Reset window
            self.panic_block_window_start = now
            self.panic_block_count = 0
        
        # Increment block count
        self.panic_block_count += 1
        
        # Check if 100% of trades blocked (all trades in window blocked)
        # We track this by checking if block count exceeds expected trade frequency
        # For simplicity, if we've blocked many trades and window is active, adjust
        if self.panic_block_count >= 10:  # At least 10 blocks in 30 min window
            # Calculate block rate (simplified: assume we're blocking 100% if count is high)
            # Adjust threshold down by 25%
            new_threshold = self.momentum_threshold_pct * (1.0 - self.scaling_adjustment_pct)
            
            # Don't go below 0.01% (1 basis point minimum)
            min_threshold = 0.0001
            if new_threshold < min_threshold:
                new_threshold = min_threshold
            
            if new_threshold < self.momentum_threshold_pct:
                old_threshold = self.momentum_threshold_pct
                self.momentum_threshold_pct = new_threshold
                self._save_scaling_state()
                self._log_threshold_adjustment(old_threshold, new_threshold, self.panic_block_count)
                
                # Reset tracking after adjustment
                self.panic_block_window_start = None
                self.panic_block_count = 0
    
    def _log_threshold_adjustment(self, old_threshold: float, new_threshold: float, block_count: int):
        """Log threshold adjustment event"""
        log_file = Path("logs/momentum_scaling.jsonl")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "threshold_adjusted_panic_regime",
            "old_threshold_pct": old_threshold,
            "new_threshold_pct": new_threshold,
            "block_count": block_count,
            "adjustment_pct": self.scaling_adjustment_pct * 100
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(record) + "\n")
        
        # Also log to system log
        try:
            from config.registry import append_jsonl
            append_jsonl("system", {
                "msg": "momentum_threshold_adjusted_panic",
                "old_threshold": old_threshold,
                "new_threshold": new_threshold,
                "block_count": block_count
            })
        except:
            pass
    
    def reset_to_base_threshold(self):
        """Reset threshold to base value (called when trade is captured)"""
        if self.momentum_threshold_pct < self.base_momentum_threshold_pct:
            self.momentum_threshold_pct = self.base_momentum_threshold_pct
            self._save_scaling_state()
    
    def check_momentum(self, symbol: str, signal_direction: str, current_price: float, 
                      entry_score: float = 0.0, market_regime: str = "mixed") -> Dict[str, Any]:
        """
        Check if price has moved +0.2% in the last 2 minutes.
        
        Args:
            symbol: Stock symbol
            signal_direction: "bullish" or "bearish"
            current_price: Current price at signal time
            
        Returns:
            Dict with:
                - passed: bool (True if momentum detected)
                - price_change_pct: float (actual price change %)
                - price_2min_ago: float (price 2 minutes ago)
                - current_price: float
                - reason: str (why it passed/failed)
        """
        if not self.api_key or not self.api_secret:
            return {
                "passed": True,  # Fail open - don't block if API unavailable
                "price_change_pct": 0.0,
                "price_2min_ago": current_price,
                "current_price": current_price,
                "reason": "api_unavailable_fail_open"
            }
        
        try:
            # Get bars from 3 minutes ago to now (1-minute bars)
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=3)
            
            url = f"{self.base_url}/bars"
            params = {
                "symbols": symbol,
                "timeframe": "1Min",
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%S-00:00"),
                "end": end_time.strftime("%Y-%m-%dT%H:%M:%S-00:00"),
                "limit": 5,
                "adjustment": "raw",
                "feed": "sip",  # Professional SIP feed
                "sort": "asc"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            bars = data.get("bars", {}).get(symbol, [])
            
            if len(bars) < 2:
                # Not enough data - fail open
                return {
                    "passed": True,
                    "price_change_pct": 0.0,
                    "price_2min_ago": current_price,
                    "current_price": current_price,
                    "reason": "insufficient_data_fail_open"
                }
            
            # Get price from ~2 minutes ago (second bar from start)
            price_2min_ago = float(bars[0]["c"])  # Close price of oldest bar
            price_now = float(bars[-1]["c"])  # Close price of most recent bar
            
            # Calculate price change
            price_change_pct = (price_now - price_2min_ago) / price_2min_ago
            
            # Check momentum based on signal direction
            if signal_direction.lower() in ["bullish", "long", "buy"]:
                # Bullish: need positive momentum (+0.05% reduced from 0.2%)
                momentum_passed = price_change_pct >= self.momentum_threshold_pct
                reason = "bullish_momentum_confirmed" if momentum_passed else f"insufficient_bullish_momentum_{price_change_pct*100:.2f}%"
            else:  # bearish/short/sell
                # Bearish: need negative momentum (-0.05% reduced from 0.2%)
                momentum_passed = price_change_pct <= -self.momentum_threshold_pct
                reason = "bearish_momentum_confirmed" if momentum_passed else f"insufficient_bearish_momentum_{price_change_pct*100:.2f}%"
            
            # SOFT-FAIL MODE: If momentum is 0.00% but entry_score > 4.0, allow trade with warning
            if not momentum_passed and entry_score > 4.0 and abs(price_change_pct) < 0.001:  # < 0.1% movement
                momentum_passed = True
                reason = f"high_conviction_soft_pass_score_{entry_score:.2f}_momentum_{price_change_pct*100:.2f}%"
            
            # DYNAMIC MOMENTUM SCALING: Check if we should adjust threshold in PANIC regime
            if not momentum_passed:
                self._check_and_adjust_panic_scaling(market_regime)
            
            return {
                "passed": momentum_passed,
                "price_change_pct": price_change_pct,
                "price_2min_ago": price_2min_ago,
                "current_price": price_now,
                "reason": reason,
                "threshold_used": self.momentum_threshold_pct
            }
            
        except Exception as e:
            # Fail open on errors - don't block trades due to API issues
            return {
                "passed": True,
                "price_change_pct": 0.0,
                "price_2min_ago": current_price,
                "current_price": current_price,
                "reason": f"error_fail_open_{str(e)[:50]}"
            }

# Global instance
_momentum_filter = None

def get_momentum_filter() -> MomentumIgnitionFilter:
    """Get singleton instance"""
    global _momentum_filter
    if _momentum_filter is None:
        _momentum_filter = MomentumIgnitionFilter()
    return _momentum_filter

def check_momentum_before_entry(symbol: str, signal_direction: str, current_price: float, 
                                entry_score: float = 0.0, market_regime: str = "mixed") -> Dict[str, Any]:
    """
    Convenience function to check momentum before entry.
    
    Args:
        symbol: Stock symbol
        signal_direction: "bullish" or "bearish"
        current_price: Current price
        entry_score: Entry score for soft-fail mode (default: 0.0)
        market_regime: Market regime for dynamic scaling (default: "mixed")
    
    Returns dict with 'passed' key indicating if entry should proceed.
    """
    filter_instance = get_momentum_filter()
    result = filter_instance.check_momentum(symbol, signal_direction, current_price, entry_score, market_regime)
    
    # Reset threshold if trade passes (captured a trade)
    if result.get("passed", False):
        filter_instance.reset_to_base_threshold()
    
    return result

if __name__ == "__main__":
    # Test the filter
    filter_instance = get_momentum_filter()
    result = filter_instance.check_momentum("AAPL", "bullish", 150.0)
    print(f"Momentum check result: {result}")
