#!/usr/bin/env python3
"""
Integration Test: Structural Intelligence Overhaul
Tests all 5 components working together.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

def test_regime_detector():
    """Test 1: Regime Detector"""
    print("\n=== Test 1: Regime Detector ===")
    try:
        from structural_intelligence.regime_detector import get_regime_detector, get_current_regime
        
        detector = get_regime_detector()
        regime, confidence = get_current_regime()
        
        print(f"  [PASS] Regime detected: {regime} (confidence: {confidence:.2f})")
        
        # Test multiplier
        bull_mult = detector.get_regime_multiplier("bullish")
        bear_mult = detector.get_regime_multiplier("bearish")
        print(f"  [PASS] Bullish multiplier: {bull_mult:.2f}, Bearish multiplier: {bear_mult:.2f}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Regime detector error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_macro_gate():
    """Test 2: Macro Gate"""
    print("\n=== Test 2: Macro Gate ===")
    try:
        from structural_intelligence.macro_gate import get_macro_gate
        
        gate = get_macro_gate()
        gate.update_macro_data()
        
        status = gate.get_macro_status()
        print(f"  [PASS] Macro status: {status}")
        
        # Test multiplier
        tech_mult = gate.get_macro_multiplier("bullish", "Technology")
        print(f"  [PASS] Tech bullish multiplier: {tech_mult:.2f}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Macro gate error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_structural_exit():
    """Test 3: Structural Exit"""
    print("\n=== Test 3: Structural Exit ===")
    try:
        from structural_intelligence.structural_exit import get_structural_exit
        
        exit_mgr = get_structural_exit()
        
        # Test exit recommendation
        position_data = {
            "current_price": 150.0,
            "side": "buy",
            "entry_price": 145.0,
            "unrealized_pnl_pct": 0.03
        }
        
        rec = exit_mgr.get_exit_recommendation("AAPL", position_data)
        print(f"  [PASS] Exit recommendation: {rec}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Structural exit error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_thompson_sampling():
    """Test 4: Thompson Sampling Engine"""
    print("\n=== Test 4: Thompson Sampling Engine ===")
    try:
        from learning.thompson_sampling_engine import get_thompson_engine
        
        engine = get_thompson_engine()
        
        # Register a component
        engine.register_component("flow_count", 1.0)
        
        # Sample weight
        weight = engine.sample_weight("flow_count")
        print(f"  [PASS] Sampled weight: {weight:.2f}")
        
        # Record outcome
        engine.record_outcome("flow_count", weight, 0.05, success_threshold=0.0)
        
        # Get optimal weight
        optimal = engine.get_optimal_weight("flow_count")
        print(f"  [PASS] Optimal weight: {optimal:.2f}")
        
        # Get stats
        stats = engine.get_component_stats("flow_count")
        print(f"  [PASS] Component stats: {stats}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Thompson sampling error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_shadow_logger():
    """Test 5: Shadow Trade Logger"""
    print("\n=== Test 5: Shadow Trade Logger ===")
    try:
        from self_healing.shadow_trade_logger import get_shadow_logger
        
        logger = get_shadow_logger()
        
        # Log rejected signal
        logger.log_rejected_signal(
            "AAPL", "score_below_min", 1.5,
            {"flow_count": 2, "premium": 30000},
            "score_gate", 2.0
        )
        print("  [PASS] Rejected signal logged")
        
        # Analyze performance
        analysis = logger.analyze_shadow_performance(lookback_days=30)
        print(f"  [PASS] Shadow analysis: {len(analysis.get('gate_analysis', {}))} gates analyzed")
        
        # Get threshold
        threshold = logger.get_gate_threshold("score_gate", "min_score", 2.0)
        print(f"  [PASS] Current threshold: {threshold}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Shadow logger error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_token_bucket():
    """Test 6: Token Bucket"""
    print("\n=== Test 6: Token Bucket ===")
    try:
        from api_management.token_bucket import get_quota_manager
        
        manager = get_quota_manager()
        
        # Prioritize symbol
        manager.prioritize_symbol("AAPL", volume=1000000, open_interest=500000)
        
        # Check if can poll
        can_poll, wait_time = manager.should_poll_symbol("AAPL")
        print(f"  [PASS] Can poll AAPL: {can_poll}, wait time: {wait_time:.1f}s")
        
        # Get status
        status = manager.get_quota_status()
        print(f"  [PASS] Quota status: {status}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Token bucket error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test 7: Full Integration"""
    print("\n=== Test 7: Full Integration ===")
    try:
        # Test that all modules can work together
        from structural_intelligence import get_regime_detector, get_macro_gate, get_structural_exit
        from learning import get_thompson_engine
        from self_healing import get_shadow_logger
        from api_management import get_quota_manager
        
        # Get all instances
        regime = get_regime_detector()
        macro = get_macro_gate()
        exit_mgr = get_structural_exit()
        thompson = get_thompson_engine()
        shadow = get_shadow_logger()
        quota = get_quota_manager()
        
        print("  [PASS] All modules imported and instantiated")
        
        # Test composite score adjustment
        regime_name, confidence = regime.detect_regime()
        regime_mult = regime.get_regime_multiplier("bullish")
        macro_mult = macro.get_macro_multiplier("bullish", "Technology")
        composite_mult = regime_mult * macro_mult
        
        print(f"  [PASS] Composite multiplier: {composite_mult:.2f} (regime: {regime_mult:.2f} * macro: {macro_mult:.2f})")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("=" * 80)
    print("STRUCTURAL INTELLIGENCE INTEGRATION TESTS")
    print("=" * 80)
    
    tests = [
        ("Regime Detector", test_regime_detector),
        ("Macro Gate", test_macro_gate),
        ("Structural Exit", test_structural_exit),
        ("Thompson Sampling", test_thompson_sampling),
        ("Shadow Logger", test_shadow_logger),
        ("Token Bucket", test_token_bucket),
        ("Full Integration", test_integration)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n[FAIL] {name} crashed: {e}")
            results[name] = False
    
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Save results
    results_file = Path("structural_intelligence_test_results.json")
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

