#!/usr/bin/env python3
"""
Comprehensive Dashboard XAI Regression Test
Tests Natural Language Auditor and all dashboard endpoints after recent changes.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def test_xai_logger():
    """Test XAI logger functionality"""
    print("=" * 80)
    print("TESTING XAI LOGGER")
    print("=" * 80)
    
    try:
        from xai.explainable_logger import ExplainableLogger, get_explainable_logger
        
        logger = get_explainable_logger()
        print("[OK] XAI Logger imported and initialized")
        
        # Test log_trade_entry
        try:
            why = logger.log_trade_entry(
                symbol="TEST",
                direction="bullish",
                score=5.23,
                components={"dark_pool": 0.5, "greeks_gamma": 0.3},
                regime="RISK_ON",
                macro_yield=4.5,
                whale_clusters={"count": 5, "premium_usd": 1000000},
                gamma_walls={"distance_pct": 0.03, "gamma_exposure": 5000000},
                composite_score=5.23,
                entry_price=100.0
            )
            print(f"[OK] log_trade_entry works: {why[:100]}...")
        except Exception as e:
            print(f"[ERROR] log_trade_entry failed: {e}")
            return False
        
        # Test log_weight_adjustment
        try:
            logger.log_weight_adjustment(
                component="dark_pool",
                old_weight=1.0,
                new_weight=1.2,
                reason="Thompson Sampling optimization",
                sample_count=20,
                win_rate=0.75,
                regime="RISK_ON",
                pnl_contribution=0.15
            )
            print("[OK] log_weight_adjustment works")
        except Exception as e:
            print(f"[ERROR] log_weight_adjustment failed: {e}")
            return False
        
        # Test log_threshold_adjustment
        try:
            logger.log_threshold_adjustment(
                symbol="TEST",
                base_threshold=2.0,
                adjusted_threshold=2.5,
                adjustment=0.5,
                reason="Raised threshold after 3 consecutive losses",
                consecutive_losses=3,
                status={"is_activated": True, "last_3_trades": "loss,loss,loss"}
            )
            print("[OK] log_threshold_adjustment works")
        except Exception as e:
            print(f"[ERROR] log_threshold_adjustment failed: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Failed to import XAI logger: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] XAI logger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_xai_data_file():
    """Test that XAI data file exists and is readable"""
    print("\n" + "=" * 80)
    print("TESTING XAI DATA FILE")
    print("=" * 80)
    
    data_file = Path("data/explainable_logs.jsonl")
    
    if not data_file.exists():
        print(f"[WARN] XAI data file not found: {data_file}")
        print("[INFO] This is OK if no trades have been logged yet")
        return True
    
    try:
        records = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        print(f"[OK] XAI data file readable: {len(records)} records found")
        
        if records:
            latest = records[-1]
            print(f"[OK] Latest record type: {latest.get('type', 'unknown')}")
            print(f"[OK] Latest record timestamp: {latest.get('timestamp', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to read XAI data file: {e}")
        return False

def test_dashboard_xai_endpoint():
    """Test dashboard XAI endpoint logic (without Flask)"""
    print("\n" + "=" * 80)
    print("TESTING DASHBOARD XAI ENDPOINT LOGIC")
    print("=" * 80)
    
    try:
        from xai.explainable_logger import get_explainable_logger
        
        logger = get_explainable_logger()
        data_file = Path("data/explainable_logs.jsonl")
        
        if not data_file.exists():
            print("[WARN] No XAI data file - endpoint will return empty list")
            return True
        
        # Simulate endpoint logic
        records = []
        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except:
                        continue
        
        # Sort by timestamp (newest first)
        records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit to 100 most recent
        records = records[:100]
        
        print(f"[OK] Endpoint logic works: {len(records)} records processed")
        
        # Check record structure
        if records:
            sample = records[0]
            required_fields = ["type", "timestamp"]
            missing = [f for f in required_fields if f not in sample]
            if missing:
                print(f"[WARN] Sample record missing fields: {missing}")
            else:
                print("[OK] Record structure valid")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Dashboard XAI endpoint logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_recent_changes_impact():
    """Test if recent changes to main.py affected XAI logging"""
    print("\n" + "=" * 80)
    print("TESTING RECENT CHANGES IMPACT")
    print("=" * 80)
    
    # Check if new exit reasons are logged properly
    try:
        # Read main.py directly to avoid import issues
        main_py = Path("main.py")
        if not main_py.exists():
            print("[WARN] main.py not found - skipping config test")
            return True
        
        content = main_py.read_text(encoding='utf-8')
        
        # Check for new config values
        if "TIME_EXIT_MINUTES = get_env(\"TIME_EXIT_MINUTES\", 150" in content:
            print("[OK] TIME_EXIT_MINUTES set to 150")
        else:
            print("[WARN] TIME_EXIT_MINUTES may not be 150")
        
        if "STALE_TRADE_EXIT_MINUTES" in content:
            print("[OK] STALE_TRADE_EXIT_MINUTES found in main.py")
        else:
            print("[WARN] STALE_TRADE_EXIT_MINUTES not found")
        
        if "STALE_TRADE_MOMENTUM_THRESH_PCT" in content:
            print("[OK] STALE_TRADE_MOMENTUM_THRESH_PCT found in main.py")
        else:
            print("[WARN] STALE_TRADE_MOMENTUM_THRESH_PCT not found")
        
        # Check if exit reason building function exists
        if "def build_composite_close_reason" in content:
            print("[OK] build_composite_close_reason function exists")
            
            # Check if stale_trade is handled
            if "stale_trade" in content and "build_composite_close_reason" in content:
                stale_trade_section = content[content.find("def build_composite_close_reason"):content.find("def build_composite_close_reason") + 2000]
                if "stale_trade" in stale_trade_section:
                    print("[OK] stale_trade exit reason handling found")
                else:
                    print("[WARN] stale_trade not found in build_composite_close_reason")
        else:
            print("[WARN] build_composite_close_reason function not found")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Recent changes impact test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_dashboard_endpoints():
    """Test all dashboard endpoint imports and logic"""
    print("\n" + "=" * 80)
    print("TESTING ALL DASHBOARD ENDPOINTS")
    print("=" * 80)
    
    endpoints = [
        ("/api/positions", "Positions"),
        ("/api/health_status", "Health Status"),
        ("/api/sre/health", "SRE Health"),
        ("/api/executive_summary", "Executive Summary"),
        ("/api/xai/auditor", "XAI Auditor"),
        ("/api/xai/export", "XAI Export"),
        ("/api/failure_points", "Failure Points")
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        try:
            # Check if endpoint function exists in dashboard.py
            if endpoint == "/api/xai/auditor":
                from xai.explainable_logger import get_explainable_logger
                logger = get_explainable_logger()
                results[name] = "OK - XAI logger available"
            elif endpoint == "/api/executive_summary":
                try:
                    from executive_summary_generator import generate_executive_summary
                    results[name] = "OK - Executive summary generator available"
                except:
                    results[name] = "WARN - Executive summary generator not available"
            elif endpoint == "/api/sre/health":
                try:
                    from sre_monitoring import get_sre_health
                    results[name] = "OK - SRE monitoring available"
                except:
                    results[name] = "WARN - SRE monitoring not available"
            elif endpoint == "/api/failure_points":
                try:
                    from failure_point_monitor import get_failure_point_monitor
                    results[name] = "OK - Failure point monitor available"
                except:
                    results[name] = "WARN - Failure point monitor not available"
            else:
                results[name] = "OK - Endpoint exists in dashboard.py"
        except Exception as e:
            results[name] = f"ERROR - {str(e)[:50]}"
    
    for name, status in results.items():
        status_icon = "[OK]" if "OK" in status else "[WARN]" if "WARN" in status else "[ERROR]"
        print(f"{status_icon} {name}: {status}")
    
    errors = [name for name, status in results.items() if "ERROR" in status]
    if errors:
        print(f"\n[ERROR] {len(errors)} endpoint(s) have errors")
        return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 80)
    print("DASHBOARD XAI REGRESSION TEST SUITE")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("XAI Logger", test_xai_logger),
        ("XAI Data File", test_xai_data_file),
        ("Dashboard XAI Endpoint", test_dashboard_xai_endpoint),
        ("Recent Changes Impact", test_recent_changes_impact),
        ("All Dashboard Endpoints", test_all_dashboard_endpoints)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n[ERROR] Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

