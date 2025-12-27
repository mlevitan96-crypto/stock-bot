#!/usr/bin/env python3
"""
Regression Tests for Learning Enhancements

Tests all three learning enhancements:
1. Gate Pattern Learning
2. UW Blocked Entry Learning
3. Signal Pattern Learning

Follows SDLC best practices with comprehensive test coverage.
"""

import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from learning_enhancements_v1 import (
    GatePatternLearner,
    UWBlockedEntryLearner,
    SignalPatternLearner
)

# Test results
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_test(name: str, passed: bool, message: str = ""):
    """Log test result"""
    if passed:
        test_results["passed"].append(name)
        print(f"[PASS] {name}")
    else:
        test_results["failed"].append(name)
        print(f"[FAIL] {name}: {message}")

def test_gate_pattern_learner():
    """Test Gate Pattern Learning"""
    print("\n" + "=" * 80)
    print("TESTING: Gate Pattern Learning")
    print("=" * 80)
    
    # Create temporary state file
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "gate_pattern_learning.json"
        learner = GatePatternLearner()
        learner.state_file = state_file
        
        # Test 1: Record gate blocks
        learner.record_gate_block("score_below_min", "AAPL", 1.5, {"flow": 0.3, "dark_pool": 0.2}, "score_too_low")
        learner.record_gate_block("score_below_min", "MSFT", 0.8, {"flow": 0.1}, "score_too_low")
        learner.record_gate_block("max_positions", "GOOGL", 3.2, {"flow": 0.5, "insider": 0.3}, "max_positions_reached")
        
        log_test("Gate Learner - Record blocks", learner.patterns["score_below_min"]["blocks"] == 2)
        log_test("Gate Learner - Track score ranges", "0-1" in learner.patterns["score_below_min"]["score_ranges"] or "1-2" in learner.patterns["score_below_min"]["score_ranges"])
        
        # Test 2: Save and load state
        learner.save_state()
        new_learner = GatePatternLearner()
        new_learner.state_file = state_file
        new_learner.load_state()
        log_test("Gate Learner - State persistence", new_learner.patterns["score_below_min"]["blocks"] == 2)
        
        # Test 3: Get effectiveness
        effectiveness = learner.get_gate_effectiveness("score_below_min")
        log_test("Gate Learner - Effectiveness calculation", "effectiveness_ratio" in effectiveness)
        log_test("Gate Learner - Effectiveness structure", isinstance(effectiveness, dict) and "gate" in effectiveness)

def test_uw_blocked_learner():
    """Test UW Blocked Entry Learning"""
    print("\n" + "=" * 80)
    print("TESTING: UW Blocked Entry Learning")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "uw_blocked_learning.json"
        learner = UWBlockedEntryLearner()
        learner.state_file = state_file
        
        # Test 1: Record blocked entries
        learner.record_blocked_entry("AAPL", 0.45, {"flow": 0.3, "dark_pool": 0.2}, "BULLISH", "BULLISH", "NEUTRAL")
        learner.record_blocked_entry("MSFT", 0.35, {"flow": 0.1}, "BEARISH", "NEUTRAL", "NEUTRAL")
        learner.record_blocked_entry("AAPL", 0.55, {"flow": 0.4, "insider": 0.3}, "BULLISH", "BULLISH", "BULLISH")
        
        log_test("UW Blocked Learner - Record entries", learner.patterns["AAPL"]["blocked_count"] == 2)
        log_test("UW Blocked Learner - Track components", "flow" in learner.patterns["AAPL"]["component_patterns"])
        
        # Test 2: Save and load state
        learner.save_state()
        new_learner = UWBlockedEntryLearner()
        new_learner.state_file = state_file
        new_learner.load_state()
        log_test("UW Blocked Learner - State persistence", new_learner.patterns["AAPL"]["blocked_count"] == 2)
        
        # Test 3: Get patterns
        patterns = learner.get_blocked_patterns()
        log_test("UW Blocked Learner - Pattern analysis", "total_blocked_entries" in patterns)
        log_test("UW Blocked Learner - Pattern structure", isinstance(patterns, dict))

def test_signal_pattern_learner():
    """Test Signal Pattern Learning"""
    print("\n" + "=" * 80)
    print("TESTING: Signal Pattern Learning")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "signal_pattern_learning.json"
        learner = SignalPatternLearner()
        learner.state_file = state_file
        
        # Test 1: Record signals
        learner.record_signal("signal_1", "AAPL", {"flow": 0.3, "dark_pool": 0.2}, 2.5)
        learner.record_signal("signal_2", "MSFT", {"flow": 0.1, "insider": 0.3}, 1.8)
        learner.record_signal("signal_3", "AAPL", {"flow": 0.4, "dark_pool": 0.3}, 3.0)
        
        log_test("Signal Learner - Record signals", learner.patterns["AAPL"]["signal_count"] == 2)
        log_test("Signal Learner - Track combinations", len(learner.patterns["AAPL"]["component_combinations"]) > 0)
        
        # Test 2: Correlate with outcomes
        learner.update_pattern_with_outcome("AAPL", {"flow": 0.3, "dark_pool": 0.2}, 2.5)  # Win
        learner.update_pattern_with_outcome("AAPL", {"flow": 0.4, "dark_pool": 0.3}, -1.2)  # Loss
        learner.update_pattern_with_outcome("MSFT", {"flow": 0.1, "insider": 0.3}, 1.8)  # Win
        
        log_test("Signal Learner - Correlate outcomes", learner.patterns["AAPL"]["trades_resulting"] == 2)
        log_test("Signal Learner - Track wins/losses", learner.patterns["AAPL"]["wins"] == 1 and learner.patterns["AAPL"]["losses"] == 1)
        
        # Test 3: Get best patterns
        best = learner.get_best_patterns(min_samples=1)
        log_test("Signal Learner - Best patterns", isinstance(best, list))
        log_test("Signal Learner - Pattern ranking", len(best) > 0 or learner.patterns["AAPL"]["trades_resulting"] < 1)
        
        # Test 4: Save and load state
        learner.save_state()
        new_learner = SignalPatternLearner()
        new_learner.state_file = state_file
        new_learner.load_state()
        log_test("Signal Learner - State persistence", new_learner.patterns["AAPL"]["signal_count"] == 2)

def test_integration():
    """Test integration with comprehensive learning orchestrator"""
    print("\n" + "=" * 80)
    print("TESTING: Integration with Comprehensive Learning")
    print("=" * 80)
    
    # Test that modules can be imported
    try:
        from learning_enhancements_v1 import (
            get_gate_learner,
            get_uw_blocked_learner,
            get_signal_learner
        )
        gate_learner = get_gate_learner()
        uw_learner = get_uw_blocked_learner()
        signal_learner = get_signal_learner()
        
        log_test("Integration - Module imports", True)
        log_test("Integration - Gate learner instance", gate_learner is not None)
        log_test("Integration - UW learner instance", uw_learner is not None)
        log_test("Integration - Signal learner instance", signal_learner is not None)
    except ImportError as e:
        log_test("Integration - Module imports", False, str(e))

def test_error_handling():
    """Test error handling and graceful degradation"""
    print("\n" + "=" * 80)
    print("TESTING: Error Handling")
    print("=" * 80)
    
    # Test with invalid data
    learner = GatePatternLearner()
    try:
        learner.record_gate_block(None, None, None, None, None)
        log_test("Error Handling - Invalid data (gate)", True, "Gracefully handled")
    except Exception as e:
        log_test("Error Handling - Invalid data (gate)", False, str(e))
    
    learner = UWBlockedEntryLearner()
    try:
        learner.record_blocked_entry(None, None, None, None, None, None)
        log_test("Error Handling - Invalid data (UW)", True, "Gracefully handled")
    except Exception as e:
        log_test("Error Handling - Invalid data (UW)", False, str(e))
    
    learner = SignalPatternLearner()
    try:
        learner.record_signal(None, None, None, None)
        log_test("Error Handling - Invalid data (signal)", True, "Gracefully handled")
    except Exception as e:
        log_test("Error Handling - Invalid data (signal)", False, str(e))

def run_all_tests():
    """Run all regression tests"""
    print("=" * 80)
    print("LEARNING ENHANCEMENTS - REGRESSION TEST SUITE")
    print("=" * 80)
    print()
    
    test_gate_pattern_learner()
    test_uw_blocked_learner()
    test_signal_pattern_learner()
    test_integration()
    test_error_handling()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Passed: {len(test_results['passed'])}")
    print(f"Failed: {len(test_results['failed'])}")
    print(f"Warnings: {len(test_results['warnings'])}")
    print()
    
    if test_results['failed']:
        print("FAILED TESTS:")
        for test in test_results['failed']:
            print(f"  - {test}")
        print()
        return False
    else:
        print("[PASS] All tests passed!")
        return True

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
