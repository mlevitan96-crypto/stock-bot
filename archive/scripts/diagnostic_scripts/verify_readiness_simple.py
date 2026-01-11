#!/usr/bin/env python3
"""Simple readiness verification without Unicode"""

from failure_point_monitor import get_failure_point_monitor

monitor = get_failure_point_monitor()
readiness = monitor.get_trading_readiness()

print(f"Readiness: {readiness['readiness']}")
print(f"Critical: {readiness['critical_count']}")
print(f"Warnings: {readiness['warning_count']}")
print(f"Total Checked: {readiness['total_checked']}")

if readiness['critical_fps']:
    print(f"\nCritical FPs: {', '.join(readiness['critical_fps'])}")
if readiness['warning_fps']:
    print(f"Warning FPs: {', '.join(readiness['warning_fps'])}")

print(f"\nStatus: {'READY' if readiness['readiness'] == 'READY' else 'NOT READY'}")

