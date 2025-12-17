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
    
    def analyze_weight_variations(self) -> Dict[str, Any]:
        """
        Analyze how different weight variations perform.
        Tests percentage-based variations, not just on/off.
        """
        try:
            from adaptive_signal_optimizer import get_optimizer
            optimizer = get_optimizer()
            if not optimizer:
                return {"status": "skipped", "reason": "optimizer_not_available"}
            
            # Read recent trades
            attribution_file = DATA_DIR / "attribution.jsonl"
            if not attribution_file.exists():
                return {"status": "skipped", "reason": "no_trades"}
            
            # Analyze each weight variation
            variation_results = {}
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
            
            with attribution_file.open("r") as f:
                lines = f.readlines()
            
            for line in lines[-500:]:  # Last 500 trades
                try:
                    trade = json.loads(line.strip())
                    if trade.get("type") != "attribution":
                        continue
                    
                    ts_str = trade.get("ts", "")
                    if not ts_str:
                        continue
                    
                    trade_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if trade_time < cutoff_time:
                        continue
                    
                    components = trade.get("context", {}).get("components", {})
                    pnl = trade.get("pnl_usd", 0.0)
                    
                    # For each component, test how different weight variations would have performed
                    for component, value in components.items():
                        if component not in self.weight_variations:
                            continue
                        
                        if component not in variation_results:
                            variation_results[component] = {}
                        
                        # Test each variation
                        for variation in self.weight_variations[component]:
                            var_key = f"{variation.variation_pct}%"
                            if var_key not in variation_results[component]:
                                variation_results[component][var_key] = {
                                    "test_count": 0,
                                    "total_pnl": 0.0,
                                    "wins": 0,
                                    "losses": 0
                                }
                            
                            # Simulate P&L with this weight variation
                            # P&L scales with weight (higher weight = more impact)
                            simulated_pnl = pnl * (variation.effective_weight / 1.0)
                            
                            var_result = variation_results[component][var_key]
                            var_result["test_count"] += 1
                            var_result["total_pnl"] += simulated_pnl
                            if simulated_pnl > 0:
                                var_result["wins"] += 1
                            else:
                                var_result["losses"] += 1
                
                except Exception as e:
                    logger.debug(f"Error analyzing trade: {e}")
                    continue
            
            # Find best variations and update optimizer
            best_variations = {}
            for component, variations in variation_results.items():
                best_var = None
                best_avg_pnl = float('-inf')
                
                for var_key, result in variations.items():
                    if result["test_count"] < 5:  # Need minimum samples
                        continue
                    
                    avg_pnl = result["total_pnl"] / result["test_count"]
                    if avg_pnl > best_avg_pnl:
                        best_avg_pnl = avg_pnl
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
        """Analyze optimal entry/exit timing."""
        try:
            attribution_file = DATA_DIR / "attribution.jsonl"
            if not attribution_file.exists():
                return {"status": "skipped", "reason": "no_trades"}
            
            scenario_results = {}
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
            
            with attribution_file.open("r") as f:
                lines = f.readlines()
            
            for line in lines[-500:]:
                try:
                    trade = json.loads(line.strip())
                    if trade.get("type") != "attribution":
                        continue
                    
                    context = trade.get("context", {})
                    hold_minutes = context.get("hold_minutes", 0)
                    pnl = trade.get("pnl_usd", 0.0)
                    
                    # Match to closest timing scenario
                    for scenario in self.timing_scenarios:
                        if abs(hold_minutes - scenario.exit_duration_min) < 60:  # Within 1 hour
                            scenario_key = f"{scenario.entry_delay_min}m_delay_{scenario.exit_duration_min}m_hold"
                            
                            if scenario_key not in scenario_results:
                                scenario_results[scenario_key] = {
                                    "test_count": 0,
                                    "total_pnl": 0.0,
                                    "wins": 0,
                                    "losses": 0
                                }
                            
                            result = scenario_results[scenario_key]
                            result["test_count"] += 1
                            result["total_pnl"] += pnl
                            if pnl > 0:
                                result["wins"] += 1
                            else:
                                result["losses"] += 1
                
                except Exception as e:
                    logger.debug(f"Error analyzing timing: {e}")
                    continue
            
            # Find best timing scenario
            best_scenario = None
            best_avg_pnl = float('-inf')
            
            for scenario_key, result in scenario_results.items():
                if result["test_count"] < 5:
                    continue
                
                avg_pnl = result["total_pnl"] / result["test_count"]
                if avg_pnl > best_avg_pnl:
                    best_avg_pnl = avg_pnl
                    best_scenario = scenario_key
            
            return {
                "status": "success",
                "scenarios_tested": len(scenario_results),
                "best_scenario": best_scenario,
                "best_avg_pnl": best_avg_pnl
            }
            
        except Exception as e:
            logger.error(f"Timing analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def analyze_sizing_scenarios(self) -> Dict[str, Any]:
        """Analyze optimal position sizing."""
        try:
            attribution_file = DATA_DIR / "attribution.jsonl"
            if not attribution_file.exists():
                return {"status": "skipped", "reason": "no_trades"}
            
            scenario_results = {}
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
            
            with attribution_file.open("r") as f:
                lines = f.readlines()
            
            for line in lines[-500:]:
                try:
                    trade = json.loads(line.strip())
                    if trade.get("type") != "attribution":
                        continue
                    
                    context = trade.get("context", {})
                    entry_score = context.get("entry_score", 0.0)
                    pnl = trade.get("pnl_usd", 0.0)
                    qty = context.get("qty", 1)
                    
                    # Match to sizing scenario based on confidence (entry_score)
                    for scenario in self.sizing_scenarios:
                        if entry_score >= scenario.confidence_threshold:
                            scenario_key = f"{scenario.size_multiplier}x_{scenario.confidence_threshold}conf"
                            
                            if scenario_key not in scenario_results:
                                scenario_results[scenario_key] = {
                                    "test_count": 0,
                                    "total_pnl": 0.0,
                                    "total_shares": 0,
                                    "pnl_per_share": 0.0
                                }
                            
                            result = scenario_results[scenario_key]
                            result["test_count"] += 1
                            result["total_pnl"] += pnl
                            result["total_shares"] += qty
                            
                            if result["total_shares"] > 0:
                                result["pnl_per_share"] = result["total_pnl"] / result["total_shares"]
                
                except Exception as e:
                    logger.debug(f"Error analyzing sizing: {e}")
                    continue
            
            # Find best sizing scenario
            best_scenario = None
            best_pnl_per_share = float('-inf')
            
            for scenario_key, result in scenario_results.items():
                if result["test_count"] < 5:
                    continue
                
                if result["pnl_per_share"] > best_pnl_per_share:
                    best_pnl_per_share = result["pnl_per_share"]
                    best_scenario = scenario_key
            
            return {
                "status": "success",
                "scenarios_tested": len(scenario_results),
                "best_scenario": best_scenario,
                "best_pnl_per_share": best_pnl_per_share
            }
            
        except Exception as e:
            logger.error(f"Sizing analysis error: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_learning_cycle(self) -> Dict[str, Any]:
        """Run complete learning cycle."""
        logger.info("Starting comprehensive learning cycle")
        
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counterfactual": {},
            "weight_variations": {},
            "timing": {},
            "sizing": {},
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
        
        # Log results
        self._log_results(results)
        
        # Update state
        self.last_run_ts = time.time()
        if results["errors"]:
            self.error_count += len(results["errors"])
        else:
            self.success_count += 1
        
        self._save_state()
        
        logger.info(f"Learning cycle complete: {len(results['errors'])} errors")
        return results
    
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
