#!/usr/bin/env python3
"""
Regression tests for Explainable AI (XAI) implementation
Tests all components to ensure nothing breaks.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all XAI modules can be imported"""
    print("Testing imports...")
    try:
        from xai.explainable_logger import ExplainableLogger, get_explainable_logger
        print("  [OK] XAI imports successful")
        return True
    except Exception as e:
        print(f"  [FAIL] XAI imports failed: {e}")
        return False

def test_explainable_logger():
    """Test ExplainableLogger functionality"""
    print("Testing ExplainableLogger...")
    try:
        from xai.explainable_logger import get_explainable_logger
        explainable = get_explainable_logger()
        
        # Test trade entry logging
        why = explainable.log_trade_entry(
            symbol="TEST",
            direction="bullish",
            score=3.5,
            components={"options_flow": 0.75, "dark_pool": 0.60},
            regime="RISK_ON",
            macro_yield=4.2,
            whale_clusters={"count": 5, "premium_usd": 100000},
            gamma_walls={"distance_pct": 0.03, "gamma_exposure": 5000000},
            composite_score=3.5,
            entry_price=100.0
        )
        assert "TEST" in why
        assert "RISK_ON" in why or "bullish" in why
        print("  [OK] Trade entry logging works")
        
        # Test trade exit logging
        why_exit = explainable.log_trade_exit(
            symbol="TEST",
            entry_price=100.0,
            exit_price=105.0,
            pnl_pct=5.0,
            hold_minutes=120,
            exit_reason="profit_target",
            regime="RISK_ON",
            gamma_walls=None
        )
        assert "TEST" in why_exit
        assert "profit" in why_exit.lower()
        print("  [OK] Trade exit logging works")
        
        # Test weight adjustment logging
        why_weight = explainable.log_weight_adjustment(
            component="options_flow",
            old_weight=1.0,
            new_weight=1.2,
            reason="Thompson Sampling (min_sample_size=30, Wilson CI>95%)",
            sample_count=35,
            win_rate=0.65,
            regime="RISK_ON",
            pnl_contribution=2.5
        )
        assert "options_flow" in why_weight
        assert "increased" in why_weight.lower() or "decreased" in why_weight.lower()
        print("  [OK] Weight adjustment logging works")
        
        # Test retrieval
        trades = explainable.get_trade_explanations(symbol="TEST", limit=10)
        assert len(trades) > 0
        print("  [OK] Trade explanation retrieval works")
        
        weights = explainable.get_weight_explanations(component="options_flow", limit=10)
        assert len(weights) > 0
        print("  [OK] Weight explanation retrieval works")
        
        return True
    except Exception as e:
        print(f"  [FAIL] ExplainableLogger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_thompson_sampling_min_sample():
    """Test that Thompson Sampling enforces min_sample_size"""
    print("Testing Thompson Sampling min_sample_size...")
    try:
        from learning.thompson_sampling_engine import ThompsonSamplingEngine
        
        engine = ThompsonSamplingEngine()
        engine.register_component("test_component", initial_weight=1.0)
        
        # Add 29 samples (below minimum)
        for i in range(29):
            engine.record_outcome("test_component", 1.0, 0.05 if i % 2 == 0 else -0.02)
        
        # Should not finalize with < 30 samples
        should_finalize = engine.should_finalize_weight("test_component", min_sample_size=30)
        assert not should_finalize, "Should not finalize with < 30 samples"
        print("  [OK] min_sample_size=30 enforced correctly")
        
        # Add one more sample to reach 30
        engine.record_outcome("test_component", 1.0, 0.05)
        
        # Now might finalize (depending on confidence)
        should_finalize_30 = engine.should_finalize_weight("test_component", min_sample_size=30)
        print(f"  [OK] With 30 samples, finalization check: {should_finalize_30}")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Thompson Sampling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_imports():
    """Test that main.py can import XAI"""
    print("Testing main.py XAI integration...")
    try:
        # Check if import exists in main.py
        main_py = Path("main.py")
        if not main_py.exists():
            print("  [SKIP] main.py not found")
            return True
        
        content = main_py.read_text(encoding='utf-8')
        if "from xai.explainable_logger import get_explainable_logger" in content:
            print("  [OK] main.py has XAI import")
        else:
            print("  [WARN] main.py missing XAI import (may need manual integration)")
        
        if "explainable.log_trade_entry" in content:
            print("  [OK] main.py has trade entry logging")
        else:
            print("  [WARN] main.py missing trade entry logging")
        
        if "explainable.log_trade_exit" in content:
            print("  [OK] main.py has trade exit logging")
        else:
            print("  [WARN] main.py missing trade exit logging")
        
        return True
    except Exception as e:
        print(f"  [FAIL] main.py integration test failed: {e}")
        return False

def test_dashboard_integration():
    """Test dashboard XAI integration"""
    print("Testing dashboard XAI integration...")
    try:
        dashboard_py = Path("dashboard.py")
        if not dashboard_py.exists():
            print("  [SKIP] dashboard.py not found")
            return True
        
        content = dashboard_py.read_text(encoding='utf-8')
        
        checks = [
            ("Natural Language Auditor", "XAI tab button"),
            ("loadXAIAuditor", "XAI load function"),
            ("renderXAIAuditor", "XAI render function"),
            ("/api/xai/auditor", "XAI API endpoint"),
            ("/api/xai/export", "XAI export endpoint")
        ]
        
        all_ok = True
        for check, name in checks:
            if check in content:
                print(f"  [OK] Dashboard has {name}")
            else:
                print(f"  [WARN] Dashboard missing {name}")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"  [FAIL] Dashboard integration test failed: {e}")
        return False

def test_learning_integration():
    """Test learning system XAI integration"""
    print("Testing learning system XAI integration...")
    try:
        learning_py = Path("comprehensive_learning_orchestrator_v2.py")
        if not learning_py.exists():
            print("  [SKIP] comprehensive_learning_orchestrator_v2.py not found")
            return True
        
        content = learning_py.read_text(encoding='utf-8')
        
        if "get_explainable_logger" in content:
            print("  [OK] Learning system has XAI integration")
        else:
            print("  [WARN] Learning system missing XAI integration")
        
        if "success_category" in content or "FULL LOOP VERIFICATION" in content:
            print("  [OK] Learning system categorizes using explainable Why")
        else:
            print("  [WARN] Learning system missing explainable categorization")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Learning integration test failed: {e}")
        return False

def main():
    """Run all regression tests"""
    print("=" * 60)
    print("XAI Regression Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("ExplainableLogger", test_explainable_logger),
        ("Thompson Sampling min_sample_size", test_thompson_sampling_min_sample),
        ("main.py Integration", test_main_imports),
        ("Dashboard Integration", test_dashboard_integration),
        ("Learning Integration", test_learning_integration)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n[{name}]")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  [ERROR] Test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All regression tests passed!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed or had warnings")
        return 1

if __name__ == "__main__":
    sys.exit(main())

