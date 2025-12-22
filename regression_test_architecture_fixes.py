#!/usr/bin/env python3
"""
Regression Tests for Architecture Fixes
=========================================

Tests that all architecture fixes work correctly and don't break existing functionality.
"""

import sys
from pathlib import Path

def test_registry_imports():
    """Test that registry imports work correctly"""
    try:
        from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles
        assert hasattr(StateFiles, 'FAIL_COUNTER')
        assert hasattr(StateFiles, 'SMART_POLLER')
        assert hasattr(StateFiles, 'CHAMPIONS')
        assert hasattr(StateFiles, 'PRE_MARKET_FREEZE')
        assert hasattr(CacheFiles, 'GOVERNANCE_EVENTS')
        assert hasattr(CacheFiles, 'EXECUTION_QUALITY')
        assert hasattr(CacheFiles, 'UW_ATTRIBUTION')
        assert hasattr(LogFiles, 'RECONCILE')
        assert hasattr(ConfigFiles, 'THEME_RISK')
        print("OK: Registry imports work correctly")
        return True
    except Exception as e:
        print(f"FAIL: Registry imports failed: {e}")
        return False

def test_main_imports():
    """Test that main.py imports work"""
    try:
        # Test that main.py can be imported without errors
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", "main.py")
        if spec and spec.loader:
            # Just check syntax, don't actually import (would run code)
            with open("main.py", 'r', encoding='utf-8') as f:
                code = f.read()
                compile(code, "main.py", "exec")
            print("OK: main.py syntax is valid")
        return True
    except SyntaxError as e:
        print(f"FAIL: main.py syntax error: {e}")
        return False
    except Exception as e:
        print(f"FAIL: main.py import check failed: {e}")
        return False

def test_path_resolution():
    """Test that registry paths resolve correctly"""
    try:
        from config.registry import StateFiles, CacheFiles, LogFiles, ConfigFiles
        
        # Test that paths are Path objects
        assert isinstance(StateFiles.FAIL_COUNTER, Path)
        assert isinstance(StateFiles.SMART_POLLER, Path)
        assert isinstance(CacheFiles.GOVERNANCE_EVENTS, Path)
        assert isinstance(LogFiles.RECONCILE, Path)
        assert isinstance(ConfigFiles.THEME_RISK, Path)
        
        # Test that paths have correct structure
        assert str(StateFiles.FAIL_COUNTER).endswith("fail_counter.json")
        assert str(CacheFiles.GOVERNANCE_EVENTS).endswith("governance_events.jsonl")
        
        print("OK: Path resolution works correctly")
        return True
    except Exception as e:
        print(f"FAIL: Path resolution failed: {e}")
        return False

def test_v2_orchestrator_import():
    """Test that v2 orchestrator can be imported"""
    try:
        from comprehensive_learning_orchestrator_v2 import (
            load_learning_state,
            run_comprehensive_learning,
            run_historical_backfill
        )
        print("OK: v2 orchestrator imports work correctly")
        return True
    except Exception as e:
        print(f"FAIL: v2 orchestrator import failed: {e}")
        return False

def test_no_deprecated_imports():
    """Test that deprecated imports are not present in critical files"""
    critical_files = ["main.py", "comprehensive_learning_scheduler.py"]
    issues = []
    
    for file_path in critical_files:
        path = Path(file_path)
        if path.exists():
            content = path.read_text(encoding='utf-8', errors='ignore')
            if 'from comprehensive_learning_orchestrator import' in content:
                # Check it's not the old one (without _v2)
                if 'from comprehensive_learning_orchestrator import' in content and '_v2' not in content.split('from comprehensive_learning_orchestrator import')[0]:
                    issues.append(f"{file_path} has deprecated import")
    
    if issues:
        print(f"FAIL: Found deprecated imports: {issues}")
        return False
    else:
        print("OK: No deprecated imports in critical files")
        return True

def run_all_tests():
    """Run all regression tests"""
    print("=" * 80)
    print("REGRESSION TESTS FOR ARCHITECTURE FIXES")
    print("=" * 80)
    print()
    
    tests = [
        ("Registry Imports", test_registry_imports),
        ("Main Imports", test_main_imports),
        ("Path Resolution", test_path_resolution),
        ("V2 Orchestrator Import", test_v2_orchestrator_import),
        ("No Deprecated Imports", test_no_deprecated_imports),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"Running: {name}...")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"FAIL: {name} raised exception: {e}")
            results.append((name, False))
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All regression tests passed!")
        return 0
    else:
        print("FAIL: Some regression tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
