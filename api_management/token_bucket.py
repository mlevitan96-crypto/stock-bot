#!/usr/bin/env python3
"""
Smart Quota Management: Token Bucket Algorithm
Prioritizes symbols by Volume > Open Interest.
Stays within 120 calls/min and 15k calls/day.
Focuses resources on first and last hours of market.
"""

import time
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import threading

STATE_DIR = Path("state")
TOKEN_BUCKET_STATE_FILE = STATE_DIR / "token_bucket_state.json"

class TokenBucket:
    """Token bucket algorithm for API rate limiting."""
    
    def __init__(self, rate_per_min: int = 120, daily_limit: int = 15000):
        self.rate_per_min = rate_per_min
        self.daily_limit = daily_limit
        self.tokens = float(rate_per_min)  # Start with full bucket
        self.last_refill = time.time()
        self.daily_calls = 0
        self.daily_reset_time = None
        self.lock = threading.Lock()
        self.state_file = TOKEN_BUCKET_STATE_FILE
        self._load_state()
        self._reset_daily_if_needed()
    
    def _load_state(self):
        """Load token bucket state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.daily_calls = state.get("daily_calls", 0)
                    reset_str = state.get("daily_reset_time")
                    if reset_str:
                        self.daily_reset_time = datetime.fromisoformat(reset_str.replace('Z', '+00:00'))
            except:
                pass
    
    def _save_state(self):
        """Save token bucket state"""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                "daily_calls": self.daily_calls,
                "daily_reset_time": self.daily_reset_time.isoformat() if self.daily_reset_time else None,
                "last_update": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)
    
    def _reset_daily_if_needed(self):
        """Reset daily counter if new day"""
        now = datetime.now(timezone.utc)
        if self.daily_reset_time is None:
            # Set reset time to next midnight UTC
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            self.daily_reset_time = tomorrow
        elif now >= self.daily_reset_time:
            # Reset daily counter
            self.daily_calls = 0
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            self.daily_reset_time = tomorrow
            self._save_state()
    
    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = (elapsed / 60.0) * self.rate_per_min
        self.tokens = min(self.rate_per_min, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def can_make_call(self) -> bool:
        """Check if we can make an API call"""
        with self.lock:
            self._reset_daily_if_needed()
            self._refill_tokens()
            
            # Check daily limit
            if self.daily_calls >= self.daily_limit:
                return False
            
            # Check token bucket
            if self.tokens >= 1.0:
                return True
            
            return False
    
    def consume_token(self):
        """Consume a token (call this after making API call)"""
        with self.lock:
            self._refill_tokens()
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                self.daily_calls += 1
                self._save_state()
                return True
            return False
    
    def get_wait_time(self) -> float:
        """Get time to wait before next call is allowed"""
        with self.lock:
            self._reset_daily_if_needed()
            self._refill_tokens()
            
            if self.daily_calls >= self.daily_limit:
                # Wait until next day
                if self.daily_reset_time:
                    wait_seconds = (self.daily_reset_time - datetime.now(timezone.utc)).total_seconds()
                    return max(0, wait_seconds)
                return 3600  # Default 1 hour
            
            if self.tokens < 1.0:
                # Wait for token refill
                tokens_needed = 1.0 - self.tokens
                wait_seconds = (tokens_needed / self.rate_per_min) * 60.0
                return max(0, wait_seconds)
            
            return 0.0
    
    def get_status(self) -> Dict:
        """Get current token bucket status"""
        with self.lock:
            self._reset_daily_if_needed()
            self._refill_tokens()
            
            return {
                "tokens_available": self.tokens,
                "rate_per_min": self.rate_per_min,
                "daily_calls": self.daily_calls,
                "daily_limit": self.daily_limit,
                "daily_remaining": self.daily_limit - self.daily_calls,
                "can_make_call": self.tokens >= 1.0 and self.daily_calls < self.daily_limit
            }

class SmartQuotaManager:
    """Smart quota manager with symbol prioritization and time-based focusing."""
    
    def __init__(self):
        self.token_bucket = TokenBucket(rate_per_min=120, daily_limit=15000)
        self.symbol_priority = {}  # symbol -> priority score
        self.market_hours_focus = True
    
    def _is_market_open_hours(self) -> bool:
        """Check if we're in first or last hour of market (9:30-10:30 or 3:00-4:00 ET)"""
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            try:
                from backports.zoneinfo import ZoneInfo
            except ImportError:
                # Fallback: Use UTC offset (ET is UTC-5, but DST makes it UTC-4)
                # This is approximate - for production, install tzdata
                now = datetime.now(timezone.utc)
                # Assume ET is UTC-5 (winter) or UTC-4 (summer) - approximate
                et_offset = timedelta(hours=-5)  # Winter time
                et_now = now + et_offset
                hour = et_now.hour
                minute = et_now.minute
                
                # First hour: 9:30-10:30
                if hour == 9 and minute >= 30:
                    return True
                if hour == 10 and minute < 30:
                    return True
                
                # Last hour: 3:00-4:00
                if hour == 15:  # 3 PM
                    return True
                if hour == 16 and minute == 0:  # 4 PM exactly
                    return True
                
                return False
        
        now = datetime.now(timezone.utc)
        try:
            et_now = now.astimezone(ZoneInfo("America/New_York"))
        except:
            # Fallback if timezone data not available
            et_offset = timedelta(hours=-5)
            et_now = now + et_offset
        hour = et_now.hour
        minute = et_now.minute
        
        # First hour: 9:30-10:30
        if hour == 9 and minute >= 30:
            return True
        if hour == 10 and minute < 30:
            return True
        
        # Last hour: 3:00-4:00
        if hour == 15:  # 3 PM
            return True
        if hour == 16 and minute == 0:  # 4 PM exactly
            return True
        
        return False
    
    def prioritize_symbol(self, symbol: str, volume: float, open_interest: float):
        """Prioritize symbol based on Volume > Open Interest"""
        # Priority = volume * 0.7 + open_interest * 0.3
        priority = (volume * 0.7) + (open_interest * 0.3)
        self.symbol_priority[symbol] = priority
    
    def should_poll_symbol(self, symbol: str) -> Tuple[bool, float]:
        """
        Determine if we should poll a symbol.
        Returns: (should_poll, wait_time)
        """
        # Check if we can make a call
        if not self.token_bucket.can_make_call():
            wait_time = self.token_bucket.get_wait_time()
            return False, wait_time
        
        # If market hours focus is enabled, prioritize first/last hour
        if self.market_hours_focus:
            if not self._is_market_open_hours():
                # Outside focus hours - only poll high priority symbols
                priority = self.symbol_priority.get(symbol, 0.0)
                if priority < 1000000:  # Only poll high-volume symbols
                    return False, 60.0  # Wait 1 minute
        
        # Check symbol priority
        priority = self.symbol_priority.get(symbol, 0.0)
        
        # Always allow if we have tokens and within daily limit
        if self.token_bucket.can_make_call():
            return True, 0.0
        
        wait_time = self.token_bucket.get_wait_time()
        return False, wait_time
    
    def record_api_call(self, symbol: str):
        """Record that an API call was made"""
        self.token_bucket.consume_token()
    
    def get_quota_status(self) -> Dict:
        """Get current quota status"""
        bucket_status = self.token_bucket.get_status()
        return {
            **bucket_status,
            "symbols_tracked": len(self.symbol_priority),
            "market_hours_focus": self.market_hours_focus,
            "in_focus_hours": self._is_market_open_hours()
        }

# Global instance
_quota_manager = None

def get_quota_manager() -> SmartQuotaManager:
    """Get global quota manager instance"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = SmartQuotaManager()
    return _quota_manager

