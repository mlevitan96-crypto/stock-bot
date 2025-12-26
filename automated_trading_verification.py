#!/usr/bin/env python3
"""
Automated Trading Verification System
Runs before market open to verify trading will work
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def run_verification():
    """Run complete trading verification"""
    print("=" * 80)
    print("AUTOMATED TRADING VERIFICATION")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "overall_status": "UNKNOWN",
        "ready_for_trading": False
    }
    
    # 1. Failure Point Monitor
    print("1. FAILURE POINT MONITOR")
    print("-" * 80)
    try:
        from failure_point_monitor import get_failure_point_monitor
        monitor = get_failure_point_monitor()
        readiness = monitor.get_trading_readiness()
        
        results["tests"]["failure_points"] = {
            "status": readiness["readiness"],
            "critical_count": readiness["critical_count"],
            "warning_count": readiness["warning_count"],
            "passed": readiness["readiness"] == "READY"
        }
        
        print(f"Readiness: {readiness['readiness']}")
        print(f"Critical: {readiness['critical_count']}, Warnings: {readiness['warning_count']}")
        
        if readiness["readiness"] != "READY":
            print(f"[FAIL] Trading readiness: {readiness['readiness']}")
            if readiness.get("critical_fps"):
                print(f"Critical FPs: {', '.join(readiness['critical_fps'])}")
    except Exception as e:
        print(f"[ERROR] Failure point monitor failed: {e}")
        results["tests"]["failure_points"] = {"status": "ERROR", "error": str(e), "passed": False}
    
    # 2. Trading Readiness Test Harness
    print("\n2. TRADING READINESS TEST HARNESS")
    print("-" * 80)
    try:
        import subprocess
        result = subprocess.run(
            ['python3', 'trading_readiness_test_harness.py'],
            capture_output=True,
            timeout=60,
            cwd=Path.cwd()
        )
        
        passed = result.returncode == 0
        output = result.stdout.decode() if result.stdout else ""
        
        # Count passes/fails from output
        pass_count = output.count("[PASS]")
        fail_count = output.count("[FAIL]")
        
        results["tests"]["readiness_harness"] = {
            "status": "PASS" if passed else "FAIL",
            "pass_count": pass_count,
            "fail_count": fail_count,
            "passed": passed
        }
        
        print(f"Status: {'PASS' if passed else 'FAIL'}")
        print(f"Passed: {pass_count}, Failed: {fail_count}")
        
        if not passed:
            print(f"[FAIL] Test harness failed")
            print(output[-500:])  # Last 500 chars
    except Exception as e:
        print(f"[ERROR] Test harness failed: {e}")
        results["tests"]["readiness_harness"] = {"status": "ERROR", "error": str(e), "passed": False}
    
    # 3. Signal Injection Test
    print("\n3. SIGNAL INJECTION TEST")
    print("-" * 80)
    try:
        import subprocess
        result = subprocess.run(
            ['python3', 'inject_fake_signal_test.py'],
            capture_output=True,
            timeout=60,
            cwd=Path.cwd()
        )
        
        passed = result.returncode == 0
        output = result.stdout.decode() if result.stdout else ""
        
        would_execute = "would execute" in output.lower() or "all tests passed" in output.lower()
        
        results["tests"]["signal_injection"] = {
            "status": "PASS" if passed and would_execute else "FAIL",
            "would_execute": would_execute,
            "passed": passed and would_execute
        }
        
        print(f"Status: {'PASS' if passed and would_execute else 'FAIL'}")
        print(f"Would Execute: {would_execute}")
        
        if not (passed and would_execute):
            print(f"[FAIL] Signal injection test failed or would not execute")
            print(output[-500:])
    except Exception as e:
        print(f"[ERROR] Signal injection test failed: {e}")
        results["tests"]["signal_injection"] = {"status": "ERROR", "error": str(e), "passed": False}
    
    # Overall Status
    print("\n" + "=" * 80)
    print("OVERALL STATUS")
    print("=" * 80)
    
    all_passed = all(
        test.get("passed", False) 
        for test in results["tests"].values()
    )
    
    results["overall_status"] = "READY" if all_passed else "NOT_READY"
    results["ready_for_trading"] = all_passed
    
    if all_passed:
        print("✅ ALL VERIFICATIONS PASSED - READY FOR TRADING")
    else:
        print("❌ VERIFICATIONS FAILED - NOT READY FOR TRADING")
        print("\nFailed tests:")
        for test_name, test_result in results["tests"].items():
            if not test_result.get("passed", False):
                print(f"  - {test_name}: {test_result.get('status', 'UNKNOWN')}")
    
    # Save results
    results_file = Path("data/trading_verification_results.json")
    results_file.parent.mkdir(exist_ok=True)
    with results_file.open("w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Also save latest
    latest_file = Path("data/trading_verification_latest.json")
    with latest_file.open("w") as f:
        json.dump(results, f, indent=2, default=str)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_verification())

