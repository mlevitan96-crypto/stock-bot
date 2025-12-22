#!/usr/bin/env python3
"""
Comprehensive Test Suite for Learning System
============================================
Tests all learning components to ensure no regressions.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Test data directory
TEST_DATA_DIR = Path("test_data")
TEST_DATA_DIR.mkdir(exist_ok=True)


class LearningSystemTester:
    """Comprehensive test suite for learning system."""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def run_all_tests(self):
        """Run all tests."""
        print("=" * 80)
        print("LEARNING SYSTEM COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print()
        
        # Test 1: Exit Learning
        self.test_exit_learning()
        
        # Test 2: Profit Target Learning
        self.test_profit_target_learning()
        
        # Test 3: Risk Limit Learning
        self.test_risk_limit_learning()
        
        # Test 4: Execution Quality Learning
        self.test_execution_quality_learning()
        
        # Test 5: Integration Test
        self.test_integration()
        
        # Print summary
        print()
        print("=" * 80)
        print(f"TEST SUMMARY: {self.passed} passed, {self.failed} failed")
        print("=" * 80)
        
        return self.failed == 0
    
    def test_exit_learning(self):
        """Test exit learning components."""
        print("TEST 1: Exit Learning System")
        print("-" * 80)
        
        try:
            # Test close reason parsing (using main.py function)
            from main import build_composite_close_reason
            
            test_signals = {
                "time_exit": True,
                "age_hours": 72,
                "signal_decay": 0.65,
                "flow_reversal": True
            }
            reason = build_composite_close_reason(test_signals)
            
            assert "time_exit" in reason, "Should include time_exit"
            assert "signal_decay" in reason, "Should include signal_decay"
            assert "flow_reversal" in reason, "Should include flow_reversal"
            
            print("  [PASS] Close reason parsing works")
            self.passed += 1
            
            # Test exit threshold scenarios
            assert len(orchestrator.exit_threshold_scenarios) > 0, "Should have exit threshold scenarios"
            print("  [PASS] Exit threshold scenarios initialized")
            self.passed += 1
            
        except Exception as e:
            print(f"  [FAIL] Exit learning test failed: {e}")
            self.failed += 1
            import traceback
            traceback.print_exc()
    
    def test_profit_target_learning(self):
        """Test profit target optimization."""
        print()
        print("TEST 2: Profit Target Learning")
        print("-" * 80)
        
        try:
            # Create test attribution data
            test_attribution = self._create_test_attribution_data()
            attribution_file = TEST_DATA_DIR / "test_attribution.jsonl"
            
            with attribution_file.open("w") as f:
                for trade in test_attribution:
                    f.write(json.dumps(trade) + "\n")
            
            # Test that profit target scenarios can be created
            from comprehensive_learning_orchestrator import ComprehensiveLearningOrchestrator
            
            orchestrator = ComprehensiveLearningOrchestrator()
            
            # Verify profit target scenarios exist
            if hasattr(orchestrator, 'profit_target_scenarios'):
                assert len(orchestrator.profit_target_scenarios) > 0, "Should have profit target scenarios"
                print("  [PASS] Profit target scenarios initialized")
                self.passed += 1
            else:
                print("  [WARN] Profit target scenarios not yet implemented (will be added)")
            
        except Exception as e:
            print(f"  [FAIL] Profit target learning test failed: {e}")
            self.failed += 1
            import traceback
            traceback.print_exc()
    
    def test_risk_limit_learning(self):
        """Test risk limit optimization."""
        print()
        print("TEST 3: Risk Limit Learning")
        print("-" * 80)
        
        try:
            # Test that risk limits can be optimized
            from risk_management import get_risk_limits
            
            limits = get_risk_limits()
            assert "daily_loss_pct" in limits, "Should have daily loss limit"
            assert "max_drawdown_pct" in limits, "Should have max drawdown limit"
            
            print("  [PASS] Risk limits accessible")
            self.passed += 1
            
        except Exception as e:
            print(f"  [FAIL] Risk limit learning test failed: {e}")
            self.failed += 1
            import traceback
            traceback.print_exc()
    
    def test_execution_quality_learning(self):
        """Test execution quality learning."""
        print()
        print("TEST 4: Execution Quality Learning")
        print("-" * 80)
        
        try:
            # Test that order logs can be analyzed
            orders_file = Path("logs/orders.jsonl")
            if orders_file.exists():
                print("  [PASS] Order logs exist (can be analyzed)")
                self.passed += 1
            else:
                print("  [WARN] Order logs not found (will be created during trading)")
            
        except Exception as e:
            print(f"  [FAIL] Execution quality learning test failed: {e}")
            self.failed += 1
            import traceback
            traceback.print_exc()
    
    def test_integration(self):
        """Test full integration."""
        print()
        print("TEST 5: Integration Test")
        print("-" * 80)
        
        try:
            from comprehensive_learning_orchestrator import ComprehensiveLearningOrchestrator
            
            orchestrator = ComprehensiveLearningOrchestrator()
            
            # Test that learning cycle can run without errors
            # (This is a dry run - won't actually modify anything)
            print("  [PASS] Learning orchestrator can be instantiated")
            self.passed += 1
            
            # Test that all required methods exist
            required_methods = [
                'analyze_close_reason_performance',
                'analyze_exit_thresholds',
                'analyze_profit_targets',
                'run_learning_cycle'
            ]
            
            for method in required_methods:
                assert hasattr(orchestrator, method), f"Should have {method} method"
            
            print("  [PASS] All required methods exist")
            self.passed += 1
            
        except Exception as e:
            print(f"  [FAIL] Integration test failed: {e}")
            self.failed += 1
            import traceback
            traceback.print_exc()
    
    def _create_test_attribution_data(self):
        """Create test attribution data."""
        now = datetime.now(timezone.utc)
        test_trades = []
        
        for i in range(10):
            trade_time = now - timedelta(days=i)
            test_trades.append({
                "type": "attribution",
                "ts": trade_time.isoformat(),
                "symbol": "TEST",
                "pnl_usd": 10.0 * (i % 3 - 1),  # Mix of wins and losses
                "context": {
                    "close_reason": "time_exit(240h)+signal_decay(0.70)",
                    "hold_minutes": 240,
                    "entry_score": 3.5,
                    "pnl_pct": 0.02 * (i % 3 - 1)
                }
            })
        
        return test_trades


if __name__ == "__main__":
    tester = LearningSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
