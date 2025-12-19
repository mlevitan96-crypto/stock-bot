#!/usr/bin/env python3
"""
Universal Parameter Optimizer
=============================
Framework for optimizing any hardcoded parameter based on historical outcomes.

Features:
- Test multiple parameter values
- Track outcomes with exponential decay weighting
- Gradually adjust toward optimal (anti-overfitting)
- Regime-specific and symbol-specific optimization
- Multi-parameter optimization (test combinations)
"""

import json
import math
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

DATA_DIR = Path("data")
STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

PARAMETER_STATE_FILE = STATE_DIR / "parameter_optimization_state.json"
ATTRIBUTION_FILE = LOGS_DIR / "attribution.jsonl"


@dataclass
class ParameterTest:
    """Represents a parameter value being tested"""
    param_name: str
    test_value: float
    test_count: int = 0
    total_outcome: float = 0.0
    weighted_outcome: float = 0.0
    total_weight: float = 0.0
    wins: int = 0
    losses: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ParameterOptimizer:
    """Universal framework for optimizing any hardcoded parameter."""
    
    def __init__(self):
        self.parameter_tests: Dict[str, List[ParameterTest]] = {}
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load optimization state."""
        try:
            if PARAMETER_STATE_FILE.exists():
                return json.loads(PARAMETER_STATE_FILE.read_text())
        except Exception:
            pass
        return {}
    
    def _save_state(self):
        """Save optimization state."""
        try:
            PARAMETER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            PARAMETER_STATE_FILE.write_text(json.dumps(self.state, indent=2))
        except Exception:
            pass
    
    def _exponential_decay_weight(self, age_days: float, halflife_days: float = 30.0) -> float:
        """Calculate exponential decay weight for time-weighted learning."""
        return math.exp(-age_days * math.log(2) / halflife_days)
    
    def optimize_parameter(self,
                          param_name: str,
                          test_values: List[float],
                          outcome_metric: str = "pnl",
                          min_samples: int = 30,
                          lookback_days: int = 60) -> Dict[str, Any]:
        """
        Test different parameter values and learn optimal.
        
        Args:
            param_name: Name of parameter (e.g., "TRAILING_STOP_PCT")
            test_values: List of values to test (e.g., [0.010, 0.015, 0.020, 0.025])
            outcome_metric: What to optimize ("pnl", "win_rate", "sharpe")
            min_samples: Minimum samples before making recommendations
            lookback_days: How far back to look
        
        Returns:
            {
                "status": "success",
                "best_value": float,
                "test_results": {...},
                "recommendation": float (gradual adjustment)
            }
        """
        if not ATTRIBUTION_FILE.exists():
            return {"status": "skipped", "reason": "no_trades"}
        
        # Initialize test tracking
        if param_name not in self.parameter_tests:
            self.parameter_tests[param_name] = [
                ParameterTest(param_name=param_name, test_value=val)
                for val in test_values
            ]
        
        tests = self.parameter_tests[param_name]
        now = datetime.now(timezone.utc)
        
        # Process historical trades
        with ATTRIBUTION_FILE.open("r") as f:
            lines = f.readlines()
        
        for line in lines:
            try:
                trade = json.loads(line.strip())
                if trade.get("type") != "attribution":
                    continue
                
                ts_str = trade.get("ts", "")
                if not ts_str:
                    continue
                
                trade_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if trade_time.tzinfo is None:
                    trade_time = trade_time.replace(tzinfo=timezone.utc)
                else:
                    trade_time = trade_time.astimezone(timezone.utc)
                
                trade_age_days = (now - trade_time).total_seconds() / 86400.0
                if trade_age_days > lookback_days:
                    continue
                
                decay_weight = self._exponential_decay_weight(trade_age_days)
                
                # Get outcome
                if outcome_metric == "pnl":
                    outcome = float(trade.get("pnl_usd", 0.0))
                elif outcome_metric == "pnl_pct":
                    outcome = float(trade.get("context", {}).get("pnl_pct", 0.0))
                else:
                    outcome = 0.0
                
                # Simulate: "What if we used test_value for this trade?"
                # This requires parameter-specific simulation logic
                # For now, we'll use a simplified approach
                for test in tests:
                    # Simulate outcome with this parameter value
                    # (Implementation depends on parameter type)
                    simulated_outcome = self._simulate_parameter_effect(
                        param_name, test.test_value, trade, outcome
                    )
                    
                    test.test_count += 1
                    test.total_outcome += simulated_outcome
                    test.weighted_outcome += simulated_outcome * decay_weight
                    test.total_weight += decay_weight
                    
                    if simulated_outcome > 0:
                        test.wins += 1
                    else:
                        test.losses += 1
                
            except Exception as e:
                continue
        
        # Find best value
        best_test = None
        best_weighted_avg = float('-inf')
        
        for test in tests:
            if test.test_count < min_samples:
                continue
            
            if test.total_weight > 0:
                weighted_avg = test.weighted_outcome / test.total_weight
            else:
                weighted_avg = test.total_outcome / test.test_count
            
            if weighted_avg > best_weighted_avg:
                best_weighted_avg = weighted_avg
                best_test = test
        
        if not best_test:
            return {"status": "insufficient_data", "min_samples": min_samples}
        
        # Calculate gradual recommendation (10% toward optimal)
        current_value = self._get_current_parameter_value(param_name)
        if current_value is None:
            current_value = test_values[len(test_values) // 2]  # Use middle value as default
        
        recommendation = current_value + (best_test.test_value - current_value) * 0.1
        
        return {
            "status": "success",
            "best_value": best_test.test_value,
            "best_weighted_avg": round(best_weighted_avg, 2),
            "current_value": current_value,
            "recommendation": round(recommendation, 4),
            "test_results": {
                str(test.test_value): {
                    "count": test.test_count,
                    "weighted_avg": round(test.weighted_outcome / test.total_weight, 2) if test.total_weight > 0 else 0,
                    "win_rate": round(test.wins / test.test_count * 100, 1) if test.test_count > 0 else 0
                }
                for test in tests
            }
        }
    
    def _simulate_parameter_effect(self, param_name: str, test_value: float, 
                                   trade: Dict, actual_outcome: float) -> float:
        """
        Simulate how a different parameter value would have affected this trade.
        
        This is parameter-specific and requires custom logic per parameter type.
        For now, returns actual outcome (placeholder).
        """
        # TODO: Implement parameter-specific simulation
        # Examples:
        # - TRAILING_STOP_PCT: Would different stop have triggered earlier/later?
        # - TIME_EXIT_MINUTES: Would different time exit have been better?
        # - PROFIT_TARGETS: Would different targets have captured more profit?
        
        return actual_outcome
    
    def _get_current_parameter_value(self, param_name: str) -> Optional[float]:
        """Get current value of parameter from config."""
        try:
            from config.registry import Thresholds
            return getattr(Thresholds, param_name, None)
        except Exception:
            return None
    
    def optimize_all_parameters(self) -> Dict[str, Any]:
        """Optimize all hardcoded parameters."""
        results = {}
        
        # Exit parameters
        results["TRAILING_STOP_PCT"] = self.optimize_parameter(
            "TRAILING_STOP_PCT", [0.010, 0.015, 0.020, 0.025]
        )
        results["TIME_EXIT_MINUTES"] = self.optimize_parameter(
            "TIME_EXIT_MINUTES", [180, 240, 300, 360]
        )
        results["TIME_EXIT_DAYS_STALE"] = self.optimize_parameter(
            "TIME_EXIT_DAYS_STALE", [10, 12, 14, 16]
        )
        
        # Entry parameters
        results["MIN_EXEC_SCORE"] = self.optimize_parameter(
            "MIN_EXEC_SCORE", [1.5, 2.0, 2.5, 3.0]
        )
        results["MIN_PREMIUM_USD"] = self.optimize_parameter(
            "MIN_PREMIUM_USD", [50000, 100000, 200000, 500000]
        )
        
        # Position management
        results["MAX_CONCURRENT_POSITIONS"] = self.optimize_parameter(
            "MAX_CONCURRENT_POSITIONS", [12, 16, 20, 24]
        )
        results["POSITION_SIZE_USD"] = self.optimize_parameter(
            "POSITION_SIZE_USD", [300, 500, 750, 1000]
        )
        
        return results


def get_parameter_optimizer() -> ParameterOptimizer:
    """Get or create parameter optimizer instance."""
    global _parameter_optimizer
    if _parameter_optimizer is None:
        _parameter_optimizer = ParameterOptimizer()
    return _parameter_optimizer


_parameter_optimizer: Optional[ParameterOptimizer] = None
