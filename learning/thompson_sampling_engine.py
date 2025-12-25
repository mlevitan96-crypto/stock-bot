#!/usr/bin/env python3
"""
Anti-Overfitting Learning Engine: Thompson Sampling
Replaces manual weight adjustments with Thompson Sampling using Beta distributions.
Only finalizes weight changes when Wilson confidence intervals exceed 95%.
"""

import json
import math
import random
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Optional numpy import
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

STATE_DIR = Path("state")
THOMPSON_STATE_FILE = STATE_DIR / "thompson_sampling_state.json"

# Wilson confidence interval calculation
def wilson_confidence_interval(successes: int, trials: int, z: float = 1.96) -> Tuple[float, float]:
    """
    Calculate Wilson confidence interval.
    z = 1.96 for 95% confidence
    Returns: (lower_bound, upper_bound)
    """
    if trials == 0:
        return (0.0, 1.0)
    
    p = successes / trials
    denominator = 1 + (z**2 / trials)
    center = (p + (z**2 / (2 * trials))) / denominator
    margin = (z / denominator) * math.sqrt((p * (1 - p) / trials) + (z**2 / (4 * trials**2)))
    
    return (max(0.0, center - margin), min(1.0, center + margin))

class ThompsonSamplingEngine:
    """Thompson Sampling engine for signal component weight optimization."""
    
    def __init__(self):
        self.state_file = THOMPSON_STATE_FILE
        self.components = {}  # Component name -> Beta distribution params
        self.weight_history = {}  # Component name -> list of (weight, outcome) tuples
        self._load_state()
    
    def _load_state(self):
        """Load Thompson Sampling state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.components = data.get("components", {})
                    self.weight_history = data.get("weight_history", {})
            except:
                pass
    
    def _save_state(self):
        """Save Thompson Sampling state"""
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                "components": self.components,
                "weight_history": self.weight_history,
                "last_update": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)
    
    def register_component(self, component_name: str, initial_weight: float = 1.0):
        """Register a signal component for Thompson Sampling"""
        if component_name not in self.components:
            # Initialize Beta distribution: Beta(alpha=1, beta=1) = uniform
            # We'll use alpha for successes, beta for failures
            self.components[component_name] = {
                "alpha": 1.0,  # Successes
                "beta": 1.0,   # Failures
                "current_weight": initial_weight,
                "proposed_weight": initial_weight,
                "trials": 0,
                "successes": 0,
                "last_confidence": (0.0, 1.0)
            }
            self.weight_history[component_name] = []
            self._save_state()
    
    def sample_weight(self, component_name: str) -> float:
        """
        Sample a weight from Beta distribution using Thompson Sampling.
        Returns: sampled weight (0.25 to 2.5 range)
        """
        if component_name not in self.components:
            self.register_component(component_name)
        
        comp = self.components[component_name]
        alpha = comp["alpha"]
        beta = comp["beta"]
        
        # Sample from Beta distribution
        try:
            # Use numpy if available
            if HAS_NUMPY and hasattr(np.random, 'beta'):
                sample = np.random.beta(alpha, beta)
            else:
                # Simple approximation using uniform random
                # Beta(alpha, beta) approximation: use alpha/(alpha+beta) as mean
                mean = alpha / (alpha + beta) if (alpha + beta) > 0 else 0.5
                # Add some randomness around the mean
                sample = max(0.0, min(1.0, mean + (random.random() - 0.5) * 0.2))
        except:
            # Fallback to uniform
            sample = 0.5
        
        # Map [0, 1] to [0.25, 2.5] weight range
        weight = 0.25 + sample * 2.25
        
        # Store as proposed weight
        comp["proposed_weight"] = weight
        
        return weight
    
    def record_outcome(self, component_name: str, weight_used: float, pnl_pct: float, 
                      success_threshold: float = 0.0):
        """
        Record outcome for a component weight.
        success_threshold: P&L threshold to consider a success (default: >0)
        """
        if component_name not in self.components:
            self.register_component(component_name)
        
        comp = self.components[component_name]
        is_success = pnl_pct > success_threshold
        
        # Update Beta distribution
        if is_success:
            comp["alpha"] += 1.0
            comp["successes"] += 1
        else:
            comp["beta"] += 1.0
        
        comp["trials"] += 1
        
        # Record in history
        if component_name not in self.weight_history:
            self.weight_history[component_name] = []
        
        self.weight_history[component_name].append({
            "weight": weight_used,
            "pnl_pct": pnl_pct,
            "success": is_success,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Keep only last 1000 records
        if len(self.weight_history[component_name]) > 1000:
            self.weight_history[component_name] = self.weight_history[component_name][-1000:]
        
        self._save_state()
    
    def should_finalize_weight(self, component_name: str, confidence_level: float = 0.95) -> bool:
        """
        Check if weight change should be finalized based on Wilson confidence interval.
        confidence_level: Required confidence (default: 0.95 = 95%)
        """
        if component_name not in self.components:
            return False
        
        comp = self.components[component_name]
        trials = comp["trials"]
        successes = comp["successes"]
        
        if trials < 30:  # Minimum trials required
            return False
        
        # Calculate Wilson confidence interval
        z = 1.96 if confidence_level == 0.95 else 2.576 if confidence_level == 0.99 else 1.645
        lower, upper = wilson_confidence_interval(successes, trials, z)
        
        comp["last_confidence"] = (lower, upper)
        
        # Finalize if confidence interval is tight enough
        # (upper - lower) < 0.2 means we're confident
        confidence_width = upper - lower
        
        if confidence_width < 0.2 and trials >= 30:
            return True
        
        return False
    
    def finalize_weight(self, component_name: str):
        """Finalize proposed weight as current weight"""
        if component_name not in self.components:
            return
        
        comp = self.components[component_name]
        comp["current_weight"] = comp["proposed_weight"]
        self._save_state()
    
    def get_optimal_weight(self, component_name: str) -> float:
        """Get current optimal weight for a component"""
        if component_name not in self.components:
            self.register_component(component_name)
        
        comp = self.components[component_name]
        
        # If we have enough confidence, use current weight
        if self.should_finalize_weight(component_name):
            return comp["current_weight"]
        
        # Otherwise, sample new weight
        return self.sample_weight(component_name)
    
    def get_all_weights(self) -> Dict[str, float]:
        """Get all current optimal weights"""
        weights = {}
        for component_name in self.components.keys():
            weights[component_name] = self.get_optimal_weight(component_name)
        return weights
    
    def get_component_stats(self, component_name: str) -> Dict:
        """Get statistics for a component"""
        if component_name not in self.components:
            return {}
        
        comp = self.components[component_name]
        trials = comp["trials"]
        successes = comp["successes"]
        win_rate = successes / trials if trials > 0 else 0.0
        
        lower, upper = comp.get("last_confidence", (0.0, 1.0))
        
        return {
            "current_weight": comp["current_weight"],
            "proposed_weight": comp["proposed_weight"],
            "trials": trials,
            "successes": successes,
            "win_rate": win_rate,
            "confidence_interval": (lower, upper),
            "alpha": comp["alpha"],
            "beta": comp["beta"]
        }

# Global instance
_thompson_engine = None

def get_thompson_engine() -> ThompsonSamplingEngine:
    """Get global Thompson Sampling engine instance"""
    global _thompson_engine
    if _thompson_engine is None:
        _thompson_engine = ThompsonSamplingEngine()
    return _thompson_engine

