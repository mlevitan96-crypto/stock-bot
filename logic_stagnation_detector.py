#!/usr/bin/env python3
"""
Logic Stagnation Detector - Semantic Watchdog for Trading Bot

Monitors signal-to-trade ratio and detects when execution deviates from signal volume.
Triggers auto-recalibration when logic failures are detected.

Authoritative Source: MEMORY_BANK.md
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from collections import deque

STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

# Thresholds for stagnation detection
SIGNAL_ZERO_SCORE_THRESHOLD = 20  # Trigger after 20 signals with score=0.00
MOMENTUM_BLOCK_THRESHOLD = 10  # Trigger after 10 consecutive momentum blocks
SOFT_RESET_COOLDOWN_SEC = 300  # 5 minutes between resets

class LogicStagnationDetector:
    """Detects when trading logic is stagnating and triggers soft resets"""
    
    def __init__(self):
        self.state_file = STATE_DIR / "logic_stagnation_state.json"
        self.state = self._load_state()
        
        # In-memory tracking (last 100 signals)
        self.recent_signals = deque(maxlen=100)
        self.recent_blocks = deque(maxlen=100)
        
        # Tracking counters
        self.zero_score_count = 0
        self.consecutive_momentum_blocks = 0
        self.last_soft_reset_ts = self.state.get("last_soft_reset_ts", 0)
    
    def _load_state(self) -> Dict[str, Any]:
        """Load detector state from disk"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_soft_reset_ts": 0,
            "soft_reset_count": 0,
            "zero_score_detections": 0,
            "momentum_block_detections": 0
        }
    
    def _save_state(self):
        """Save detector state to disk"""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def record_signal(self, symbol: str, score: float, source: str = "unknown"):
        """Record a signal for stagnation tracking"""
        signal_record = {
            "timestamp": time.time(),
            "symbol": symbol,
            "score": score,
            "source": source
        }
        self.recent_signals.append(signal_record)
        
        # Check for zero scores
        if score <= 0.0:
            self.zero_score_count += 1
        else:
            self.zero_score_count = 0  # Reset counter on non-zero score
    
    def record_momentum_block(self, symbol: str, reason: str):
        """Record a momentum filter block"""
        block_record = {
            "timestamp": time.time(),
            "symbol": symbol,
            "reason": reason
        }
        self.recent_blocks.append(block_record)
        self.consecutive_momentum_blocks += 1
    
    def record_momentum_pass(self):
        """Record a momentum filter pass (resets consecutive counter)"""
        self.consecutive_momentum_blocks = 0
    
    def check_stagnation(self) -> Optional[Dict[str, Any]]:
        """
        Check if logic stagnation is detected.
        
        Returns:
            Dict with stagnation details if detected, None otherwise
        """
        now = time.time()
        
        # Check cooldown period
        if now - self.last_soft_reset_ts < SOFT_RESET_COOLDOWN_SEC:
            return None
        
        stagnation_detected = False
        stagnation_reason = None
        
        # Check zero score threshold
        if self.zero_score_count >= SIGNAL_ZERO_SCORE_THRESHOLD:
            stagnation_detected = True
            stagnation_reason = f"zero_score_stagnation_{self.zero_score_count}_signals"
            self.state["zero_score_detections"] = self.state.get("zero_score_detections", 0) + 1
        
        # Check momentum block threshold
        if self.consecutive_momentum_blocks >= MOMENTUM_BLOCK_THRESHOLD:
            stagnation_detected = True
            stagnation_reason = f"momentum_block_stagnation_{self.consecutive_momentum_blocks}_blocks"
            self.state["momentum_block_detections"] = self.state.get("momentum_block_detections", 0) + 1
        
        if stagnation_detected:
            return {
                "detected": True,
                "reason": stagnation_reason,
                "zero_score_count": self.zero_score_count,
                "consecutive_momentum_blocks": self.consecutive_momentum_blocks,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return None
    
    def trigger_soft_reset(self) -> bool:
        """
        Trigger a soft reset of the scoring engine.
        
        Returns:
            True if reset was triggered, False if cooldown active
        """
        now = time.time()
        
        # Check cooldown
        if now - self.last_soft_reset_ts < SOFT_RESET_COOLDOWN_SEC:
            return False
        
        # Log the soft reset
        self._log_soft_reset()
        
        # Reset counters
        self.zero_score_count = 0
        self.consecutive_momentum_blocks = 0
        self.last_soft_reset_ts = now
        
        # Update state
        self.state["last_soft_reset_ts"] = now
        self.state["soft_reset_count"] = self.state.get("soft_reset_count", 0) + 1
        self._save_state()
        
        # Trigger re-initialization of scoring weights
        try:
            self._reinitialize_scoring_weights()
        except Exception as e:
            # Log error but don't fail
            self._log_error(f"Failed to reinitialize scoring weights: {e}")
        
        return True
    
    def _reinitialize_scoring_weights(self):
        """Re-initialize uw_composite_v2.py weights"""
        try:
            # Try to reload the composite scoring module
            import uw_composite_v2 as uw_v2
            if hasattr(uw_v2, 'reinitialize_weights'):
                uw_v2.reinitialize_weights()
            elif hasattr(uw_v2, 'get_threshold'):
                # Force a fresh threshold calculation
                uw_v2.get_threshold(force_refresh=True)
        except ImportError:
            pass
        except Exception as e:
            raise
    
    def _log_soft_reset(self):
        """Log soft reset event"""
        log_file = LOGS_DIR / "logic_stagnation.jsonl"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "soft_reset_triggered",
            "zero_score_count": self.zero_score_count,
            "consecutive_momentum_blocks": self.consecutive_momentum_blocks,
            "reset_count": self.state.get("soft_reset_count", 0) + 1
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(record) + "\n")
        
        # Also log to system log
        try:
            from config.registry import append_jsonl
            append_jsonl("system", {
                "msg": "logic_stagnation_soft_reset",
                "zero_score_count": self.zero_score_count,
                "consecutive_momentum_blocks": self.consecutive_momentum_blocks
            })
        except:
            pass
    
    def _log_error(self, error_msg: str):
        """Log error event"""
        log_file = LOGS_DIR / "logic_stagnation.jsonl"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "error",
            "error": error_msg
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(record) + "\n")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current detector status"""
        return {
            "zero_score_count": self.zero_score_count,
            "consecutive_momentum_blocks": self.consecutive_momentum_blocks,
            "last_soft_reset_ts": self.last_soft_reset_ts,
            "soft_reset_count": self.state.get("soft_reset_count", 0),
            "zero_score_detections": self.state.get("zero_score_detections", 0),
            "momentum_block_detections": self.state.get("momentum_block_detections", 0),
            "recent_signals_count": len(self.recent_signals),
            "recent_blocks_count": len(self.recent_blocks)
        }

# Global singleton instance
_detector_instance = None

def get_stagnation_detector() -> LogicStagnationDetector:
    """Get singleton detector instance"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LogicStagnationDetector()
    return _detector_instance

if __name__ == "__main__":
    # Test the detector
    detector = get_stagnation_detector()
    print("Logic Stagnation Detector Status:")
    print(json.dumps(detector.get_status(), indent=2))
