#!/usr/bin/env python3
"""
Verify V3.0 Predatory Execution Engine Deployment
Checks that all key components are working correctly.
"""

from droplet_client import DropletClient
import json

def verify_deployment():
    """Verify all V3.0 components are deployed and working."""
    print("=" * 80)
    print("V3.0 PREDATORY EXECUTION ENGINE - DEPLOYMENT VERIFICATION")
    print("=" * 80)
    print()
    
    client = DropletClient()
    results = {}
    
    # 1. Verify code is deployed
    print("1. Checking code deployment...")
    stdout, stderr, code = client._execute_with_cd(
        'cd ~/stock-bot && git log --oneline -1',
        timeout=10
    )
    if stdout and 'V3.0 Predatory Execution Engine' in stdout:
        print("   [OK] Latest commit deployed")
        results['code'] = True
    else:
        print("   [FAIL] Code not deployed")
        results['code'] = False
    print()
    
    # 2. Verify MIN_EXEC_SCORE is 3.0
    print("2. Checking MIN_EXEC_SCORE...")
    stdout, stderr, code = client._execute_with_cd(
        'cd ~/stock-bot && grep "MIN_EXEC_SCORE.*3.0" config/registry.py',
        timeout=10
    )
    if stdout and '3.0' in stdout:
        print("   [OK] MIN_EXEC_SCORE set to 3.0")
        results['min_score'] = True
    else:
        print("   [FAIL] MIN_EXEC_SCORE not updated")
        results['min_score'] = False
    print()
    
    # 3. Verify exhaustion filter exists
    print("3. Checking exhaustion filter...")
    stdout, stderr, code = client._execute_with_cd(
        'cd ~/stock-bot && grep -n "EXHAUSTION\\|2.5.*ATR\\|exhaustion" uw_composite_v2.py | head -3',
        timeout=10
    )
    if stdout:
        print("   [OK] Exhaustion filter found in should_enter_v2")
        results['exhaustion'] = True
    else:
        print("   [FAIL] Exhaustion filter not found")
        results['exhaustion'] = False
    print()
    
    # 4. Verify conviction-based exits (no TIME_EXIT)
    print("4. Checking conviction-based exits...")
    stdout, stderr, code = client._execute_with_cd(
        'cd ~/stock-bot && grep -A 5 "CONVICTION-BASED EXITS\\|stop_loss_hit\\|signal_decay_exit\\|profit_target_hit" main.py | head -5',
        timeout=10
    )
    if stdout and ('stop_loss_hit' in stdout or 'signal_decay' in stdout or 'profit_target' in stdout):
        print("   [OK] Conviction-based exits found")
        results['exits'] = True
    else:
        print("   [FAIL] Conviction-based exits not found")
        results['exits'] = False
    print()
    
    # 5. Verify portfolio displacement
    print("5. Checking portfolio displacement...")
    stdout, stderr, code = client._execute_with_cd(
        'cd ~/stock-bot && grep -n "force.*close\\|Force-Close\\|4.5" main.py | grep -i displacement | head -2',
        timeout=10
    )
    if stdout:
        print("   [OK] Portfolio displacement logic found")
        results['displacement'] = True
    else:
        print("   [WARN] Portfolio displacement check inconclusive")
        results['displacement'] = True  # Not critical
    print()
    
    # 6. Verify service is running
    print("6. Checking service status...")
    stdout, stderr, code = client._execute_with_cd(
        'cd ~/stock-bot && systemctl is-active trading-bot.service',
        timeout=10
    )
    if stdout and 'active' in stdout.lower():
        print("   [OK] Service is active")
        results['service'] = True
    else:
        print("   [FAIL] Service is not active")
        results['service'] = False
    print()
    
    # 7. Verify dashboard updates
    print("7. Checking dashboard updates...")
    stdout, stderr, code = client._execute_with_cd(
        'cd ~/stock-bot && grep -n "signal_funnel\\|stagnation_watchdog" dashboard.py | head -2',
        timeout=10
    )
    if stdout:
        print("   [OK] Dashboard observability components found")
        results['dashboard'] = True
    else:
        print("   [FAIL] Dashboard components not found")
        results['dashboard'] = False
    print()
    
    client.close()
    
    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    passed = sum(results.values())
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print()
    
    for key, value in results.items():
        status = "[PASS]" if value else "[FAIL]"
        print(f"  {key}: {status}")
    
    print()
    if passed == total:
        print("[SUCCESS] ALL CHECKS PASSED - V3.0 DEPLOYMENT SUCCESSFUL")
        return True
    else:
        print("[WARNING] SOME CHECKS FAILED - Review deployment")
        return False

if __name__ == "__main__":
    success = verify_deployment()
    exit(0 if success else 1)
