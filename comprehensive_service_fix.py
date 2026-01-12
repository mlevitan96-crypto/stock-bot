#!/usr/bin/env python3
"""
Comprehensive service fix - investigate and fix all service issues
"""

from droplet_client import DropletClient
import time
import json

c = DropletClient()

print("=" * 80)
print("COMPREHENSIVE SERVICE FIX")
print("=" * 80)
print()

# Step 1: Check current status
print("[1/7] Checking current service status...")
stdout1, stderr1, code1 = c._execute('pgrep -f uw_flow_daemon')
stdout2, stderr2, code2 = c._execute('pgrep -f "python.*main.py"')
stdout3, stderr3, code3 = c._execute('pgrep -f deploy_supervisor')

uw_running = bool(stdout1)
bot_running = bool(stdout2)
supervisor_running = bool(stdout3)

print(f"  Supervisor: {'RUNNING' if supervisor_running else 'NOT RUNNING'}")
if stdout3:
    print(f"    PID: {stdout3.strip()}")
print(f"  UW Daemon: {'RUNNING' if uw_running else 'NOT RUNNING'}")
if stdout1:
    print(f"    PID: {stdout1.strip()}")
print(f"  Trading Bot: {'RUNNING' if bot_running else 'NOT RUNNING'}")
if stdout2:
    print(f"    PID: {stdout2.strip()}")
print()

# Step 2: Check supervisor logs for recent failures
print("[2/7] Checking supervisor logs for recent failures...")
stdout4, stderr4, code4 = c._execute('cd /root/stock-bot && tail -200 logs/supervisor.jsonl | tail -30')
if stdout4:
    lines = stdout4.strip().split('\n')
    recent_events = []
    for line in lines:
        if line.strip():
            try:
                event = json.loads(line)
                if 'uw-daemon' in str(event) or 'trading-bot' in str(event):
                    recent_events.append(event)
            except:
                pass
    
    if recent_events:
        print("  Recent service events:")
        for event in recent_events[-5:]:
            print(f"    {event.get('ts', '')} - {event.get('event', '')} - {event.get('service', '')}")
    else:
        print("  No recent service events found")
else:
    print("  No supervisor logs found")
print()

# Step 3: Check if services are crashing immediately
print("[3/7] Testing service startup...")
# Check UW daemon startup
stdout5, stderr5, code5 = c._execute('cd /root/stock-bot && timeout 3 /root/stock-bot/venv/bin/python uw_flow_daemon.py 2>&1 | head -10')
if stdout5:
    print("  UW daemon startup test:")
    print(f"    {stdout5[:300]}")
else:
    print("  UW daemon: No immediate errors (may be starting)")
print()

# Step 4: Check supervisor process registry
print("[4/7] Checking supervisor process management...")
# The supervisor should have processes in its registry
# Check if supervisor is actually monitoring services
stdout6, stderr6, code6 = c._execute('ps auxf | grep -A 10 deploy_supervisor | grep -v grep | head -15')
if stdout6:
    print("  Supervisor process tree:")
    print(f"    {stdout6[:400]}")
else:
    print("  Could not get process tree")
print()

# Step 5: Check for systemd service
print("[5/7] Checking systemd service status...")
stdout7, stderr7, code7 = c._execute('systemctl status trading-bot.service 2>&1 | head -10')
if stdout7:
    if 'could not be found' in stdout7 or 'Unit trading-bot.service could not be found' in stdout7:
        print("  Systemd service NOT found (using manual supervisor)")
    else:
        print(f"  Systemd service status:")
        print(f"    {stdout7[:400]}")
else:
    print("  Could not check systemd status")
print()

# Step 6: Fix - Restart supervisor properly
print("[6/7] Restarting supervisor to fix services...")
if supervisor_running:
    print("  Stopping existing supervisor...")
    c._execute('pkill -f deploy_supervisor')
    time.sleep(3)
    
    # Check if it stopped
    stdout8, stderr8, code8 = c._execute('pgrep -f deploy_supervisor')
    if stdout8:
        print("  [WARNING] Supervisor still running, force killing...")
        c._execute('pkill -9 -f deploy_supervisor')
        time.sleep(2)
else:
    print("  Supervisor not running, will start fresh")

# Start supervisor
print("  Starting supervisor...")
stdout9, stderr9, code9 = c._execute('cd /root/stock-bot && nohup /root/stock-bot/venv/bin/python deploy_supervisor.py > logs/supervisor_restart.log 2>&1 &')
time.sleep(5)

# Verify supervisor started
stdout10, stderr10, code10 = c._execute('pgrep -f deploy_supervisor')
if stdout10:
    print(f"  [OK] Supervisor started (PID: {stdout10.strip()})")
else:
    print("  [ERROR] Supervisor failed to start - check logs/supervisor_restart.log")
print()

# Step 7: Wait and verify services
print("[7/7] Waiting for services to start and verifying...")
time.sleep(10)  # Give services time to start

stdout11, stderr11, code11 = c._execute('pgrep -f uw_flow_daemon')
stdout12, stderr12, code12 = c._execute('pgrep -f "python.*main.py"')

uw_now = bool(stdout11)
bot_now = bool(stdout12)

print()
print("=" * 80)
print("FINAL STATUS")
print("=" * 80)
print()
print(f"UW Daemon (FP-1.1): {'RUNNING' if uw_now else 'NOT RUNNING'}")
if stdout11:
    print(f"  PID: {stdout11.strip()}")
print()
print(f"Trading Bot (FP-6.1): {'RUNNING' if bot_now else 'NOT RUNNING'}")
if stdout12:
    print(f"  PID: {stdout12.strip()}")
print()

if uw_now and bot_now:
    print("[SUCCESS] Both services are now running!")
    print("  Dashboard should show them as OK after next refresh")
elif uw_now or bot_now:
    print("[PARTIAL] Some services started, but not all")
    if not uw_now:
        print("  UW daemon failed to start - check logs")
    if not bot_now:
        print("  Trading bot failed to start - check logs")
else:
    print("[FAILED] Services did not start")
    print("  Check logs:")
    print("    - tail -50 /root/stock-bot/logs/supervisor_restart.log")
    print("    - tail -50 /root/stock-bot/logs/supervisor.jsonl")
    print()
    print("  Possible causes:")
    print("    - Missing dependencies")
    print("    - Configuration errors")
    print("    - Credential issues")
    print("    - Import errors")

c.close()
