#!/usr/bin/env python3
"""
Universal Parameter Optimizer
Learns optimal values for all hardcoded parameters through historical analysis.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

STATE_DIR = Path("state")
PARAMETER_OPTIMIZATION_STATE = STATE_DIR / "parameter_optimization.json"

class ParameterOptimizer:
    """Universal framework for optimizing any hardcoded parameter."""
    
    def __init__(self):
        self.state_file = PARAMETER_OPTIMIZATION_STATE
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load optimization state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "parameters": {},  # param_name -> {current_value, optimal_value, test_values, outcomes}
            "last_updated": None
        }
    
    def _save_state(self):
        """Save optimization state"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2)
    
    def register_parameter(self, param_name: str, current_value: float, 
                          test_values: List[float], description: str = ""):
        """
        Register a parameter for optimization.
        
        Args:
            param_name: Name of parameter (e.g., "TRAILING_STOP_PCT")
            current_value: Current parameter value
            test_values: List of values to test
            description: Description of parameter
        """
        if param_name not in self.state["parameters"]:
            self.state["parameters"][param_name] = {
                "current_value": current_value,
                "optimal_value": current_value,
                "test_values": test_values,
                "outcomes": {},  # value -> {pnl_sum, win_rate, samples}
                "description": description,
                "last_optimized": None
            }
        else:
            # Update current value if changed
            self.state["parameters"][param_name]["current_value"] = current_value
            if test_values:
                self.state["parameters"][param_name]["test_values"] = test_values
        
        self._save_state()
    
    def record_outcome(self, param_name: str, param_value: float, 
                      pnl_pct: float, win: bool):
        """
        Record outcome for a parameter value.
        
        Args:
            param_name: Parameter name
            param_value: Value that was used
            pnl_pct: P&L percentage
            win: Whether trade was a win
        """
        if param_name not in self.state["parameters"]:
            return
        
        param = self.state["parameters"][param_name]
        value_key = str(round(param_value, 6))
        
        if value_key not in param["outcomes"]:
            param["outcomes"][value_key] = {
                "pnl_sum": 0.0,
                "wins": 0,
                "losses": 0,
                "samples": 0
            }
        
        outcome = param["outcomes"][value_key]
        outcome["pnl_sum"] += pnl_pct
        outcome["samples"] += 1
        if win:
            outcome["wins"] += 1
        else:
            outcome["losses"] += 1
        
        # Update optimal value if we have enough samples
        if outcome["samples"] >= 10:
            self._update_optimal_value(param_name)
        
        self._save_state()
    
    def _update_optimal_value(self, param_name: str):
        """Update optimal value for a parameter based on outcomes"""
        param = self.state["parameters"][param_name]
        
        best_value = param["current_value"]
        best_score = float('-inf')
        
        for value_str, outcome in param["outcomes"].items():
            if outcome["samples"] < 10:  # Need minimum samples
                continue
            
            win_rate = outcome["wins"] / outcome["samples"] if outcome["samples"] > 0 else 0
            avg_pnl = outcome["pnl_sum"] / outcome["samples"] if outcome["samples"] > 0 else 0
            
            # Score = win_rate * 0.6 + (avg_pnl > 0) * 0.4
            score = win_rate * 0.6 + (1 if avg_pnl > 0 else 0) * 0.4
            
            if score > best_score:
                best_score = score
                try:
                    best_value = float(value_str)
                except:
                    pass
        
        if best_value != param["optimal_value"]:
            param["optimal_value"] = best_value
            param["last_optimized"] = datetime.now(timezone.utc).isoformat()
    
    def get_optimal_value(self, param_name: str) -> Optional[float]:
        """Get optimal value for a parameter"""
        if param_name not in self.state["parameters"]:
            return None
        
        param = self.state["parameters"][param_name]
        optimal = param.get("optimal_value")
        
        # Only return if we have enough data
        total_samples = sum(outcome["samples"] for outcome in param["outcomes"].values())
        if total_samples < 30:  # Need minimum samples across all values
            return None
        
        return optimal
    
    def get_all_optimizations(self) -> Dict[str, float]:
        """Get all parameter optimizations"""
        optimizations = {}
        for param_name, param in self.state["parameters"].items():
            optimal = self.get_optimal_value(param_name)
            if optimal is not None:
                optimizations[param_name] = optimal
        return optimizations

# Global instance
_optimizer_instance = None

def get_parameter_optimizer() -> ParameterOptimizer:
    """Get global parameter optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = ParameterOptimizer()
    return _optimizer_instance
