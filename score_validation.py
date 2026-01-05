#!/usr/bin/env python3
"""
Automated Score Validation - Sanity Check Post-Scoring

Implements sanity checks after composite scoring to detect 0.00 score bugs.
Logs CRITICAL_LOGIC_EXCEPTION and attempts to re-initialize weights.

Authoritative Source: MEMORY_BANK.md
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

class ScoreValidator:
    """Validates composite scores and triggers recovery actions"""
    
    def __init__(self):
        self.critical_exceptions_log = LOGS_DIR / "critical_logic_exceptions.jsonl"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.reinitialization_count = 0
        self.last_reinit_ts = 0
        self.reinit_cooldown_sec = 60  # 1 minute cooldown between reinitializations
    
    def validate_score(self, symbol: str, score: float, source: str, 
                      cluster_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a composite score after calculation.
        
        Args:
            symbol: Stock symbol
            score: Calculated composite score
            source: Score source (composite_v3, unknown, etc.)
            cluster_data: Original cluster data for context
        
        Returns:
            Dict with validation result and any actions taken
        """
        result = {
            "valid": True,
            "action_taken": None,
            "warning": None
        }
        
        # CRITICAL: Check for 0.00 or invalid scores
        if score <= 0.0:
            # Check if this is expected (e.g., negative sentiment for bearish)
            direction = cluster_data.get("direction", "unknown")
            
            # Log CRITICAL_LOGIC_EXCEPTION
            self._log_critical_exception(symbol, score, source, cluster_data)
            
            # Attempt re-initialization if cooldown passed
            if self._should_reinitialize():
                reinit_success = self._reinitialize_scoring_weights()
                if reinit_success:
                    result["action_taken"] = "scoring_weights_reinitialized"
                    result["warning"] = f"CRITICAL: Score was {score}, reinitialized scoring weights"
                else:
                    result["action_taken"] = "reinitialization_failed"
                    result["warning"] = f"CRITICAL: Score was {score}, reinitialization failed"
            else:
                result["warning"] = f"CRITICAL: Score was {score}, reinitialization on cooldown"
            
            # Score is still invalid even after reinit attempt
            result["valid"] = False
        
        return result
    
    def _log_critical_exception(self, symbol: str, score: float, source: str, 
                                cluster_data: Dict[str, Any]):
        """Log a CRITICAL_LOGIC_EXCEPTION"""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "CRITICAL_LOGIC_EXCEPTION",
            "symbol": symbol,
            "score": score,
            "source": source,
            "cluster_direction": cluster_data.get("direction", "unknown"),
            "cluster_count": cluster_data.get("count", 0),
            "cluster_avg_premium": cluster_data.get("avg_premium", 0),
            "reinitialization_count": self.reinitialization_count
        }
        
        with open(self.critical_exceptions_log, 'a') as f:
            f.write(json.dumps(record) + "\n")
        
        # Also log to system log
        try:
            from config.registry import append_jsonl
            append_jsonl("system", {
                "msg": "CRITICAL_LOGIC_EXCEPTION_zero_score",
                "symbol": symbol,
                "score": score,
                "source": source
            })
        except:
            pass
    
    def _should_reinitialize(self) -> bool:
        """Check if we should attempt reinitialization"""
        now = time.time()
        if now - self.last_reinit_ts < self.reinit_cooldown_sec:
            return False
        return True
    
    def _reinitialize_scoring_weights(self) -> bool:
        """
        Attempt to re-initialize uw_composite_v2.py weights.
        
        Returns:
            True if reinitialization was attempted, False otherwise
        """
        try:
            self.last_reinit_ts = time.time()
            self.reinitialization_count += 1
            
            # Try to reload the composite scoring module
            import uw_composite_v2 as uw_v2
            
            # Force reimport to clear any cached state
            import importlib
            importlib.reload(uw_v2)
            
            # Try to reinitialize if method exists
            if hasattr(uw_v2, 'reinitialize_weights'):
                uw_v2.reinitialize_weights()
            elif hasattr(uw_v2, 'get_threshold'):
                # Force a fresh threshold calculation
                try:
                    uw_v2.get_threshold(force_refresh=True)
                except TypeError:
                    # Method doesn't accept force_refresh, call normally
                    uw_v2.get_threshold()
            
            # Log successful reinitialization
            with open(self.critical_exceptions_log, 'a') as f:
                record = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "scoring_weights_reinitialized",
                    "reinitialization_count": self.reinitialization_count
                }
                f.write(json.dumps(record) + "\n")
            
            return True
            
        except Exception as e:
            # Log reinitialization failure
            with open(self.critical_exceptions_log, 'a') as f:
                record = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "reinitialization_failed",
                    "error": str(e),
                    "reinitialization_count": self.reinitialization_count
                }
                f.write(json.dumps(record) + "\n")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get validator status"""
        return {
            "reinitialization_count": self.reinitialization_count,
            "last_reinit_ts": self.last_reinit_ts,
            "critical_exceptions_log": str(self.critical_exceptions_log)
        }

# Global singleton instance
_validator_instance = None

def get_score_validator() -> ScoreValidator:
    """Get singleton validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ScoreValidator()
    return _validator_instance

if __name__ == "__main__":
    # Test the validator
    validator = get_score_validator()
    print("Score Validator Status:")
    print(json.dumps(validator.get_status(), indent=2))
