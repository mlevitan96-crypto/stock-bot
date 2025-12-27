#!/usr/bin/env python3
"""
Regression Test: Structural Intelligence Overhaul
Ensures existing functionality still works after integration.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

def test_main_imports():
    """Test 1: Main imports work"""
    print("\n=== Test 1: Main Imports ===")
    try:
        import main
        print("  [PASS] main.py imports successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] main.py import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_structural_intelligence_imports():
    """Test 2: Structural intelligence modules import"""
    print("\n=== Test 2: Structural Intelligence Imports ===")
    try:
        from structural_intelligence import get_regime_detector, get_macro_gate, get_structural_exit
        from learning import get_thompson_engine
        from self_healing import get_shadow_logger
        from api_management import get_quota_manager
        
        print("  [PASS] All structural intelligence modules import successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_learning_orchestrator_imports():
    """Test 3: Learning orchestrator imports"""
    print("\n=== Test 3: Learning Orchestrator Imports ===")
    try:
        import comprehensive_learning_orchestrator_v2
        print("  [PASS] Learning orchestrator imports successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] Learning orchestrator import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_existing_functions():
    """Test 4: Existing functions still work"""
    print("\n=== Test 4: Existing Functions ===")
    try:
        import main
        
        # Test that key functions exist
        assert hasattr(main, 'log_event'), "log_event missing"
        assert hasattr(main, 'log_blocked_trade'), "log_blocked_trade missing"
        
        print("  [PASS] Existing functions still available")
        return True
    except Exception as e:
        print(f"  [FAIL] Function check error: {e}")
        return False

def test_config_registry():
    """Test 5: Config registry still works"""
    print("\n=== Test 5: Config Registry ===")
    try:
        from config.registry import StateFiles, LogFiles, CacheFiles
        print("  [PASS] Config registry imports successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] Config registry error: {e}")
        return False

def test_signal_modules():
    """Test 6: Signal modules still work"""
    print("\n=== Test 6: Signal Modules ===")
    try:
        from signals.uw_composite import compute_uw_composite_score
        from signals.uw_adaptive import AdaptiveGate
        print("  [PASS] Signal modules import successfully")
        return True
    except Exception as e:
        print(f"  [FAIL] Signal module error: {e}")
        return False

def main():
    """Run all regression tests"""
    print("=" * 80)
    print("REGRESSION TEST: Structural Intelligence Overhaul")
    print("=" * 80)
    
    tests = [
        ("Main Imports", test_main_imports),
        ("Structural Intelligence Imports", test_structural_intelligence_imports),
        ("Learning Orchestrator Imports", test_learning_orchestrator_imports),
        ("Existing Functions", test_existing_functions),
        ("Config Registry", test_config_registry),
        ("Signal Modules", test_signal_modules)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n[FAIL] {name} crashed: {e}")
            results[name] = False
    
    print("\n" + "=" * 80)
    print("REGRESSION TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Save results
    results_file = Path("regression_test_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tests_passed": passed,
            "tests_total": total,
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

