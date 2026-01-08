#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick verification that dashboard is working on Droplet"""

import sys
import io
import json
from droplet_client import DropletClient

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def verify_dashboard():
    """Verify dashboard is working with all fixes"""
    print("="*80)
    print("DASHBOARD VERIFICATION ON DROPLET")
    print("="*80)
    print()
    
    client = DropletClient()
    all_ok = True
    
    # 1. Check dashboard is running
    print("1. Checking dashboard process...")
    result = client._execute("ps aux | grep 'python.*dashboard.py' | grep -v grep")
    stdout = result[0] if isinstance(result, tuple) else result
    if stdout and stdout.strip():
        print(f"   [OK] Dashboard running")
        print(f"   PID: {stdout.split()[1] if len(stdout.split()) > 1 else 'N/A'}")
    else:
        print("   [FAIL] Dashboard not running!")
        all_ok = False
    print()
    
    # 2. Test health endpoint
    print("2. Testing health endpoint...")
    result = client._execute("curl -s http://localhost:5000/health")
    stdout = result[0] if isinstance(result, tuple) else result
    if stdout and '"status"' in stdout:
        print("   [OK] Health endpoint responding")
    else:
        print(f"   [FAIL] Health endpoint failed: {stdout[:100]}")
        all_ok = False
    print()
    
    # 3. Test positions endpoint with entry scores
    print("3. Testing positions endpoint (entry scores)...")
    result = client._execute("curl -s http://localhost:5000/api/positions")
    stdout = result[0] if isinstance(result, tuple) else result
    if stdout:
        try:
            data = json.loads(stdout)
            positions = data.get("positions", [])
            if positions:
                has_scores = all("entry_score" in p for p in positions)
                if has_scores:
                    scores = [p.get("entry_score", 0) for p in positions]
                    print(f"   [OK] Positions endpoint returns entry scores")
                    print(f"   Found {len(positions)} positions with scores: {scores}")
                else:
                    print("   [FAIL] Some positions missing entry_score")
                    all_ok = False
            else:
                print("   [INFO] No positions open (cannot verify scores)")
        except Exception as e:
            print(f"   [FAIL] Error parsing positions: {e}")
            all_ok = False
    else:
        print("   [FAIL] Positions endpoint returned no data")
        all_ok = False
    print()
    
    # 4. Test SRE health with signal funnel
    print("4. Testing SRE health (signal funnel & stagnation watchdog)...")
    result = client._execute("curl -s http://localhost:5000/api/sre/health")
    stdout = result[0] if isinstance(result, tuple) else result
    if stdout:
        try:
            data = json.loads(stdout)
            has_funnel = "signal_funnel" in data
            has_watchdog = "stagnation_watchdog" in data
            
            if has_funnel:
                funnel = data["signal_funnel"]
                print("   [OK] Signal Funnel present")
                print(f"      Alerts: {funnel.get('alerts', 0)}, Parsed: {funnel.get('parsed', 0)}")
                print(f"      Scored >3.0: {funnel.get('scored_above_threshold', 0)}, Orders: {funnel.get('orders_sent', 0)}")
            else:
                print("   [FAIL] Signal Funnel missing")
                all_ok = False
                
            if has_watchdog:
                watchdog = data["stagnation_watchdog"]
                print(f"   [OK] Stagnation Watchdog present: {watchdog.get('status', 'UNKNOWN')}")
            else:
                print("   [FAIL] Stagnation Watchdog missing")
                all_ok = False
        except Exception as e:
            print(f"   [FAIL] Error parsing SRE health: {e}")
            all_ok = False
    else:
        print("   [FAIL] SRE health endpoint returned no data")
        all_ok = False
    print()
    
    # 5. Test health status endpoint
    print("5. Testing health status endpoint...")
    result = client._execute("curl -s http://localhost:5000/api/health_status")
    stdout = result[0] if isinstance(result, tuple) else result
    if stdout:
        try:
            data = json.loads(stdout)
            if "last_order" in data and "doctor" in data:
                print("   [OK] Health status endpoint working")
                print(f"      Last Order: {data['last_order'].get('age_sec', 'N/A')}s ago")
                print(f"      Doctor: {data['doctor'].get('age_sec', 'N/A')}s ago")
            else:
                print("   [FAIL] Missing required fields")
                all_ok = False
        except Exception as e:
            print(f"   [FAIL] Error parsing health status: {e}")
            all_ok = False
    else:
        print("   [FAIL] Health status endpoint returned no data")
        all_ok = False
    print()
    
    # Summary
    print("="*80)
    if all_ok:
        print("[SUCCESS] All dashboard endpoints are working correctly!")
        print("Dashboard fixes deployed and verified successfully.")
    else:
        print("[WARNING] Some checks failed - review output above")
    print("="*80)
    
    return all_ok

if __name__ == "__main__":
    success = verify_dashboard()
    sys.exit(0 if success else 1)
