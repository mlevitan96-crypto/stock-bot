#!/usr/bin/env python3
"""
Verify and fix services - final comprehensive check
"""

from droplet_client import DropletClient
import time

c = DropletClient()

print("=" * 80)
print("SERVICE STATUS VERIFICATION & FIX")
print("=" * 80)
print()

# Check all services
print("Checking service status...")
stdout1, stderr1, code1 = c._execute('pgrep -f uw_flow_daemon')
stdout2, stderr2, code2 = c._execute('pgrep -f "python.*main.py"')
stdout3, stderr3, code3 = c._execute('pgrep -f deploy_supervisor')

uw_running = bool(stdout1)
bot_running = bool(stdout2)
supervisor_running = bool(stdout3)

print(f"Supervisor: {'[OK] RUNNING' if supervisor_running else '[ERROR] NOT RUNNING'}")
if stdout3:
    pids = stdout3.strip().split('\n')
    print(f"  PIDs: {', '.join(pids[:3])}")  # Show first 3
print()

print(f"UW Daemon (FP-1.1): {'[OK] RUNNING' if uw_running else '[ERROR] NOT RUNNING'}")
if stdout1:
    pids = stdout1.strip().split('\n')
    if len(pids) > 1:
        print(f"  [WARNING] Multiple instances: {', '.join(pids)}")
        print(f"  Cleaning up duplicates (keeping first)...")
        for pid in pids[1:]:
            c._execute(f'kill {pid} 2>/dev/null')
        time.sleep(1)
        # Recheck
        stdout1b, _, _ = c._execute('pgrep -f uw_flow_daemon')
        if stdout1b:
            print(f"  [OK] Single instance now (PID: {stdout1b.strip().split()[0]})")
    else:
        print(f"  PID: {pids[0]}")
print()

print(f"Trading Bot (FP-6.1): {'[OK] RUNNING' if bot_running else '[ERROR] NOT RUNNING'}")
if stdout2:
    pids = stdout2.strip().split('\n')
    if len(pids) > 1:
        print(f"  [WARNING] Multiple instances: {', '.join(pids)}")
        print(f"  Cleaning up duplicates (keeping first)...")
        for pid in pids[1:]:
            c._execute(f'kill {pid} 2>/dev/null')
        time.sleep(1)
        # Recheck
        stdout2b, _, _ = c._execute('pgrep -f "python.*main.py"')
        if stdout2b:
            print(f"  [OK] Single instance now (PID: {stdout2b.strip().split()[0]})")
    else:
        print(f"  PID: {pids[0]}")
print()

# Fix missing services
if not uw_running:
    print("Starting UW daemon...")
    # Use supervisor to start it properly
    # Or check if supervisor will start it
    print("  Checking if supervisor will start it...")
    time.sleep(5)  # Wait for supervisor monitoring loop
    stdout4, _, _ = c._execute('pgrep -f uw_flow_daemon')
    if stdout4:
        print(f"  [OK] UW daemon started by supervisor (PID: {stdout4.strip().split()[0]})")
    else:
        print("  [WARNING] Supervisor did not start UW daemon")
        print("  May need manual intervention")

if not bot_running:
    print("Starting trading bot...")
    print("  Checking if supervisor will start it...")
    time.sleep(5)  # Wait for supervisor monitoring loop
    stdout5, _, _ = c._execute('pgrep -f "python.*main.py"')
    if stdout5:
        print(f"  [OK] Trading bot started by supervisor (PID: {stdout5.strip().split()[0]})")
    else:
        print("  [WARNING] Supervisor did not start trading bot")
        print("  May need manual intervention")

print()
print("=" * 80)
print("FINAL STATUS")
print("=" * 80)
print()

# Final check
stdout6, _, _ = c._execute('pgrep -f uw_flow_daemon')
stdout7, _, _ = c._execute('pgrep -f "python.*main.py"')
stdout8, _, _ = c._execute('pgrep -f deploy_supervisor')

uw_final = bool(stdout6)
bot_final = bool(stdout7)
supervisor_final = bool(stdout8)

print(f"Supervisor: {'[OK] RUNNING' if supervisor_final else '[ERROR] NOT RUNNING'}")
print(f"UW Daemon (FP-1.1): {'[OK] RUNNING' if uw_final else '[ERROR] NOT RUNNING'}")
if stdout6:
    print(f"  PID: {stdout6.strip().split()[0]}")
print(f"Trading Bot (FP-6.1): {'[OK] RUNNING' if bot_final else '[ERROR] NOT RUNNING'}")
if stdout7:
    print(f"  PID: {stdout7.strip().split()[0]}")
print()

if uw_final and bot_final:
    print("[SUCCESS] All critical services are running!")
    print()
    print("Dashboard Status:")
    print("  - FP-1.1 (UW Daemon Running): Should show OK")
    print("  - FP-6.1 (Bot Running): Should show OK")
    print()
    print("Next steps:")
    print("  1. Refresh the dashboard to see updated status")
    print("  2. Monitor services for stability")
    print("  3. Check trading activity if market is open")
elif uw_final or bot_final:
    print("[PARTIAL] Some services running:")
    if uw_final:
        print("  [OK] UW daemon is running")
    else:
        print("  [ERROR] UW daemon is NOT running - check logs")
    if bot_final:
        print("  [OK] Trading bot is running")
    else:
        print("  [ERROR] Trading bot is NOT running - check logs")
else:
    print("[FAILED] Critical services not running")
    print("  Both UW daemon and trading bot failed to start")
    print("  Check supervisor logs: tail -100 /root/stock-bot/logs/supervisor.log")

c.close()
