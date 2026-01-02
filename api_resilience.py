#!/usr/bin/env python3
"""
API Resilience Module - Exponential Backoff & Signal Queuing
Implements exponential backoff decorator for UW and Alpaca API calls.
Handles 429 rate limits with signal queuing for Panic regimes.
"""

import time
import functools
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from collections import deque

STATE_DIR = Path("state")
SIGNAL_QUEUE_FILE = STATE_DIR / "signal_queue.json"

class ExponentialBackoff:
    """Exponential backoff decorator for API calls"""
    
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 60.0, 
                 exponential_base: float = 2.0, retry_on: tuple = (429, 500, 502, 503, 504)):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on = retry_on
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if this is a retryable error
                    status_code = getattr(e, 'status_code', None) or getattr(e, 'response', {}).get('status_code', None)
                    if hasattr(e, 'response'):
                        try:
                            status_code = e.response.status_code
                        except:
                            pass
                    
                    # Extract status code from various exception types
                    if hasattr(e, 'status') and isinstance(e.status, int):
                        status_code = e.status
                    
                    if status_code not in self.retry_on:
                        # Not a retryable error - re-raise immediately
                        raise
                    
                    if attempt < self.max_retries - 1:
                        # Calculate delay with exponential backoff
                        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
                        time.sleep(delay)
                    else:
                        # Final attempt failed
                        break
            
            # All retries exhausted
            raise last_exception
        
        return wrapper


class SignalQueue:
    """Queue for signals that should be processed when API is available"""
    
    def __init__(self, queue_file: Path = SIGNAL_QUEUE_FILE):
        self.queue_file = queue_file
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self._queue = deque()
        self._load_queue()
    
    def _load_queue(self):
        """Load queue from disk"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                    self._queue = deque(data.get("signals", []))
            except Exception:
                self._queue = deque()
        else:
            self._queue = deque()
    
    def _save_queue(self):
        """Save queue to disk"""
        try:
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "signals": list(self._queue)
            }
            with open(self.queue_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def enqueue(self, signal_data: Dict[str, Any]):
        """Add signal to queue"""
        signal_data["queued_at"] = datetime.now(timezone.utc).isoformat()
        self._queue.append(signal_data)
        self._save_queue()
    
    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Remove and return next signal from queue"""
        if self._queue:
            signal = self._queue.popleft()
            self._save_queue()
            return signal
        return None
    
    def peek(self) -> Optional[Dict[str, Any]]:
        """Return next signal without removing it"""
        if self._queue:
            return self._queue[0]
        return None
    
    def size(self) -> int:
        """Return queue size"""
        return len(self._queue)
    
    def clear(self):
        """Clear queue"""
        self._queue.clear()
        self._save_queue()


# Global signal queue instance
_signal_queue = None

def get_signal_queue() -> SignalQueue:
    """Get global signal queue instance"""
    global _signal_queue
    if _signal_queue is None:
        _signal_queue = SignalQueue()
    return _signal_queue


def api_call_with_backoff(max_retries: int = 5, base_delay: float = 1.0, 
                          max_delay: float = 60.0, queue_on_429: bool = True):
    """
    Decorator for API calls with exponential backoff and signal queuing.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds
        queue_on_429: If True, queue signals on 429 errors (rate limit)
    
    Usage:
        @api_call_with_backoff(queue_on_429=True)
        def my_api_call(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            backoff = ExponentialBackoff(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay
            )
            
            try:
                return backoff(func)(*args, **kwargs)
            except Exception as e:
                # Check for 429 rate limit
                status_code = None
                if hasattr(e, 'response'):
                    try:
                        status_code = e.response.status_code
                    except:
                        pass
                elif hasattr(e, 'status_code'):
                    status_code = e.status_code
                elif hasattr(e, 'status') and isinstance(e.status, int):
                    status_code = e.status
                
                # If 429 and queue_on_429 is True, queue the signal
                if status_code == 429 and queue_on_429:
                    # Extract signal data from kwargs or args
                    signal_data = {
                        "function": func.__name__,
                        "args": str(args)[:500],  # Limit size
                        "kwargs": {k: str(v)[:200] for k, v in kwargs.items()},  # Limit size
                        "error": str(e)[:200],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
                    queue = get_signal_queue()
                    queue.enqueue(signal_data)
                    
                    # Re-raise with information about queuing
                    raise Exception(f"Rate limited (429) - signal queued for later processing: {e}")
                
                # Re-raise other exceptions
                raise
        
        return wrapper
    return decorator


# Convenience function for checking current regime
def is_panic_regime() -> bool:
    """Check if current market regime is PANIC"""
    try:
        from structural_intelligence.regime_detector import get_current_regime
        regime, _ = get_current_regime()
        return regime == "PANIC"
    except:
        return False
