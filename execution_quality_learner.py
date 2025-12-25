#!/usr/bin/env python3
"""
Execution Quality Learner
Learns from order execution patterns to optimize execution strategy.
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

STATE_DIR = Path("state")
EXECUTION_QUALITY_STATE = STATE_DIR / "execution_quality_learning.json"

class ExecutionQualityLearner:
    """Learns optimal execution strategies from order patterns."""
    
    def __init__(self):
        self.state_file = EXECUTION_QUALITY_STATE
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load learning state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "order_patterns": {},  # strategy -> {slippage_avg, fill_rate, sample_count}
            "symbol_patterns": {},  # symbol -> {best_strategy, avg_slippage}
            "regime_patterns": {},  # regime -> {best_strategy, avg_slippage}
            "last_updated": None
        }
    
    def _save_state(self):
        """Save learning state"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2)
    
    def record_order_execution(self, symbol: str, strategy: str, regime: str,
                             slippage_pct: float, filled: bool, fill_time_sec: float = None):
        """
        Record order execution for learning.
        
        Args:
            symbol: Symbol traded
            strategy: Execution strategy used (e.g., "limit_offset", "market")
            regime: Market regime
            slippage_pct: Slippage percentage
            filled: Whether order was filled
            fill_time_sec: Time to fill in seconds (optional)
        """
        # Update strategy patterns
        if strategy not in self.state["order_patterns"]:
            self.state["order_patterns"][strategy] = {
                "slippage_sum": 0.0,
                "slippage_count": 0,
                "fills": 0,
                "attempts": 0
            }
        
        pattern = self.state["order_patterns"][strategy]
        pattern["attempts"] += 1
        if filled:
            pattern["fills"] += 1
            pattern["slippage_sum"] += slippage_pct
            pattern["slippage_count"] += 1
        
        # Update symbol patterns
        if symbol not in self.state["symbol_patterns"]:
            self.state["symbol_patterns"][symbol] = {
                "strategies": {},
                "best_strategy": None
            }
        
        if strategy not in self.state["symbol_patterns"][symbol]["strategies"]:
            self.state["symbol_patterns"][symbol]["strategies"][strategy] = {
                "slippage_avg": 0.0,
                "fill_rate": 0.0,
                "samples": 0
            }
        
        sym_strat = self.state["symbol_patterns"][symbol]["strategies"][strategy]
        sym_strat["samples"] += 1
        if filled:
            # Update running average
            current_avg = sym_strat["slippage_avg"]
            n = sym_strat["samples"]
            sym_strat["slippage_avg"] = (current_avg * (n - 1) + slippage_pct) / n
            sym_strat["fill_rate"] = sym_strat.get("fills", 0) / n
        
        # Update regime patterns
        if regime not in self.state["regime_patterns"]:
            self.state["regime_patterns"][regime] = {
                "strategies": {},
                "best_strategy": None
            }
        
        if strategy not in self.state["regime_patterns"][regime]["strategies"]:
            self.state["regime_patterns"][regime]["strategies"][strategy] = {
                "slippage_avg": 0.0,
                "fill_rate": 0.0,
                "samples": 0
            }
        
        reg_strat = self.state["regime_patterns"][regime]["strategies"][strategy]
        reg_strat["samples"] += 1
        if filled:
            current_avg = reg_strat["slippage_avg"]
            n = reg_strat["samples"]
            reg_strat["slippage_avg"] = (current_avg * (n - 1) + slippage_pct) / n
            reg_strat["fill_rate"] = reg_strat.get("fills", 0) / n
        
        # Update best strategies (every 10 samples)
        if sym_strat["samples"] % 10 == 0:
            self._update_best_strategies()
        
        self._save_state()
    
    def _update_best_strategies(self):
        """Update best strategy recommendations based on learned patterns"""
        # Update symbol best strategies
        for symbol, sym_data in self.state["symbol_patterns"].items():
            best_strategy = None
            best_score = float('inf')
            
            for strategy, stats in sym_data["strategies"].items():
                if stats["samples"] < 5:  # Need minimum samples
                    continue
                
                # Score = slippage + (1 - fill_rate) * 0.01
                # Lower is better
                score = stats["slippage_avg"] + (1 - stats["fill_rate"]) * 0.01
                if score < best_score:
                    best_score = score
                    best_strategy = strategy
            
            if best_strategy:
                sym_data["best_strategy"] = best_strategy
        
        # Update regime best strategies
        for regime, reg_data in self.state["regime_patterns"].items():
            best_strategy = None
            best_score = float('inf')
            
            for strategy, stats in reg_data["strategies"].items():
                if stats["samples"] < 5:
                    continue
                
                score = stats["slippage_avg"] + (1 - stats["fill_rate"]) * 0.01
                if score < best_score:
                    best_score = score
                    best_strategy = strategy
            
            if best_strategy:
                reg_data["best_strategy"] = best_strategy
    
    def get_recommended_strategy(self, symbol: str, regime: str) -> Optional[str]:
        """
        Get recommended execution strategy based on learned patterns.
        
        Returns:
            Recommended strategy name, or None if not enough data
        """
        # Prefer symbol-specific, fallback to regime-specific, then global
        sym_data = self.state["symbol_patterns"].get(symbol, {})
        if sym_data.get("best_strategy") and sym_data["strategies"].get(sym_data["best_strategy"], {}).get("samples", 0) >= 5:
            return sym_data["best_strategy"]
        
        reg_data = self.state["regime_patterns"].get(regime, {})
        if reg_data.get("best_strategy") and reg_data["strategies"].get(reg_data["best_strategy"], {}).get("samples", 0) >= 5:
            return reg_data["best_strategy"]
        
        # Global best
        best_strategy = None
        best_score = float('inf')
        for strategy, pattern in self.state["order_patterns"].items():
            if pattern["attempts"] < 10:
                continue
            fill_rate = pattern["fills"] / pattern["attempts"] if pattern["attempts"] > 0 else 0
            slippage_avg = pattern["slippage_sum"] / pattern["slippage_count"] if pattern["slippage_count"] > 0 else 0.01
            score = slippage_avg + (1 - fill_rate) * 0.01
            if score < best_score:
                best_score = score
                best_strategy = strategy
        
        return best_strategy

# Global instance
_learner_instance = None

def get_execution_learner() -> ExecutionQualityLearner:
    """Get global execution quality learner instance"""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = ExecutionQualityLearner()
    return _learner_instance

