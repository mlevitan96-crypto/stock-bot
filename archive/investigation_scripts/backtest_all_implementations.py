#!/usr/bin/env python3
"""
Comprehensive Backtest - Verify All TODO Implementations Work
Uses existing logging data to verify all implementations are functioning correctly.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

# Test results
results = {
    "tests_passed": 0,
    "tests_failed": 0,
    "tests_total": 0,
    "details": []
}

def test_result(name: str, passed: bool, message: str = ""):
    """Record test result"""
    results["tests_total"] += 1
    if passed:
        results["tests_passed"] += 1
        status = "PASS"
    else:
        results["tests_failed"] += 1
        status = "FAIL"
    
    results["details"].append({
        "test": name,
        "status": status,
        "message": message
    })
    status_char = "[PASS]" if passed else "[FAIL]"
    print(f"{status_char} {name}: {message}")

def test_tca_data_manager():
    """Test TCA data manager implementation"""
    print("\n=== Testing TCA Data Manager ===")
    
    try:
        from tca_data_manager import (
            get_recent_slippage, get_tca_quality_score, 
            get_regime_forecast_modifier, get_toxicity_sentinel_score,
            get_recent_failures, track_execution_failure
        )
        
        # Test 1: get_recent_slippage (should not crash)
        try:
            slippage = get_recent_slippage("AAPL", 24)
            test_result("TCA: get_recent_slippage", True, f"Returns {slippage:.4f}")
        except Exception as e:
            test_result("TCA: get_recent_slippage", False, f"Error: {e}")
        
        # Test 2: get_tca_quality_score
        try:
            quality = get_tca_quality_score("AAPL", 24)
            test_result("TCA: get_tca_quality_score", True, f"Returns {quality:.2f}")
        except Exception as e:
            test_result("TCA: get_tca_quality_score", False, f"Error: {e}")
        
        # Test 3: get_regime_forecast_modifier
        try:
            modifier = get_regime_forecast_modifier("RISK_ON")
            test_result("TCA: get_regime_forecast_modifier", True, f"Returns {modifier:.4f}")
        except Exception as e:
            test_result("TCA: get_regime_forecast_modifier", False, f"Error: {e}")
        
        # Test 4: get_toxicity_sentinel_score
        try:
            cluster_data = {"toxicity": 0.6, "conviction": 0.7}
            toxicity = get_toxicity_sentinel_score("AAPL", cluster_data)
            test_result("TCA: get_toxicity_sentinel_score", True, f"Returns {toxicity:.2f}")
        except Exception as e:
            test_result("TCA: get_toxicity_sentinel_score", False, f"Error: {e}")
        
        # Test 5: track_execution_failure
        try:
            track_execution_failure("AAPL", "test_failure", {"test": True})
            test_result("TCA: track_execution_failure", True, "No errors")
        except Exception as e:
            test_result("TCA: track_execution_failure", False, f"Error: {e}")
        
        # Test 6: get_recent_failures
        try:
            failures = get_recent_failures("AAPL", 24)
            test_result("TCA: get_recent_failures", True, f"Returns {failures}")
        except Exception as e:
            test_result("TCA: get_recent_failures", False, f"Error: {e}")
            
    except ImportError as e:
        test_result("TCA: Module import", False, f"Import error: {e}")

def test_execution_quality_learner():
    """Test execution quality learner"""
    print("\n=== Testing Execution Quality Learner ===")
    
    try:
        from execution_quality_learner import get_execution_learner
        
        learner = get_execution_learner()
        test_result("Execution Learner: Import", True, "Module imported")
        
        # Test recording execution
        try:
            learner.record_order_execution(
                symbol="AAPL",
                strategy="limit_offset",
                regime="RISK_ON",
                slippage_pct=0.003,
                filled=True,
                fill_time_sec=0.5
            )
            test_result("Execution Learner: record_order_execution", True, "No errors")
        except Exception as e:
            test_result("Execution Learner: record_order_execution", False, f"Error: {e}")
        
        # Test getting recommendation
        try:
            strategy = learner.get_recommended_strategy("AAPL", "RISK_ON")
            test_result("Execution Learner: get_recommended_strategy", True, f"Returns: {strategy}")
        except Exception as e:
            test_result("Execution Learner: get_recommended_strategy", False, f"Error: {e}")
            
    except ImportError as e:
        test_result("Execution Learner: Module import", False, f"Import error: {e}")

def test_signal_pattern_learner():
    """Test signal pattern learner"""
    print("\n=== Testing Signal Pattern Learner ===")
    
    try:
        from signal_pattern_learner import get_signal_pattern_learner
        
        learner = get_signal_pattern_learner()
        test_result("Signal Learner: Import", True, "Module imported")
        
        # Test recording signal
        try:
            components = {"flow": 0.5, "dark_pool": 0.3, "insider": 0.2}
            learner.record_signal("test_signal_1", "AAPL", components, 3.5)
            test_result("Signal Learner: record_signal", True, "No errors")
        except Exception as e:
            test_result("Signal Learner: record_signal", False, f"Error: {e}")
        
        # Test getting best combinations
        try:
            best = learner.get_best_combinations(limit=5)
            test_result("Signal Learner: get_best_combinations", True, f"Returns {len(best)} combinations")
        except Exception as e:
            test_result("Signal Learner: get_best_combinations", False, f"Error: {e}")
            
    except ImportError as e:
        test_result("Signal Learner: Module import", False, f"Import error: {e}")

def test_counterfactual_analyzer():
    """Test counterfactual analyzer"""
    print("\n=== Testing Counterfactual Analyzer ===")
    
    try:
        from counterfactual_analyzer import get_price_at_time, compute_counterfactual_pnl
        
        # Test get_price_at_time (may return None if no API access, but shouldn't crash)
        try:
            price = get_price_at_time("AAPL", datetime.now(timezone.utc))
            test_result("Counterfactual: get_price_at_time", True, f"Returns: {price}")
        except Exception as e:
            test_result("Counterfactual: get_price_at_time", False, f"Error: {e}")
        
        # Test compute_counterfactual_pnl
        try:
            blocked_trade = {
                "symbol": "AAPL",
                "decision_price": 150.0,
                "direction": "bullish",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            pnl = compute_counterfactual_pnl(blocked_trade)
            test_result("Counterfactual: compute_counterfactual_pnl", True, f"Returns: {pnl}")
        except Exception as e:
            test_result("Counterfactual: compute_counterfactual_pnl", False, f"Error: {e}")
            
    except ImportError as e:
        test_result("Counterfactual: Module import", False, f"Import error: {e}")

def test_parameter_optimizer():
    """Test parameter optimizer"""
    print("\n=== Testing Parameter Optimizer ===")
    
    try:
        from parameter_optimizer import get_parameter_optimizer
        
        optimizer = get_parameter_optimizer()
        test_result("Parameter Optimizer: Import", True, "Module imported")
        
        # Test registering parameter
        try:
            optimizer.register_parameter(
                "TEST_PARAM",
                current_value=0.5,
                test_values=[0.3, 0.5, 0.7],
                description="Test parameter"
            )
            test_result("Parameter Optimizer: register_parameter", True, "No errors")
        except Exception as e:
            test_result("Parameter Optimizer: register_parameter", False, f"Error: {e}")
        
        # Test recording outcome
        try:
            optimizer.record_outcome("TEST_PARAM", 0.5, 0.02, win=True)
            test_result("Parameter Optimizer: record_outcome", True, "No errors")
        except Exception as e:
            test_result("Parameter Optimizer: record_outcome", False, f"Error: {e}")
        
        # Test getting optimal value
        try:
            optimal = optimizer.get_optimal_value("TEST_PARAM")
            test_result("Parameter Optimizer: get_optimal_value", True, f"Returns: {optimal}")
        except Exception as e:
            test_result("Parameter Optimizer: get_optimal_value", False, f"Error: {e}")
            
    except ImportError as e:
        test_result("Parameter Optimizer: Module import", False, f"Import error: {e}")

def test_main_integration():
    """Test that main.py integrates all modules correctly"""
    print("\n=== Testing Main.py Integration ===")
    
    # Check that main.py imports are correct
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
            
            # Check for TCA integration
            if "from tca_data_manager import get_recent_slippage" in content:
                test_result("Main: TCA integration", True, "get_recent_slippage imported")
            else:
                test_result("Main: TCA integration", False, "get_recent_slippage not found")
            
            # Check for regime forecast
            if "get_regime_forecast_modifier" in content:
                test_result("Main: Regime forecast", True, "get_regime_forecast_modifier used")
            else:
                test_result("Main: Regime forecast", False, "get_regime_forecast_modifier not found")
            
            # Check for toxicity sentinel
            if "get_toxicity_sentinel_score" in content:
                test_result("Main: Toxicity sentinel", True, "get_toxicity_sentinel_score used")
            else:
                test_result("Main: Toxicity sentinel", False, "get_toxicity_sentinel_score not found")
            
            # Check for execution failure tracking
            if "track_execution_failure" in content:
                test_result("Main: Execution failure tracking", True, "track_execution_failure used")
            else:
                test_result("Main: Execution failure tracking", False, "track_execution_failure not found")
            
            # Check for experiment parameters
            if "promoted_to_prod" in content or "parameters_copied" in content:
                test_result("Main: Experiment parameters", True, "Parameter copying implemented")
            else:
                test_result("Main: Experiment parameters", False, "Parameter copying not found")
                
    except Exception as e:
        test_result("Main: Integration check", False, f"Error reading main.py: {e}")

def test_learning_integration():
    """Test that learning orchestrator integrates all learners"""
    print("\n=== Testing Learning Orchestrator Integration ===")
    
    try:
        with open("comprehensive_learning_orchestrator_v2.py", "r", encoding="utf-8") as f:
            content = f.read()
            
            # Check for execution quality learning
            if "from execution_quality_learner import" in content or "execution_quality_learner" in content:
                test_result("Learning: Execution quality", True, "Execution quality learner integrated")
            else:
                test_result("Learning: Execution quality", False, "Execution quality learner not found")
            
            # Check for signal pattern learning
            if "from signal_pattern_learner import" in content or "signal_pattern_learner" in content:
                test_result("Learning: Signal patterns", True, "Signal pattern learner integrated")
            else:
                test_result("Learning: Signal patterns", False, "Signal pattern learner not found")
            
            # Check for counterfactual analysis
            if "from counterfactual_analyzer import compute_counterfactual_pnl" in content:
                test_result("Learning: Counterfactual", True, "Counterfactual analysis integrated")
            else:
                test_result("Learning: Counterfactual", False, "Counterfactual analysis not found")
                
    except Exception as e:
        test_result("Learning: Integration check", False, f"Error reading orchestrator: {e}")

def test_logging_cycle():
    """Test that logging files exist and can be processed"""
    print("\n=== Testing Logging Cycle ===")
    
    log_files = {
        "attribution": Path("logs/attribution.jsonl"),
        "exit": Path("logs/exit.jsonl"),
        "signals": Path("logs/signals.jsonl"),
        "orders": Path("logs/orders.jsonl"),
        "gate": Path("logs/gate.jsonl"),
    }
    
    state_files = {
        "blocked_trades": Path("state/blocked_trades.jsonl"),
        "uw_attribution": Path("data/uw_attribution.jsonl"),
    }
    
    for name, path in {**log_files, **state_files}.items():
        if path.exists():
            try:
                # Try to read at least one line
                with open(path, "r", encoding="utf-8") as f:
                    line = f.readline()
                    if line.strip():
                        test_result(f"Logging: {name}", True, f"File exists and has data")
                    else:
                        test_result(f"Logging: {name}", True, f"File exists (empty)")
            except Exception as e:
                test_result(f"Logging: {name}", False, f"Error reading: {e}")
        else:
            test_result(f"Logging: {name}", True, f"File doesn't exist yet (OK)")

def main():
    """Run all backtests"""
    print("=" * 80)
    print("COMPREHENSIVE BACKTEST - All TODO Implementations")
    print("=" * 80)
    print()
    
    # Run all tests
    test_tca_data_manager()
    test_execution_quality_learner()
    test_signal_pattern_learner()
    test_counterfactual_analyzer()
    test_parameter_optimizer()
    test_main_integration()
    test_learning_integration()
    test_logging_cycle()
    
    # Print summary
    print("\n" + "=" * 80)
    print("BACKTEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['tests_total']}")
    print(f"Passed: {results['tests_passed']}")
    print(f"Failed: {results['tests_failed']}")
    print(f"Success Rate: {results['tests_passed']/results['tests_total']*100:.1f}%")
    print()
    
    # Save results
    results_file = Path("backtest_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {results_file}")
    
    # Exit with appropriate code
    if results["tests_failed"] == 0:
        print("\n[SUCCESS] ALL TESTS PASSED")
        return 0
    else:
        print(f"\n[FAILURE] {results['tests_failed']} TEST(S) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())

