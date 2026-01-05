#!/usr/bin/env python3
"""
Momentum Ignition Filter - Ensures price is actually moving before executing a Whale signal.

Uses Alpaca Professional SIP data to verify +0.2% price movement in 2 minutes before entry.
This prevents entering on stale signals that have already moved.
"""
import os
import requests
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
        self.momentum_threshold_pct = 0.0005  # 0.05% = 5 basis points (reduced from 0.2%)
        self.lookback_minutes = 2
    
    def check_momentum(self, symbol: str, signal_direction: str, current_price: float, entry_score: float = 0.0) -> Dict[str, Any]:
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
            
            return {
                "passed": momentum_passed,
                "price_change_pct": price_change_pct,
                "price_2min_ago": price_2min_ago,
                "current_price": price_now,
                "reason": reason
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

def check_momentum_before_entry(symbol: str, signal_direction: str, current_price: float, entry_score: float = 0.0) -> Dict[str, Any]:
    """
    Convenience function to check momentum before entry.
    
    Args:
        symbol: Stock symbol
        signal_direction: "bullish" or "bearish"
        current_price: Current price
        entry_score: Entry score for soft-fail mode (default: 0.0)
    
    Returns dict with 'passed' key indicating if entry should proceed.
    """
    filter_instance = get_momentum_filter()
    return filter_instance.check_momentum(symbol, signal_direction, current_price, entry_score)

if __name__ == "__main__":
    # Test the filter
    filter_instance = get_momentum_filter()
    result = filter_instance.check_momentum("AAPL", "bullish", 150.0)
    print(f"Momentum check result: {result}")
