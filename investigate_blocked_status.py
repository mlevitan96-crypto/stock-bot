#!/usr/bin/env python3
"""Investigate why trading readiness is BLOCKED"""

import json
from pathlib import Path
from failure_point_monitor import get_failure_point_monitor

def main():
    print("=" * 80)
    print("INVESTIGATING BLOCKED STATUS")
    print("=" * 80)
    
    monitor = get_failure_point_monitor()
    readiness = monitor.get_trading_readiness()
    
    print(f"\nOverall Readiness: {readiness['readiness']}")
    print(f"Critical Count: {readiness['critical_count']}")
    print(f"Warning Count: {readiness['warning_count']}")
    print(f"Total Checked: {readiness['total_checked']}")
    
    if readiness['critical_fps']:
        print(f"\nCRITICAL FAILURE POINTS:")
        print("-" * 80)
        for fp_id in readiness['critical_fps']:
            fp_status = readiness['failure_points'].get(fp_id, {})
            print(f"\n{fp_id}: {fp_status.get('name', 'Unknown')}")
            print(f"  Status: {fp_status.get('status', 'Unknown')}")
            print(f"  Error: {fp_status.get('last_error', 'None')}")
            print(f"  Category: {fp_status.get('category', 'Unknown')}")
            if fp_status.get('details'):
                print(f"  Details: {fp_status['details']}")
    
    if readiness['warning_fps']:
        print(f"\nWARNING FAILURE POINTS:")
        print("-" * 80)
        for fp_id in readiness['warning_fps']:
            fp_status = readiness['failure_points'].get(fp_id, {})
            print(f"\n{fp_id}: {fp_status.get('name', 'Unknown')}")
            print(f"  Status: {fp_status.get('status', 'Unknown')}")
            print(f"  Error: {fp_status.get('last_error', 'None')}")
    
    # Show all failure points
    print(f"\n\nALL FAILURE POINT STATUSES:")
    print("-" * 80)
    for fp_id, fp_status in sorted(readiness['failure_points'].items()):
        status = fp_status.get('status', 'Unknown')
        status_symbol = "[OK]" if status == "OK" else "[WARN]" if status == "WARN" else "[FAIL]"
        print(f"{status_symbol} {fp_id:8} {fp_status.get('name', 'Unknown'):40} {status}")
        if fp_status.get('last_error'):
            print(f"         Error: {fp_status['last_error']}")
    
    # Recommendations
    print(f"\n\nRECOMMENDATIONS:")
    print("-" * 80)
    if readiness['critical_fps']:
        print("CRITICAL ISSUES TO FIX:")
        for fp_id in readiness['critical_fps']:
            fp_status = readiness['failure_points'].get(fp_id, {})
            error = fp_status.get('last_error', 'Unknown error')
            print(f"  - {fp_id}: {error}")
            # Provide fix suggestions
            if "daemon" in fp_id.lower() or "FP-1.1" in fp_id:
                print("    → Fix: Restart UW daemon or check systemd status")
            elif "cache" in fp_id.lower() or "FP-1" in fp_id:
                print("    → Fix: Check UW daemon is running and polling")
            elif "weights" in fp_id.lower() or "FP-2.1" in fp_id:
                print("    → Fix: Run fix_adaptive_weights_init.py")
            elif "freeze" in fp_id.lower() or "FP-3.1" in fp_id:
                print("    → Fix: Remove freeze files from state/")
            elif "alpaca" in fp_id.lower() or "FP-4" in fp_id:
                print("    → Fix: Check Alpaca API credentials")
            elif "bot" in fp_id.lower() or "FP-6" in fp_id:
                print("    → Fix: Restart trading-bot.service")
    else:
        print("No critical issues - system should be READY")
    
    return readiness

if __name__ == "__main__":
    main()

