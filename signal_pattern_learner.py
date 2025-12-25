#!/usr/bin/env python3
"""
Signal Pattern Learner
Learns which signal combinations and patterns lead to better outcomes.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from collections import defaultdict
import hashlib

STATE_DIR = Path("state")
SIGNAL_PATTERN_STATE = STATE_DIR / "signal_pattern_learning.json"

class SignalPatternLearner:
    """Learns optimal signal combinations from historical patterns."""
    
    def __init__(self):
        self.state_file = SIGNAL_PATTERN_STATE
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
            "signal_combinations": {},  # combination_hash -> {wins, losses, pnl_sum, samples}
            "component_patterns": {},  # component -> {context -> {wins, losses, pnl}}
            "timing_patterns": {},  # time_of_day -> {wins, losses, pnl}
            "last_updated": None
        }
    
    def _save_state(self):
        """Save learning state"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2)
    
    def _hash_combination(self, components: Dict) -> str:
        """Create hash of signal combination"""
        # Sort components by name for consistent hashing
        sorted_comps = sorted([(k, round(v, 4)) for k, v in components.items() if v != 0])
        comp_str = json.dumps(sorted_comps, sort_keys=True)
        return hashlib.md5(comp_str.encode()).hexdigest()[:16]
    
    def record_signal(self, signal_id: str, symbol: str, components: Dict, score: float):
        """
        Record signal generation for pattern learning.
        
        Args:
            signal_id: Unique signal ID
            symbol: Symbol
            components: Signal components dict
            score: Composite score
        """
        # Hash combination
        combo_hash = self._hash_combination(components)
        
        # Update combination patterns
        if combo_hash not in self.state["signal_combinations"]:
            self.state["signal_combinations"][combo_hash] = {
                "components": components,
                "wins": 0,
                "losses": 0,
                "pnl_sum": 0.0,
                "samples": 0,
                "avg_score": 0.0
            }
        
        combo = self.state["signal_combinations"][combo_hash]
        combo["samples"] += 1
        # Update running average score
        n = combo["samples"]
        combo["avg_score"] = (combo["avg_score"] * (n - 1) + score) / n
        
        # Update component patterns
        for comp_name, comp_value in components.items():
            if comp_value == 0:
                continue
            
            if comp_name not in self.state["component_patterns"]:
                self.state["component_patterns"][comp_name] = {}
            
            # Categorize value (low/medium/high)
            abs_value = abs(comp_value)
            if abs_value < 0.3:
                category = "low"
            elif abs_value < 0.7:
                category = "medium"
            else:
                category = "high"
            
            if category not in self.state["component_patterns"][comp_name]:
                self.state["component_patterns"][comp_name][category] = {
                    "wins": 0,
                    "losses": 0,
                    "pnl_sum": 0.0,
                    "samples": 0
                }
            
            # Will be updated when trade outcome is known
            self.state["component_patterns"][comp_name][category]["samples"] += 1
        
        self._save_state()
    
    def record_signal_outcome(self, signal_id: str, pnl_pct: float, win: bool):
        """
        Record outcome for a signal (called when trade closes).
        
        Args:
            signal_id: Signal ID (must match record_signal call)
            pnl_pct: P&L percentage
            win: Whether trade was a win
        """
        # Find signal combination by looking up in attribution log
        # For now, we'll update patterns when we process attribution log
        # This is a placeholder - full implementation would track signal_id -> combo_hash mapping
        pass
    
    def get_best_combinations(self, limit: int = 10) -> List[Dict]:
        """
        Get best performing signal combinations.
        
        Returns:
            List of combination dicts sorted by performance
        """
        combinations = []
        for combo_hash, combo_data in self.state["signal_combinations"].items():
            if combo_data["samples"] < 5:  # Need minimum samples
                continue
            
            win_rate = combo_data["wins"] / combo_data["samples"] if combo_data["samples"] > 0 else 0
            avg_pnl = combo_data["pnl_sum"] / combo_data["samples"] if combo_data["samples"] > 0 else 0
            
            # Performance score = win_rate * 0.6 + (avg_pnl > 0) * 0.4
            performance_score = win_rate * 0.6 + (1 if avg_pnl > 0 else 0) * 0.4
            
            combinations.append({
                "hash": combo_hash,
                "components": combo_data["components"],
                "win_rate": win_rate,
                "avg_pnl": avg_pnl,
                "samples": combo_data["samples"],
                "performance_score": performance_score
            })
        
        # Sort by performance score
        combinations.sort(key=lambda x: x["performance_score"], reverse=True)
        return combinations[:limit]

# Global instance
_learner_instance = None

def get_signal_pattern_learner() -> SignalPatternLearner:
    """Get global signal pattern learner instance"""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = SignalPatternLearner()
    return _learner_instance

