#!/usr/bin/env python3
"""
Comprehensive Learning Orchestrator
====================================
Coordinates all learning components for maximum profitability improvement.

Features:
- Counterfactual analysis (what-if scenarios)
- Weight variation testing (percentage-based, not just on/off)
- Timing optimization (entry/exit timing)
- Sizing optimization (position sizing)
- Self-healing and health monitoring
- Automatic retry and error recovery
"""

import os
import json
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import re

DATA_DIR = Path("data")
STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

LEARNING_STATE_FILE = STATE_DIR / "comprehensive_learning_state.json"
LEARNING_LOG_FILE = DATA_DIR / "comprehensive_learning.jsonl"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [LEARNING-ORCH] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "comprehensive_learning.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class WeightVariation:
    """Represents a weight variation to test"""
    component: str
    base_weight: float
    variation_pct: float  # -50% to +50%
    effective_weight: float
    test_count: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0


@dataclass
class TimingScenario:
    """Represents a timing scenario to test"""
    entry_delay_min: int  # Minutes after signal
    exit_duration_min: int  # Hold duration
    test_count: int = 0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    win_rate: float = 0.0


@dataclass
class SizingScenario:
    """Represents a sizing scenario to test"""
    size_multiplier: float  # 0.5x to 2.0x base size
    confidence_threshold: float
    test_count: int = 0
    total_pnl: float = 0.0
    sharpe_ratio: float = 0.0


@dataclass
class ExitThresholdScenario:
    """Represents an exit threshold scenario to test"""
    trail_stop_pct: float  # 1.0%, 1.5%, 2.0%, 2.5%
    time_exit_minutes: int  # 180, 240, 300, 360
    stale_days: int  # 10, 12, 14
    test_count: int = 0
    total_pnl: float = 0.0
    weighted_pnl: float = 0.0
    total_weight: float = 0.0
    wins: int = 0
    losses: int = 0
    avg_hold_minutes: float = 0.0


@dataclass
class ProfitTargetScenario:
    """Represents a profit target & scale-out scenario to test"""
    targets: List[float]  # e.g., [0.02, 0.05, 0.10] (2%, 5%, 10%)
    scale_fractions: List[float]  # e.g., [0.3, 0.3, 0.4] (30%, 30%, 40%)
    test_count: int = 0
    total_pnl: float = 0.0
    weighted_pnl: float = 0.0
    total_weight: float = 0.0
    targets_hit: int = 0  # How many targets were hit on average
    avg_pnl_per_target: float = 0.0


class ComprehensiveLearningOrchestrator:
    """Orchestrates all learning components for continuous improvement."""
    
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_run_ts = 0
        self.error_count = 0
        self.success_count = 0
        
        # Learning components
        self.counterfactual_analyzer = None
        self.weight_variations: Dict[str, List[WeightVariation]] = {}
        self.timing_scenarios: List[TimingScenario] = []
        self.sizing_scenarios: List[SizingScenario] = []
        self.exit_threshold_scenarios: List[ExitThresholdScenario] = []
        self.profit_target_scenarios: List[ProfitTargetScenario] = []
        self.exit_signal_performance: Dict[str, Dict[str, Any]] = {}  # Track exit signal performance
        
        # State
        self.state = self._load_state()
        self._init_components()
        self._init_scenarios()
    
    def _init_components(self):
        """Initialize learning components."""
        try:
            from counterfactual_analyzer import CounterfactualAnalyzer
            self.counterfactual_analyzer = CounterfactualAnalyzer()
            logger.info("Counterfactual analyzer initialized")
        except Exception as e:
            logger.warning(f"Counterfactual analyzer not available: {e}")
    
    def _init_scenarios(self):
        """Initialize test scenarios."""
        # Weight variations: test -50%, -25%, +25%, +50% for each component
        from adaptive_signal_optimizer import SIGNAL_COMPONENTS
        
        for component in SIGNAL_COMPONENTS:
            variations = []
            for pct in [-50, -25, 0, 25, 50]:
                variations.append(WeightVariation(
                    component=component,
                    base_weight=1.0,
                    variation_pct=pct,
                    effective_weight=1.0 * (1 + pct / 100.0)
                ))
            self.weight_variations[component] = variations
        
        # Timing scenarios: test different entry delays and hold durations
        self.timing_scenarios = [
            TimingScenario(entry_delay_min=0, exit_duration_min=60),   # Immediate entry, 1h hold
            TimingScenario(entry_delay_min=5, exit_duration_min=120),  # 5min delay, 2h hold
            TimingScenario(entry_delay_min=15, exit_duration_min=240), # 15min delay, 4h hold
            TimingScenario(entry_delay_min=30, exit_duration_min=480), # 30min delay, 8h hold
        ]
        
        # Exit threshold scenarios: test different trail stops and time exits
        self.exit_threshold_scenarios = [
            ExitThresholdScenario(trail_stop_pct=0.010, time_exit_minutes=180, stale_days=10),  # Tighter, shorter
            ExitThresholdScenario(trail_stop_pct=0.015, time_exit_minutes=240, stale_days=12),  # Current
            ExitThresholdScenario(trail_stop_pct=0.020, time_exit_minutes=300, stale_days=14),  # Looser, longer
            ExitThresholdScenario(trail_stop_pct=0.025, time_exit_minutes=360, stale_days=16),  # Very loose, very long
        ]
        
        # Profit target scenarios: test different profit targets and scale-out fractions
        self.profit_target_scenarios = [
            ProfitTargetScenario(targets=[0.015, 0.04, 0.08], scale_fractions=[0.25, 0.35, 0.40]),  # More conservative
            ProfitTargetScenario(targets=[0.02, 0.05, 0.10], scale_fractions=[0.30, 0.30, 0.40]),  # Current
            ProfitTargetScenario(targets=[0.025, 0.06, 0.12], scale_fractions=[0.35, 0.35, 0.30]),  # More aggressive
            ProfitTargetScenario(targets=[0.03, 0.08, 0.15], scale_fractions=[0.40, 0.30, 0.30]),  # Very aggressive
        ]
        
        # Sizing scenarios: test different size multipliers
        self.sizing_scenarios = [
            SizingScenario(size_multiplier=0.5, confidence_threshold=0.6),
            SizingScenario(size_multiplier=0.75, confidence_threshold=0.7),
            SizingScenario(size_multiplier=1.0, confidence_threshold=0.5),
            SizingScenario(size_multiplier=1.25, confidence_threshold=0.8),
            SizingScenario(size_multiplier=1.5, confidence_threshold=0.9),
            SizingScenario(size_multiplier=2.0, confidence_threshold=0.95),
        ]
    
    def run_counterfactual_analysis(self) -> Dict[str, Any]:
        """Run counterfactual analysis on blocked trades."""
        if not self.counterfactual_analyzer:
            return {"status": "skipped", "reason": "analyzer_not_available"}
        
        try:
            results = self.counterfactual_analyzer.process_blocked_trades(lookback_hours=24)
            logger.info(f"Counterfactual analysis: {results}")
            return {"status": "success", "results": results}
        except Exception as e:
            logger.error(f"Counterfactual analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _exponential_decay_weight(self, trade_age_days: float, halflife_days: float = 30.0) -> float:
        """Calculate exponential decay weight for a trade based on age."""
        import math
        return math.exp(-trade_age_days / (halflife_days / math.log(2)))
    
    def analyze_weight_variations(self) -> Dict[str, Any]:
        """
        Analyze how different weight variations perform.
        Tests percentage-based variations, not just on/off.
        Uses cumulative learning with exponential decay weighting.
        """
        try:
            from adaptive_signal_optimizer import get_optimizer
            optimizer = get_optimizer()
            if not optimizer:
                return {"status": "skipped", "reason": "optimizer_not_available"}
            
            # Read all trades (cumulative, not just recent)
            # Attribution is written to logs/ by main.py jsonl_write function
            attribution_file = LOGS_DIR / "attribution.jsonl"
            if not attribution_file.exists():
                return {"status": "skipped", "reason": "no_trades"}
            
            now = datetime.now(timezone.utc)
            max_age_days = 90  # Look back 90 days max
            
            # Analyze each weight variation with exponential decay
            variation_results = {}
            
            with attribution_file.open("r") as f:
                lines = f.readlines()
            
            # Process ALL trades with exponential decay weighting
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
                    
                    # Calculate trade age and decay weight
                    trade_age_days = (now - trade_time).total_seconds() / 86400.0
                    if trade_age_days > max_age_days:
                        continue
                    
                    # Exponential decay: recent trades weighted more, but all count
                    decay_weight = self._exponential_decay_weight(trade_age_days, halflife_days=30.0)
                    
                    components = trade.get("context", {}).get("components", {})
                    pnl = float(trade.get("pnl_usd", 0.0))
                    
                    # For each component, test how different weight variations would have performed
                    for component, value in components.items():
                        if component not in self.weight_variations:
                            continue
                        
                        if component not in variation_results:
                            variation_results[component] = {}
                        
                        # Test each variation with cumulative, time-weighted learning
                        for variation in self.weight_variations[component]:
                            var_key = f"{variation.variation_pct}%"
                            if var_key not in variation_results[component]:
                                variation_results[component][var_key] = {
                                    "test_count": 0,
                                    "total_pnl": 0.0,
                                    "weighted_pnl": 0.0,  # Cumulative with decay
                                    "total_weight": 0.0,
                                    "wins": 0,
                                    "losses": 0
                                }
                            
                            # Simulate P&L with this weight variation
                            # P&L scales with weight (higher weight = more impact)
                            simulated_pnl = pnl * (variation.effective_weight / 1.0)
                            
                            var_result = variation_results[component][var_key]
                            var_result["test_count"] += 1
                            var_result["total_pnl"] += simulated_pnl
                            
                            # Apply exponential decay weight for cumulative learning
                            var_result["weighted_pnl"] += simulated_pnl * decay_weight
                            var_result["total_weight"] += decay_weight
                            
                            if simulated_pnl > 0:
                                var_result["wins"] += 1
                            else:
                                var_result["losses"] += 1
                
                except Exception as e:
                    logger.debug(f"Error analyzing trade: {e}")
                    continue
            
            # Find best variations using weighted P&L (cumulative with decay)
            best_variations = {}
            for component, variations in variation_results.items():
                best_var = None
                best_weighted_avg_pnl = float('-inf')
                
                for var_key, result in variations.items():
                    if result["test_count"] < 30:  # Minimum 30 samples for statistical significance
                        continue
                    
                    # Use weighted average (recent trades matter more, but all count)
                    if result["total_weight"] > 0:
                        weighted_avg_pnl = result["weighted_pnl"] / result["total_weight"]
                    else:
                        weighted_avg_pnl = result["total_pnl"] / result["test_count"]
                    
                    if weighted_avg_pnl > best_weighted_avg_pnl:
                        best_weighted_avg_pnl = weighted_avg_pnl
                        best_var = var_key
                
                if best_var:
                    pct = float(best_var.replace("%", ""))
                    best_variations[component] = pct
            
            # Apply best variations (gradual update, not instant)
            if best_variations:
                self._apply_weight_variations(best_variations)
            
            return {
                "status": "success",
                "variations_tested": len(variation_results),
                "best_variations": best_variations
            }
            
        except Exception as e:
            logger.error(f"Weight variation analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _apply_weight_variations(self, best_variations: Dict[str, float]):
        """Apply best weight variations gradually."""
        try:
            from adaptive_signal_optimizer import get_optimizer
            optimizer = get_optimizer()
            if not optimizer:
                return
            
            # Get current weights
            current_weights = optimizer.get_weights_for_composite()
            
            # Apply variations gradually (10% per update to avoid overfitting)
            for component, pct_change in best_variations.items():
                if component not in current_weights:
                    continue
                
                current = current_weights[component]
                target = current * (1 + pct_change / 100.0)
                
                # Gradual update: move 10% toward target
                new_weight = current + (target - current) * 0.1
                
                # Update via optimizer (would need to add method for this)
                logger.info(f"Updating {component} weight: {current:.3f} -> {new_weight:.3f} (target: {target:.3f})")
        
        except Exception as e:
            logger.warning(f"Error applying weight variations: {e}")
    
    def analyze_timing_scenarios(self) -> Dict[str, Any]:
        """Analyze optimal entry/exit timing with cumulative, time-weighted learning."""
        try:
            attribution_file = DATA_DIR / "attribution.jsonl"
            if not attribution_file.exists():
                return {"status": "skipped", "reason": "no_trades"}
            
            scenario_results = {}
            now = datetime.now(timezone.utc)
            max_age_days = 60  # Look back 60 days for timing analysis
            
            with attribution_file.open("r") as f:
                lines = f.readlines()
            
            # Process ALL trades with exponential decay
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
                    if trade_age_days > max_age_days:
                        continue
                    
                    decay_weight = self._exponential_decay_weight(trade_age_days, halflife_days=30.0)
                    
                    context = trade.get("context", {})
                    hold_minutes = context.get("hold_minutes", 0)
                    pnl = float(trade.get("pnl_usd", 0.0))
                    
                    # Match to closest timing scenario
                    for scenario in self.timing_scenarios:
                        if abs(hold_minutes - scenario.exit_duration_min) < 60:  # Within 1 hour
                            scenario_key = f"{scenario.entry_delay_min}m_delay_{scenario.exit_duration_min}m_hold"
                            
                            if scenario_key not in scenario_results:
                                scenario_results[scenario_key] = {
                                    "test_count": 0,
                                    "total_pnl": 0.0,
                                    "weighted_pnl": 0.0,
                                    "total_weight": 0.0,
                                    "wins": 0,
                                    "losses": 0
                                }
                            
                            result = scenario_results[scenario_key]
                            result["test_count"] += 1
                            result["total_pnl"] += pnl
                            result["weighted_pnl"] += pnl * decay_weight
                            result["total_weight"] += decay_weight
                            if pnl > 0:
                                result["wins"] += 1
                            else:
                                result["losses"] += 1
                
                except Exception as e:
                    logger.debug(f"Error analyzing timing: {e}")
                    continue
            
            # Find best timing scenario using weighted average
            best_scenario = None
            best_weighted_avg_pnl = float('-inf')
            
            for scenario_key, result in scenario_results.items():
                if result["test_count"] < 20:  # Minimum 20 samples
                    continue
                
                # Use weighted average (cumulative with decay)
                if result["total_weight"] > 0:
                    weighted_avg_pnl = result["weighted_pnl"] / result["total_weight"]
                else:
                    weighted_avg_pnl = result["total_pnl"] / result["test_count"]
                
                if weighted_avg_pnl > best_weighted_avg_pnl:
                    best_weighted_avg_pnl = weighted_avg_pnl
                    best_scenario = scenario_key
            
            return {
                "status": "success",
                "scenarios_tested": len(scenario_results),
                "best_scenario": best_scenario,
                "best_weighted_avg_pnl": round(best_weighted_avg_pnl, 2) if best_weighted_avg_pnl != float('-inf') else None
            }
            
        except Exception as e:
            logger.error(f"Timing analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def analyze_sizing_scenarios(self) -> Dict[str, Any]:
        """Analyze optimal position sizing with cumulative, time-weighted learning."""
        try:
            attribution_file = DATA_DIR / "attribution.jsonl"
            if not attribution_file.exists():
                return {"status": "skipped", "reason": "no_trades"}
            
            scenario_results = {}
            now = datetime.now(timezone.utc)
            max_age_days = 60  # Look back 60 days for sizing analysis
            
            with attribution_file.open("r") as f:
                lines = f.readlines()
            
            # Process ALL trades with exponential decay
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
                    if trade_age_days > max_age_days:
                        continue
                    
                    decay_weight = self._exponential_decay_weight(trade_age_days, halflife_days=30.0)
                    
                    context = trade.get("context", {})
                    entry_score = context.get("entry_score", 0.0)
                    pnl = float(trade.get("pnl_usd", 0.0))
                    qty = context.get("qty", 1)
                    
                    # Match to sizing scenario based on confidence (entry_score)
                    for scenario in self.sizing_scenarios:
                        if entry_score >= scenario.confidence_threshold:
                            scenario_key = f"{scenario.size_multiplier}x_{scenario.confidence_threshold}conf"
                            
                            if scenario_key not in scenario_results:
                                scenario_results[scenario_key] = {
                                    "test_count": 0,
                                    "total_pnl": 0.0,
                                    "weighted_pnl": 0.0,
                                    "total_weight": 0.0,
                                    "total_shares": 0,
                                    "pnl_per_share": 0.0
                                }
                            
                            result = scenario_results[scenario_key]
                            result["test_count"] += 1
                            result["total_pnl"] += pnl
                            result["weighted_pnl"] += pnl * decay_weight
                            result["total_weight"] += decay_weight
                            result["total_shares"] += qty
                            
                            # Calculate weighted pnl per share
                            if result["total_weight"] > 0 and result["total_shares"] > 0:
                                result["pnl_per_share"] = result["weighted_pnl"] / result["total_weight"] / result["total_shares"]
                
                except Exception as e:
                    logger.debug(f"Error analyzing sizing: {e}")
                    continue
            
            # Find best sizing scenario using weighted metrics
            best_scenario = None
            best_weighted_pnl_per_share = float('-inf')
            
            for scenario_key, result in scenario_results.items():
                if result["test_count"] < 15:  # Minimum 15 samples
                    continue
                
                if result["pnl_per_share"] > best_weighted_pnl_per_share:
                    best_weighted_pnl_per_share = result["pnl_per_share"]
                    best_scenario = scenario_key
            
            return {
                "status": "success",
                "scenarios_tested": len(scenario_results),
                "best_scenario": best_scenario,
                "best_weighted_pnl_per_share": round(best_weighted_pnl_per_share, 2) if best_weighted_pnl_per_share != float('-inf') else None
            }
            
        except Exception as e:
            logger.error(f"Sizing analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def analyze_exit_thresholds(self) -> Dict[str, Any]:
        """Analyze optimal exit thresholds (trail stop %, time exit minutes) with cumulative learning."""
        try:
            attribution_file = DATA_DIR / "attribution.jsonl"
            if not attribution_file.exists():
                return {"status": "skipped", "reason": "no_trades"}
            
            scenario_results = {}
            now = datetime.now(timezone.utc)
            max_age_days = 60  # Look back 60 days
            
            with attribution_file.open("r") as f:
                lines = f.readlines()
            
            # Process ALL exits with exponential decay
            for line in lines:
                try:
                    trade = json.loads(line.strip())
                    if trade.get("type") != "attribution":
                        continue
                    
                    context = trade.get("context", {})
                    close_reason = context.get("close_reason", "")
                    if not close_reason or "unknown" in close_reason:
                        continue  # Skip trades without meaningful close reasons
                    
                    ts_str = trade.get("ts", "")
                    if not ts_str:
                        continue
                    
                    trade_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if trade_time.tzinfo is None:
                        trade_time = trade_time.replace(tzinfo=timezone.utc)
                    else:
                        trade_time = trade_time.astimezone(timezone.utc)
                    
                    trade_age_days = (now - trade_time).total_seconds() / 86400.0
                    if trade_age_days > max_age_days:
                        continue
                    
                    decay_weight = self._exponential_decay_weight(trade_age_days, halflife_days=30.0)
                    
                    hold_minutes = context.get("hold_minutes", 0)
                    pnl = float(trade.get("pnl_usd", 0.0))
                    
                    # Extract exit signals from close reason
                    # Format: "time_exit(72h)+trail_stop(-2.5%)+signal_decay(0.65)"
                    exit_signals = self._parse_close_reason(close_reason)
                    
                    # Match to closest threshold scenario
                    for scenario in self.exit_threshold_scenarios:
                        # Check if this exit matches scenario (within tolerance)
                        trail_match = "trail_stop" in exit_signals
                        time_match = "time_exit" in exit_signals and abs(hold_minutes - scenario.time_exit_minutes) < 60
                        
                        if trail_match or time_match:
                            scenario_key = f"trail_{scenario.trail_stop_pct:.3f}_time_{scenario.time_exit_minutes}_stale_{scenario.stale_days}"
                            
                            if scenario_key not in scenario_results:
                                scenario_results[scenario_key] = {
                                    "test_count": 0,
                                    "total_pnl": 0.0,
                                    "weighted_pnl": 0.0,
                                    "total_weight": 0.0,
                                    "wins": 0,
                                    "losses": 0,
                                    "total_hold_minutes": 0.0
                                }
                            
                            result = scenario_results[scenario_key]
                            result["test_count"] += 1
                            result["total_pnl"] += pnl
                            result["weighted_pnl"] += pnl * decay_weight
                            result["total_weight"] += decay_weight
                            result["total_hold_minutes"] += hold_minutes
                            if pnl > 0:
                                result["wins"] += 1
                            else:
                                result["losses"] += 1
                
                except Exception as e:
                    logger.debug(f"Error analyzing exit threshold: {e}")
                    continue
            
            # Find best threshold scenario
            best_scenario = None
            best_weighted_avg_pnl = float('-inf')
            
            for scenario_key, result in scenario_results.items():
                if result["test_count"] < 20:  # Minimum 20 samples
                    continue
                
                if result["total_weight"] > 0:
                    weighted_avg_pnl = result["weighted_pnl"] / result["total_weight"]
                else:
                    weighted_avg_pnl = result["total_pnl"] / result["test_count"]
                
                if weighted_avg_pnl > best_weighted_avg_pnl:
                    best_weighted_avg_pnl = weighted_avg_pnl
                    best_scenario = scenario_key
            
            return {
                "status": "success",
                "scenarios_tested": len(scenario_results),
                "best_scenario": best_scenario,
                "best_weighted_avg_pnl": round(best_weighted_avg_pnl, 2) if best_weighted_avg_pnl != float('-inf') else None
            }
            
        except Exception as e:
            logger.error(f"Exit threshold analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def analyze_close_reason_performance(self) -> Dict[str, Any]:
        """Analyze which exit signals and combinations lead to best P&L outcomes."""
        try:
            attribution_file = DATA_DIR / "attribution.jsonl"
            if not attribution_file.exists():
                return {"status": "skipped", "reason": "no_trades"}
            
            signal_performance = {}
            now = datetime.now(timezone.utc)
            max_age_days = 60
            
            with attribution_file.open("r") as f:
                lines = f.readlines()
            
            # Process ALL exits
            for line in lines:
                try:
                    trade = json.loads(line.strip())
                    if trade.get("type") != "attribution":
                        continue
                    
                    context = trade.get("context", {})
                    close_reason = context.get("close_reason", "")
                    if not close_reason or "unknown" in close_reason:
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
                    if trade_age_days > max_age_days:
                        continue
                    
                    decay_weight = self._exponential_decay_weight(trade_age_days, halflife_days=30.0)
                    
                    pnl = float(trade.get("pnl_usd", 0.0))
                    pnl_pct = float(context.get("pnl_pct", 0.0))
                    hold_minutes = context.get("hold_minutes", 0)
                    
                    # Parse close reason to extract individual signals
                    exit_signals = self._parse_close_reason(close_reason)
                    
                    # Track performance for each signal and combinations
                    for signal in exit_signals:
                        if signal not in signal_performance:
                            signal_performance[signal] = {
                                "count": 0,
                                "total_pnl": 0.0,
                                "weighted_pnl": 0.0,
                                "total_weight": 0.0,
                                "wins": 0,
                                "losses": 0,
                                "total_hold_minutes": 0.0,
                                "avg_pnl_pct": 0.0
                            }
                        
                        perf = signal_performance[signal]
                        perf["count"] += 1
                        perf["total_pnl"] += pnl
                        perf["weighted_pnl"] += pnl * decay_weight
                        perf["total_weight"] += decay_weight
                        perf["total_hold_minutes"] += hold_minutes
                        if pnl > 0:
                            perf["wins"] += 1
                        else:
                            perf["losses"] += 1
                    
                    # Also track combinations (full close reason)
                    if close_reason not in signal_performance:
                        signal_performance[close_reason] = {
                            "count": 0,
                            "total_pnl": 0.0,
                            "weighted_pnl": 0.0,
                            "total_weight": 0.0,
                            "wins": 0,
                            "losses": 0,
                            "total_hold_minutes": 0.0,
                            "avg_pnl_pct": 0.0
                        }
                    
                    combo_perf = signal_performance[close_reason]
                    combo_perf["count"] += 1
                    combo_perf["total_pnl"] += pnl
                    combo_perf["weighted_pnl"] += pnl * decay_weight
                    combo_perf["total_weight"] += decay_weight
                    combo_perf["total_hold_minutes"] += hold_minutes
                    if pnl > 0:
                        combo_perf["wins"] += 1
                    else:
                        combo_perf["losses"] += 1
                
                except Exception as e:
                    logger.debug(f"Error analyzing close reason: {e}")
                    continue
            
            # Calculate metrics for each signal
            for signal, perf in signal_performance.items():
                if perf["count"] > 0:
                    if perf["total_weight"] > 0:
                        perf["avg_pnl"] = perf["weighted_pnl"] / perf["total_weight"]
                    else:
                        perf["avg_pnl"] = perf["total_pnl"] / perf["count"]
                    
                    perf["win_rate"] = (perf["wins"] / perf["count"] * 100) if perf["count"] > 0 else 0.0
                    perf["avg_hold_minutes"] = perf["total_hold_minutes"] / perf["count"]
            
            # Sort by weighted average P&L
            sorted_signals = sorted(signal_performance.items(), 
                                   key=lambda x: x[1].get("avg_pnl", 0.0), 
                                   reverse=True)
            
            top_signals = {k: {
                "count": v["count"],
                "avg_pnl": round(v.get("avg_pnl", 0.0), 2),
                "win_rate": round(v.get("win_rate", 0.0), 1),
                "avg_hold_minutes": round(v.get("avg_hold_minutes", 0.0), 1)
            } for k, v in sorted_signals[:10]}  # Top 10
            
            return {
                "status": "success",
                "signals_analyzed": len(signal_performance),
                "top_signals": top_signals
            }
            
        except Exception as e:
            logger.error(f"Close reason performance analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def analyze_profit_targets(self) -> Dict[str, Any]:
        """Analyze optimal profit targets and scale-out fractions with cumulative learning."""
        try:
            attribution_file = DATA_DIR / "attribution.jsonl"
            if not attribution_file.exists():
                return {"status": "skipped", "reason": "no_trades"}
            
            scenario_results = {}
            now = datetime.now(timezone.utc)
            max_age_days = 60  # Look back 60 days
            
            with attribution_file.open("r") as f:
                lines = f.readlines()
            
            # Process ALL trades with exponential decay
            for line in lines:
                try:
                    trade = json.loads(line.strip())
                    if trade.get("type") != "attribution":
                        continue
                    
                    context = trade.get("context", {})
                    close_reason = context.get("close_reason", "")
                    
                    # Only analyze trades that hit profit targets
                    if "profit_target" not in close_reason:
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
                    if trade_age_days > max_age_days:
                        continue
                    
                    decay_weight = self._exponential_decay_weight(trade_age_days, halflife_days=30.0)
                    
                    pnl = float(trade.get("pnl_usd", 0.0))
                    pnl_pct = float(context.get("pnl_pct", 0.0))
                    
                    # Extract profit target from close reason
                    # Format: "profit_target(2%)" or "profit_target(5%)"
                    target_match = re.search(r"profit_target\((\d+)%\)", close_reason)
                    if not target_match:
                        continue
                    
                    hit_target_pct = float(target_match.group(1)) / 100.0
                    
                    # Simulate: "What if we used different profit targets?"
                    # For each scenario, check if this trade would have hit targets earlier/later
                    for scenario in self.profit_target_scenarios:
                        scenario_key = f"targets_{'_'.join([f'{t:.3f}' for t in scenario.targets])}_scales_{'_'.join([f'{s:.2f}' for s in scenario.scale_fractions])}"
                        
                        if scenario_key not in scenario_results:
                            scenario_results[scenario_key] = {
                                "test_count": 0,
                                "total_pnl": 0.0,
                                "weighted_pnl": 0.0,
                                "total_weight": 0.0,
                                "targets_hit": 0,
                                "total_targets_hit": 0
                            }
                        
                        result = scenario_results[scenario_key]
                        
                        # Simulate: Would this scenario have captured more profit?
                        # If actual P&L exceeded scenario's first target, count it as a hit
                        simulated_pnl = pnl_pct
                        targets_hit = 0
                        
                        for target_pct in scenario.targets:
                            if simulated_pnl >= target_pct:
                                targets_hit += 1
                            else:
                                break
                        
                        result["test_count"] += 1
                        result["total_pnl"] += pnl
                        result["weighted_pnl"] += pnl * decay_weight
                        result["total_weight"] += decay_weight
                        result["total_targets_hit"] += targets_hit
                
                except Exception as e:
                    logger.debug(f"Error analyzing profit target: {e}")
                    continue
            
            # Find best profit target scenario
            best_scenario = None
            best_weighted_avg_pnl = float('-inf')
            
            for scenario_key, result in scenario_results.items():
                if result["test_count"] < 20:  # Minimum 20 samples
                    continue
                
                if result["total_weight"] > 0:
                    weighted_avg_pnl = result["weighted_pnl"] / result["total_weight"]
                    avg_targets_hit = result["total_targets_hit"] / result["test_count"]
                else:
                    weighted_avg_pnl = result["total_pnl"] / result["test_count"]
                    avg_targets_hit = result["total_targets_hit"] / result["test_count"]
                
                # Prefer scenarios that hit more targets AND have better P&L
                score = weighted_avg_pnl * (1 + avg_targets_hit * 0.1)  # Bonus for hitting targets
                
                if score > best_weighted_avg_pnl:
                    best_weighted_avg_pnl = score
                    best_scenario = scenario_key
            
            return {
                "status": "success",
                "scenarios_tested": len(scenario_results),
                "best_scenario": best_scenario,
                "best_weighted_avg_pnl": round(best_weighted_avg_pnl, 2) if best_weighted_avg_pnl != float('-inf') else None
            }
            
        except Exception as e:
            logger.error(f"Profit target analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _parse_close_reason(self, close_reason: str) -> List[str]:
        """Parse composite close reason into individual exit signals."""
        if not close_reason or close_reason == "unknown":
            return []
        
        # Split by + to get individual signals
        signals = []
        for part in close_reason.split("+"):
            part = part.strip()
            if not part:
                continue
            
            # Extract signal name (before first parenthesis)
            if "(" in part:
                signal_name = part.split("(")[0].strip()
            else:
                signal_name = part.strip()
            
            if signal_name:
                signals.append(signal_name)
        
        return signals
    
    def run_learning_cycle(self) -> Dict[str, Any]:
        """Run complete learning cycle."""
        logger.info("Starting comprehensive learning cycle")
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counterfactual": {},
            "weight_variations": {},
            "timing": {},
            "sizing": {},
            "exit_thresholds": {},
            "close_reason_performance": {},
            "profit_targets": {},
            "errors": []
        }
        
        # 1. Counterfactual analysis
        try:
            results["counterfactual"] = self.run_counterfactual_analysis()
        except Exception as e:
            results["errors"].append(f"Counterfactual: {str(e)}")
            logger.error(f"Counterfactual error: {e}")
        
        # 2. Weight variation analysis
        try:
            results["weight_variations"] = self.analyze_weight_variations()
        except Exception as e:
            results["errors"].append(f"Weight variations: {str(e)}")
            logger.error(f"Weight variation error: {e}")
        
        # 3. Timing analysis
        try:
            results["timing"] = self.analyze_timing_scenarios()
        except Exception as e:
            results["errors"].append(f"Timing: {str(e)}")
            logger.error(f"Timing error: {e}")
        
        # 4. Sizing analysis
        try:
            results["sizing"] = self.analyze_sizing_scenarios()
        except Exception as e:
            results["errors"].append(f"Sizing: {str(e)}")
            logger.error(f"Sizing error: {e}")
        
        # 5. Exit threshold optimization
        try:
            results["exit_thresholds"] = self.analyze_exit_thresholds()
        except Exception as e:
            results["errors"].append(f"Exit thresholds: {str(e)}")
            logger.error(f"Exit threshold error: {e}")
        
        # 6. Close reason performance analysis
        try:
            results["close_reason_performance"] = self.analyze_close_reason_performance()
        except Exception as e:
            results["errors"].append(f"Close reason performance: {str(e)}")
            logger.error(f"Close reason performance error: {e}")
        
        # 7. Profit target optimization
        try:
            results["profit_targets"] = self.analyze_profit_targets()
        except Exception as e:
            results["errors"].append(f"Profit targets: {str(e)}")
            logger.error(f"Profit target error: {e}")
        
        # Log results
        self._log_results(results)
        
        # Update state
        self.last_run_ts = time.time()
        if results["errors"]:
            self.error_count += len(results["errors"])
        else:
            self.success_count += 1
        
        self._save_state()
        
        # 8. Update exit signal weights based on close reason performance
        try:
            if results.get("close_reason_performance", {}).get("status") == "success":
                self._update_exit_signal_weights(results["close_reason_performance"])
        except Exception as e:
            results["errors"].append(f"Exit weight update: {str(e)}")
            logger.error(f"Exit weight update error: {e}")
        
        # 9. Apply optimized exit thresholds
        try:
            if results.get("exit_thresholds", {}).get("status") == "success":
                self._apply_optimized_exit_thresholds(results["exit_thresholds"])
        except Exception as e:
            results["errors"].append(f"Exit threshold apply: {str(e)}")
            logger.error(f"Exit threshold apply error: {e}")
        
        # 10. Apply optimized profit targets
        try:
            if results.get("profit_targets", {}).get("status") == "success":
                self._apply_optimized_profit_targets(results["profit_targets"])
        except Exception as e:
            results["errors"].append(f"Profit target apply: {str(e)}")
            logger.error(f"Profit target apply error: {e}")
        
        logger.info(f"Learning cycle complete: {len(results['errors'])} errors")
        return results
    
    def _update_exit_signal_weights(self, performance_data: Dict[str, Any]):
        """Update exit signal weights based on close reason performance."""
        try:
            from adaptive_signal_optimizer import get_optimizer, EXIT_COMPONENTS
            optimizer = get_optimizer()
            if not optimizer or not hasattr(optimizer, 'exit_model'):
                return
            
            top_signals = performance_data.get("top_signals", {})
            if not top_signals:
                return
            
            # Update exit model weights based on performance
            for signal_name, perf in top_signals.items():
                # Map close reason signals to exit model components
                exit_component = None
                if "signal_decay" in signal_name:
                    exit_component = "entry_decay"
                elif "flow_reversal" in signal_name or "adverse_flow" in signal_name:
                    exit_component = "adverse_flow"
                elif "drawdown" in signal_name:
                    exit_component = "drawdown_velocity"
                elif "time" in signal_name or "stale" in signal_name:
                    exit_component = "time_decay"
                elif "momentum" in signal_name:
                    exit_component = "momentum_reversal"
                
                if exit_component and exit_component in EXIT_COMPONENTS:
                    avg_pnl = perf.get("avg_pnl", 0.0)
                    win_rate = perf.get("win_rate", 50.0)
                    count = perf.get("count", 0)
                    
                    if count >= 10:  # Minimum samples
                        # Increase weight if signal leads to better exits
                        if avg_pnl > 0 and win_rate > 55:
                            current = optimizer.exit_model.weight_bands[exit_component].current
                            new = min(2.5, current + 0.1)  # Gradual increase
                            optimizer.exit_model.weight_bands[exit_component].current = new
                            logger.info(f"Updated {exit_component} weight: {current:.2f} -> {new:.2f} (avg_pnl=${avg_pnl:.2f}, wr={win_rate:.1f}%)")
                        elif avg_pnl < 0 or win_rate < 45:
                            current = optimizer.exit_model.weight_bands[exit_component].current
                            new = max(0.25, current - 0.1)  # Gradual decrease
                            optimizer.exit_model.weight_bands[exit_component].current = new
                            logger.info(f"Reduced {exit_component} weight: {current:.2f} -> {new:.2f} (avg_pnl=${avg_pnl:.2f}, wr={win_rate:.1f}%)")
            
            # Save updated weights
            optimizer.save_state()
            
        except Exception as e:
            logger.warning(f"Error updating exit signal weights: {e}")
    
    def _apply_optimized_exit_thresholds(self, threshold_data: Dict[str, Any]):
        """Apply optimized exit thresholds gradually."""
        try:
            best_scenario = threshold_data.get("best_scenario")
            if not best_scenario:
                return
            
            # Parse scenario: "trail_0.020_time_300_stale_14"
            import re
            trail_match = re.search(r"trail_([\d.]+)", best_scenario)
            time_match = re.search(r"time_(\d+)", best_scenario)
            stale_match = re.search(r"stale_(\d+)", best_scenario)
            
            if trail_match and time_match:
                optimal_trail = float(trail_match.group(1))
                optimal_time = int(time_match.group(1))
                optimal_stale = int(stale_match.group(1)) if stale_match else 12
                
                # Get current thresholds
                from config.registry import Thresholds
                current_trail = Thresholds.TRAILING_STOP_PCT
                current_time = Thresholds.TIME_EXIT_MINUTES
                current_stale = Thresholds.TIME_EXIT_DAYS_STALE
                
                # Gradual update (10% toward optimal to avoid overfitting)
                new_trail = current_trail + (optimal_trail - current_trail) * 0.1
                new_time = int(current_time + (optimal_time - current_time) * 0.1)
                new_stale = int(current_stale + (optimal_stale - current_stale) * 0.1)
                
                logger.info(f"Exit threshold optimization: trail {current_trail:.3f}->{new_trail:.3f}, "
                          f"time {current_time}->{new_time}min, stale {current_stale}->{new_stale}days")
                
                # Note: Actual threshold updates would need to be persisted to state file
                # and loaded on startup. For now, we log the recommendations.
                # TODO: Implement threshold state persistence
                
        except Exception as e:
            logger.warning(f"Error applying optimized exit thresholds: {e}")
    
    def _apply_optimized_profit_targets(self, profit_target_data: Dict[str, Any]):
        """Apply optimized profit targets gradually."""
        try:
            best_scenario = profit_target_data.get("best_scenario")
            if not best_scenario:
                return
            
            # Parse scenario: "targets_0.020_0.050_0.100_scales_0.30_0.30_0.40"
            targets_match = re.search(r"targets_([\d.]+)_([\d.]+)_([\d.]+)", best_scenario)
            scales_match = re.search(r"scales_([\d.]+)_([\d.]+)_([\d.]+)", best_scenario)
            
            if targets_match and scales_match:
                optimal_targets = [
                    float(targets_match.group(1)),
                    float(targets_match.group(2)),
                    float(targets_match.group(3))
                ]
                optimal_scales = [
                    float(scales_match.group(1)),
                    float(scales_match.group(2)),
                    float(scales_match.group(3))
                ]
                
                # Get current values
                from main import Config
                current_targets = Config.PROFIT_TARGETS
                current_scales = Config.SCALE_OUT_FRACTIONS
                
                # Gradual update (10% toward optimal to avoid overfitting)
                new_targets = [
                    current_targets[i] + (optimal_targets[i] - current_targets[i]) * 0.1
                    if i < len(current_targets) and i < len(optimal_targets)
                    else current_targets[i] if i < len(current_targets) else optimal_targets[i]
                    for i in range(max(len(current_targets), len(optimal_targets)))
                ]
                new_scales = [
                    current_scales[i] + (optimal_scales[i] - current_scales[i]) * 0.1
                    if i < len(current_scales) and i < len(optimal_scales)
                    else current_scales[i] if i < len(current_scales) else optimal_scales[i]
                    for i in range(max(len(current_scales), len(optimal_scales)))
                ]
                
                logger.info(f"Profit target optimization: targets {current_targets}->{[round(t, 3) for t in new_targets]}, "
                          f"scales {current_scales}->{[round(s, 2) for s in new_scales]}")
                
                # Note: Actual threshold updates would need to be persisted to state file
                # and loaded on startup. For now, we log the recommendations.
                # TODO: Implement profit target state persistence
                
        except Exception as e:
            logger.warning(f"Error applying optimized profit targets: {e}")
    
    def _log_results(self, results: Dict[str, Any]):
        """Log learning results."""
        try:
            LEARNING_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with LEARNING_LOG_FILE.open("a") as f:
                f.write(json.dumps(results, default=str) + "\n")
        except Exception as e:
            logger.warning(f"Error logging results: {e}")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load learning state."""
        if LEARNING_STATE_FILE.exists():
            try:
                return json.loads(LEARNING_STATE_FILE.read_text())
            except:
                pass
        return {}
    
    def _save_state(self):
        """Save learning state."""
        try:
            state = {
                "last_run_ts": self.last_run_ts,
                "error_count": self.error_count,
                "success_count": self.success_count,
                "weight_variations": {
                    comp: [vars(v).copy() for v in vars_list]
                    for comp, vars_list in self.weight_variations.items()
                }
            }
            LEARNING_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            LEARNING_STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
        except Exception as e:
            logger.warning(f"Error saving state: {e}")
    
    def start_background_learning(self, interval_minutes: int = 60):
        """Start background learning thread."""
        if self.running:
            return
        
        self.running = True
        
        def learning_loop():
            while self.running:
                try:
                    self.run_learning_cycle()
                    time.sleep(interval_minutes * 60)
                except Exception as e:
                    logger.error(f"Learning loop error: {e}")
                    time.sleep(60)  # Retry after 1 minute on error
        
        self.thread = threading.Thread(target=learning_loop, daemon=True, name="ComprehensiveLearning")
        self.thread.start()
        logger.info("Background learning started")
    
    def stop_background_learning(self):
        """Stop background learning."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background learning stopped")
    
    def get_health(self) -> Dict[str, Any]:
        """Get learning system health."""
        return {
            "running": self.running,
            "last_run_ts": self.last_run_ts,
            "last_run_age_sec": time.time() - self.last_run_ts if self.last_run_ts > 0 else None,
            "error_count": self.error_count,
            "success_count": self.success_count,
            "components_available": {
                "counterfactual": self.counterfactual_analyzer is not None
            }
        }


# Global instance
_learning_orchestrator: Optional[ComprehensiveLearningOrchestrator] = None

def get_learning_orchestrator() -> ComprehensiveLearningOrchestrator:
    """Get global learning orchestrator instance."""
    global _learning_orchestrator
    if _learning_orchestrator is None:
        _learning_orchestrator = ComprehensiveLearningOrchestrator()
    return _learning_orchestrator


def main():
    """Run learning cycle manually."""
    orchestrator = get_learning_orchestrator()
    results = orchestrator.run_learning_cycle()
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()



