#!/usr/bin/env python3
"""
Final comprehensive service fix - ensures all services are running
Uses non-blocking commands to avoid SSH timeouts
"""

from droplet_client import DropletClient
import time

c = DropletClient()

print("=" * 80)
print("FINAL SERVICE FIX")
print("=" * 80)
print()

# Step 1: Check current status
print("[1/4] Current service status:")
stdout1, stderr1, code1 = c._execute('pgrep -f uw_flow_daemon')
stdout2, stderr2, code2 = c._execute('pgrep -f "python.*main.py"')
stdout3, stderr3, code3 = c._execute('pgrep -f deploy_supervisor')

uw_running = bool(stdout1)
bot_running = bool(stdout2)
supervisor_running = bool(stdout3)

print(f"  Supervisor: {'RUNNING' if supervisor_running else 'NOT RUNNING'}")
if stdout3:
    print(f"    PID: {stdout3.strip().split()[0] if stdout3.strip() else 'N/A'}")
print(f"  UW Daemon (FP-1.1): {'RUNNING' if uw_running else 'NOT RUNNING'}")
if stdout1:
    pids = stdout1.strip().split('\n')
    if len(pids) == 1:
        print(f"    PID: {pids[0]}")
    else:
        print(f"    [WARNING] Multiple instances: {', '.join(pids)}")
        print(f"    Cleaning up duplicates...")
        for pid in pids[1:]:
            c._execute(f'kill {pid}')
        time.sleep(1)
print(f"  Trading Bot (FP-6.1): {'RUNNING' if bot_running else 'NOT RUNNING'}")
if stdout2:
    print(f"    PID: {stdout2.strip()}")
print()

# Step 2: Fix UW daemon if needed
if not uw_running:
    print("[2/4] Starting UW daemon...")
    # Use a command that returns immediately
    c._execute('cd /root/stock-bot && /root/stock-bot/venv/bin/python uw_flow_daemon.py > /dev/null 2>&1 &')
    time.sleep(3)
    stdout4, stderr4, code4 = c._execute('pgrep -f uw_flow_daemon')
    if stdout4:
        print(f"  [OK] UW daemon started (PID: {stdout4.strip().split()[0]})")
    else:
        print("  [ERROR] UW daemon failed to start")
else:
    print("[2/4] UW daemon already running, skipping")
print()

# Step 3: Fix trading bot if needed
if not bot_running:
    print("[3/4] Starting trading bot...")
    # Use a command that returns immediately
    c._execute('cd /root/stock-bot && /root/stock-bot/venv/bin/python main.py > /dev/null 2>&1 &')
    time.sleep(3)
    stdout5, stderr5, code5 = c._execute('pgrep -f "python.*main.py"')
    if stdout5:
        print(f"  [OK] Trading bot started (PID: {stdout5.strip()})")
    else:
        print("  [ERROR] Trading bot failed to start")
        print("  Check for errors in main.py startup")
else:
    print("[3/4] Trading bot already running, skipping")
print()

# Step 4: Final verification
print("[4/4] Final verification...")
time.sleep(2)  # Give services time to fully start

stdout6, stderr6, code6 = c._execute('pgrep -f uw_flow_daemon')
stdout7, stderr7, code7 = c._execute('pgrep -f "python.*main.py"')
stdout8, stderr8, code8 = c._execute('pgrep -f deploy_supervisor')

uw_final = bool(stdout6)
bot_final = bool(stdout7)
supervisor_final = bool(stdout8)

print()
print("=" * 80)
print("FINAL STATUS")
print("=" * 80)
print()
print(f"Supervisor: {'✓ RUNNING' if supervisor_final else '✗ NOT RUNNING'}")
print(f"UW Daemon (FP-1.1): {'✓ RUNNING' if uw_final else '✗ NOT RUNNING'}")
if stdout6:
    print(f"  PID: {stdout6.strip().split()[0]}")
print(f"Trading Bot (FP-6.1): {'✓ RUNNING' if bot_final else '✗ NOT RUNNING'}")
if stdout7:
    print(f"  PID: {stdout7.strip()}")
print()

if uw_final and bot_final:
    print("[SUCCESS] All critical services are running!")
    print("  Dashboard should show:")
    print("    - FP-1.1 (UW Daemon): OK")
    print("    - FP-6.1 (Bot Running): OK")
    print("  Refresh the dashboard to see updated status")
elif uw_final:
    print("[PARTIAL SUCCESS] UW daemon running, but trading bot failed")
    print("  Trading bot may have startup errors")
    print("  Check: tail -50 /root/stock-bot/logs/run.jsonl")
elif bot_final:
    print("[PARTIAL SUCCESS] Trading bot running, but UW daemon failed")
    print("  UW daemon may have startup errors")
else:
    print("[FAILED] Services did not start")
    print("  Both services failed to start - check logs and dependencies")

c.close()
