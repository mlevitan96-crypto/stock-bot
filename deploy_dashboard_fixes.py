#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy dashboard fixes to Droplet and verify everything works.
"""

import json
import time
import sys
import io
from droplet_client import DropletClient

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def deploy_and_verify():
    """Deploy dashboard fixes and verify everything works."""
    print("="*80)
    print("DASHBOARD FIXES DEPLOYMENT TO DROPLET")
    print("="*80)
    print()
    
    client = DropletClient()
    
    # Step 1: Check current status
    print("Step 1: Checking current Droplet status...")
    print("-" * 80)
    try:
        status_result = client._execute("cd /root/stock-bot && ps aux | grep -E '(dashboard|deploy_supervisor|main.py)' | grep -v grep")
        stdout, stderr, exit_code = status_result if isinstance(status_result, tuple) else (status_result, "", 0)
        print("Current processes:")
        print(stdout if stdout else "No processes found")
    except Exception as e:
        print(f"Warning: Could not check status: {e}")
    print()
    
    # Step 2: Pull latest changes
    print("Step 2: Pulling latest changes from GitHub...")
    print("-" * 80)
    try:
        git_pull_result = client._execute("cd /root/stock-bot && git pull origin main")
        stdout, stderr, exit_code = git_pull_result if isinstance(git_pull_result, tuple) else (git_pull_result, "", 0)
        print(stdout)
        if stderr:
            print(f"Stderr: {stderr}")
        if exit_code != 0:
            print(f"[WARN] Git pull exit code: {exit_code}")
        if stdout and ("error" in stdout.lower() or "conflict" in stdout.lower()):
            print("[WARN] Git pull had issues!")
        else:
            print("[OK] Git pull successful")
    except Exception as e:
        print(f"[ERROR] Error during git pull: {e}")
        return False
    print()
    
    # Step 3: Check if dashboard needs restart
    print("Step 3: Checking dashboard service...")
    print("-" * 80)
    try:
        # Check if dashboard is running
        dashboard_result = client._execute("ps aux | grep 'python.*dashboard.py' | grep -v grep")
        stdout, stderr, exit_code = dashboard_result if isinstance(dashboard_result, tuple) else (dashboard_result, "", 0)
        dashboard_check = stdout.strip() if stdout else ""
        if not dashboard_check or len(dashboard_check) == 0:
            print("[WARN] Dashboard not running, will need to start it")
        else:
            print("[OK] Dashboard is running")
            print(f"Process: {dashboard_check[:100]}")
    except Exception as e:
        print(f"Warning: Could not check dashboard: {e}")
    print()
    
    # Step 4: Restart dashboard (if using supervisor, just kill it and let it restart)
    print("Step 4: Restarting dashboard service...")
    print("-" * 80)
    try:
        # Kill dashboard process (supervisor will restart it)
        kill_result = client._execute("pkill -f 'python.*dashboard.py'")
        stdout, stderr, exit_code = kill_result if isinstance(kill_result, tuple) else (kill_result, "", 0)
        print("Dashboard process killed (supervisor will restart)")
        print("Waiting 10 seconds for restart...")
        time.sleep(10)
        
        # Verify dashboard restarted
        dashboard_result = client._execute("ps aux | grep 'python.*dashboard.py' | grep -v grep")
        stdout, stderr, exit_code = dashboard_result if isinstance(dashboard_result, tuple) else (dashboard_result, "", 0)
        dashboard_check = stdout.strip() if stdout else ""
        if dashboard_check and len(dashboard_check) > 0:
            print("[OK] Dashboard restarted successfully")
            print(f"Process: {dashboard_check[:100]}")
        else:
            print("[WARN] Dashboard may not have restarted - checking supervisor...")
            # Check supervisor
            supervisor_result = client._execute("ps aux | grep 'deploy_supervisor' | grep -v grep")
            stdout, stderr, exit_code = supervisor_result if isinstance(supervisor_result, tuple) else (supervisor_result, "", 0)
            supervisor_check = stdout.strip() if stdout else ""
            if supervisor_check:
                print("Supervisor is running, dashboard should restart automatically")
                print("Waiting additional 10 seconds...")
                time.sleep(10)
                dashboard_result = client._execute("ps aux | grep 'python.*dashboard.py' | grep -v grep")
                stdout, stderr, exit_code = dashboard_result if isinstance(dashboard_result, tuple) else (dashboard_result, "", 0)
                dashboard_check = stdout.strip() if stdout else ""
                if dashboard_check:
                    print("[OK] Dashboard restarted")
                else:
                    print("[ERROR] Dashboard did not restart - manual intervention needed")
            else:
                print("[ERROR] Supervisor not running - dashboard may need manual start")
    except Exception as e:
        print(f"[WARN] Error restarting dashboard: {e}")
    print()
    
    # Step 5: Test endpoints
    print("Step 5: Testing dashboard endpoints...")
    print("-" * 80)
    
    endpoints_to_test = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/api/positions", "Positions endpoint"),
        ("/api/health_status", "Health status endpoint"),
        ("/api/sre/health", "SRE health endpoint"),
        ("/api/executive_summary", "Executive summary endpoint"),
    ]
    
    all_passed = True
    for endpoint, description in endpoints_to_test:
        try:
            test_result = client._execute(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:5000{endpoint}")
            stdout, stderr, exit_code = test_result if isinstance(test_result, tuple) else (test_result, "", 0)
            status_code = stdout.strip() if stdout else ""
            if status_code == "200":
                print(f"[OK] {description}: HTTP {status_code}")
            else:
                print(f"[FAIL] {description}: HTTP {status_code}")
                all_passed = False
        except Exception as e:
            print(f"[FAIL] {description}: Error - {e}")
            all_passed = False
    print()
    
    # Step 6: Verify specific functionality
    print("Step 6: Verifying specific functionality...")
    print("-" * 80)
    
    # Test positions endpoint for entry scores
    try:
        positions_result = client._execute("curl -s http://localhost:5000/api/positions")
        stdout, stderr, exit_code = positions_result if isinstance(positions_result, tuple) else (positions_result, "", 0)
        positions_json = stdout if stdout else ""
        if positions_json:
            import json as json_module
            try:
                positions_data = json_module.loads(positions_json)
                positions = positions_data.get("positions", [])
                if positions:
                    has_scores = all("entry_score" in p for p in positions)
                    if has_scores:
                        print(f"[OK] Positions endpoint returns entry scores (found {len(positions)} positions)")
                    else:
                        print(f"[WARN] Positions endpoint missing entry_score field in some positions")
                        all_passed = False
                else:
                    print("[INFO] No positions currently open (cannot verify scores)")
            except:
                print("[WARN] Could not parse positions JSON")
        else:
            print("[FAIL] Positions endpoint returned no data")
            all_passed = False
    except Exception as e:
        print(f"[WARN] Error checking positions: {e}")
    print()
    
    # Test SRE health for signal funnel
    try:
        sre_result = client._execute("curl -s http://localhost:5000/api/sre/health")
        stdout, stderr, exit_code = sre_result if isinstance(sre_result, tuple) else (sre_result, "", 0)
        sre_json = stdout if stdout else ""
        if sre_json:
            import json as json_module
            try:
                sre_data = json_module.loads(sre_json)
                if "signal_funnel" in sre_data:
                    funnel = sre_data["signal_funnel"]
                    print(f"[OK] Signal Funnel present in SRE health")
                    print(f"   Alerts: {funnel.get('alerts', 0)}, Parsed: {funnel.get('parsed', 0)}, Scored: {funnel.get('scored_above_threshold', 0)}, Orders: {funnel.get('orders_sent', 0)}")
                else:
                    print("[WARN] Signal Funnel missing from SRE health")
                if "stagnation_watchdog" in sre_data:
                    watchdog = sre_data["stagnation_watchdog"]
                    print(f"[OK] Stagnation Watchdog present: {watchdog.get('status', 'UNKNOWN')}")
                else:
                    print("[WARN] Stagnation Watchdog missing from SRE health")
            except Exception as e:
                print(f"[WARN] Could not parse SRE health JSON: {e}")
        else:
            print("[WARN] SRE health endpoint returned no data")
    except Exception as e:
        print(f"[WARN] Error checking SRE health: {e}")
    print()
    
    # Step 7: Final summary
    print("="*80)
    print("DEPLOYMENT SUMMARY")
    print("="*80)
    if all_passed:
        print("[SUCCESS] All tests passed! Dashboard is operational.")
    else:
        print("[WARNING] Some tests failed - please review the output above")
    print()
    print("Next steps:")
    print("1. Open dashboard in browser: http://your-droplet-ip:5000")
    print("2. Verify all tabs load correctly")
    print("3. Check Positions tab for entry scores")
    print("4. Check SRE tab for Signal Funnel and Stagnation Watchdog")
    print("5. Monitor logs: tail -f /root/stock-bot/logs/dashboard*.log")
    
    return all_passed

if __name__ == "__main__":
    success = deploy_and_verify()
    exit(0 if success else 1)
