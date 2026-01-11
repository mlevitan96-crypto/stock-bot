#!/usr/bin/env python3
"""Verify trading readiness system is deployed on droplet"""

import subprocess
import sys
from pathlib import Path

def check_file_exists(filename):
    """Check if file exists"""
    return Path(filename).exists()

def main():
    print("=" * 80)
    print("DROPLET DEPLOYMENT VERIFICATION")
    print("=" * 80)
    
    files_to_check = [
        "failure_point_monitor.py",
        "trading_readiness_test_harness.py",
        "inject_fake_signal_test.py",
        "automated_trading_verification.py",
        "continuous_fp_monitoring.py",
        "pre_market_verification.sh",
        "COMPREHENSIVE_TRADING_FAILURE_POINTS.md",
        "TRADING_READINESS_COMPLETE.md",
        "FINAL_TRADING_READINESS_SYSTEM.md",
        "COMPLETE_SYSTEM_SUMMARY.md"
    ]
    
    print("\nChecking files...")
    all_exist = True
    for filename in files_to_check:
        exists = check_file_exists(filename)
        status = "OK" if exists else "MISSING"
        print(f"  {status:8} {filename}")
        if not exists:
            all_exist = False
    
    print("\nTesting imports...")
    try:
        from failure_point_monitor import get_failure_point_monitor
        monitor = get_failure_point_monitor()
        readiness = monitor.get_trading_readiness()
        print(f"  OK       failure_point_monitor.py (Readiness: {readiness['readiness']})")
    except Exception as e:
        print(f"  ERROR    failure_point_monitor.py: {e}")
        all_exist = False
    
    print("\n" + "=" * 80)
    if all_exist:
        print("DEPLOYMENT STATUS: COMPLETE")
        print("All files present and working")
        return 0
    else:
        print("DEPLOYMENT STATUS: INCOMPLETE")
        print("Some files missing or not working")
        print("\nRun: git pull origin main")
        return 1

if __name__ == "__main__":
    sys.exit(main())

