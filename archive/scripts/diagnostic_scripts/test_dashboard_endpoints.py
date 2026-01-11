#!/usr/bin/env python3
"""
Dashboard Endpoint Comprehensive Test
Tests all dashboard API endpoints to ensure they're working correctly.
"""

import json
import requests
import sys
from pathlib import Path
from datetime import datetime, timezone

def test_endpoint(name, url, method="GET", expected_keys=None):
    """Test a single endpoint"""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*80)
    
    try:
        if method == "GET":
            resp = requests.get(url, timeout=5)
        else:
            resp = requests.post(url, timeout=5)
        
        print(f"Status Code: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"[FAIL] Non-200 status: {resp.status_code}")
            try:
                print(f"Response: {resp.text[:200]}")
            except:
                pass
            return False
        
        try:
            data = resp.json()
        except:
            print(f"[FAIL] Invalid JSON response")
            print(f"Response: {resp.text[:500]}")
            return False
        
        print(f"[OK] Response received")
        
        # Check for expected keys
        if expected_keys:
            missing = [key for key in expected_keys if key not in data]
            if missing:
                print(f"[WARN] Missing expected keys: {missing}")
            else:
                print(f"[OK] All expected keys present: {expected_keys}")
        
        # Show sample of data
        print(f"\nSample Response Keys: {list(data.keys())[:10]}")
        
        # Check for error field
        if "error" in data:
            print(f"[WARN] Response contains error field: {data['error']}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] Connection refused - endpoint may not be running")
        return False
    except requests.exceptions.Timeout:
        print(f"[FAIL] Request timeout")
        return False
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        return False

def test_dashboard_comprehensive():
    """Comprehensive dashboard endpoint testing"""
    print("="*80)
    print("DASHBOARD COMPREHENSIVE ENDPOINT TEST")
    print("="*80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    base_url = "http://localhost:5000"
    results = {}
    
    # Test 1: Root endpoint
    print("\n1. Testing Root Endpoint")
    results['root'] = test_endpoint("Root", f"{base_url}/")
    
    # Test 2: Health endpoint
    print("\n2. Testing Health Endpoint")
    results['health'] = test_endpoint("Health", f"{base_url}/health")
    
    # Test 3: Positions endpoint
    print("\n3. Testing Positions Endpoint")
    results['positions'] = test_endpoint(
        "Positions", 
        f"{base_url}/api/positions",
        expected_keys=["positions", "total_value", "unrealized_pnl"]
    )
    
    # Test 4: Health Status endpoint
    print("\n4. Testing Health Status Endpoint")
    results['health_status'] = test_endpoint(
        "Health Status",
        f"{base_url}/api/health_status",
        expected_keys=["last_order", "doctor", "market"]
    )
    
    # Test 5: SRE Health endpoint
    print("\n5. Testing SRE Health Endpoint")
    results['sre_health'] = test_endpoint(
        "SRE Health",
        f"{base_url}/api/sre/health",
        expected_keys=["overall_health", "signal_components", "market_open"]
    )
    
    # Test 6: Executive Summary endpoint
    print("\n6. Testing Executive Summary Endpoint")
    results['executive'] = test_endpoint(
        "Executive Summary",
        f"{base_url}/api/executive_summary",
        expected_keys=["trades", "total_trades", "pnl_metrics"]
    )
    
    # Test 7: XAI Auditor endpoint
    print("\n7. Testing XAI Auditor Endpoint")
    results['xai'] = test_endpoint(
        "XAI Auditor",
        f"{base_url}/api/xai/auditor",
        expected_keys=["trades", "weights", "status"]
    )
    
    # Test 8: Failure Points endpoint
    print("\n8. Testing Failure Points Endpoint")
    results['failure_points'] = test_endpoint(
        "Failure Points",
        f"{base_url}/api/failure_points",
        expected_keys=["readiness", "failure_points"]
    )
    
    # Test 9: Check if positions show entry_score
    print("\n9. Testing Entry Scores in Positions")
    try:
        resp = requests.get(f"{base_url}/api/positions", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            positions = data.get("positions", [])
            if positions:
                has_scores = all("entry_score" in p for p in positions)
                scores_present = [p.get("entry_score") for p in positions if p.get("entry_score", 0) > 0]
                print(f"[OK] Positions endpoint returns {len(positions)} positions")
                print(f"[{'OK' if has_scores else 'FAIL'}] All positions have entry_score field: {has_scores}")
                print(f"[INFO] Positions with non-zero scores: {len(scores_present)}/{len(positions)}")
                if scores_present:
                    print(f"[INFO] Sample scores: {scores_present[:5]}")
                results['positions_scores'] = has_scores
            else:
                print(f"[INFO] No positions open - cannot test scores")
                results['positions_scores'] = True  # N/A
        else:
            print(f"[FAIL] Could not fetch positions")
            results['positions_scores'] = False
    except Exception as e:
        print(f"[FAIL] Error checking positions scores: {e}")
        results['positions_scores'] = False
    
    # Test 10: Check Executive Summary shows scores
    print("\n10. Testing Entry Scores in Executive Summary")
    try:
        resp = requests.get(f"{base_url}/api/executive_summary", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            trades = data.get("trades", [])
            if trades:
                has_scores = all("entry_score" in t for t in trades)
                scores_present = [t.get("entry_score") for t in trades if t.get("entry_score", 0) > 0]
                print(f"[OK] Executive Summary returns {len(trades)} trades")
                print(f"[{'OK' if has_scores else 'FAIL'}] All trades have entry_score field: {has_scores}")
                print(f"[INFO] Trades with non-zero scores: {len(scores_present)}/{len(trades)}")
                if scores_present:
                    print(f"[INFO] Sample scores: {scores_present[:5]}")
                results['executive_scores'] = has_scores
            else:
                print(f"[INFO] No trades in executive summary - cannot test scores")
                results['executive_scores'] = True  # N/A
        else:
            print(f"[FAIL] Could not fetch executive summary")
            results['executive_scores'] = False
    except Exception as e:
        print(f"[FAIL] Error checking executive scores: {e}")
        results['executive_scores'] = False
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED")
        return True
    else:
        print(f"\n[WARNING] {total - passed} TESTS FAILED")
        return False

if __name__ == "__main__":
    success = test_dashboard_comprehensive()
    sys.exit(0 if success else 1)
