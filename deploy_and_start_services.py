#!/usr/bin/env python3
"""
Deploy to droplet and start all services
"""

from droplet_client import DropletClient
import time

c = DropletClient()

print("=" * 80)
print("DEPLOYING AND STARTING SERVICES")
print("=" * 80)
print()

# Step 1: Pull latest code
print("[1/5] Pulling latest code from GitHub...")
stdout1, stderr1, code1 = c._execute('cd /root/stock-bot && git pull origin main')
if code1 == 0:
    print("  [OK] Code updated")
    if stdout1:
        print(f"    {stdout1[:200]}")
else:
    print(f"  [WARNING] Git pull had issues: {stderr1[:200]}")
print()

# Step 2: Clean up existing services
print("[2/5] Cleaning up existing service instances...")
c._execute('pkill -f uw_flow_daemon')
c._execute('pkill -f "python.*main.py"')
c._execute('pkill -f deploy_supervisor')
time.sleep(3)
print("  [OK] Services stopped")
print()

# Step 3: Restart supervisor
print("[3/5] Restarting supervisor...")
c._execute('cd /root/stock-bot && bash -c "nohup /root/stock-bot/venv/bin/python deploy_supervisor.py > logs/supervisor_restart.log 2>&1 &"')
time.sleep(5)
print("  [OK] Supervisor restart command sent")
print()

# Step 4: Wait and check if services started
print("[4/5] Waiting for services to start (10 seconds)...")
time.sleep(10)

stdout2, _, _ = c._execute('pgrep -f uw_flow_daemon')
stdout3, _, _ = c._execute('pgrep -f "python.*main.py"')

uw_started = bool(stdout2)
bot_started = bool(stdout3)

# Step 5: Manually start services if supervisor didn't start them
print("[5/5] Starting services manually if needed...")
if not uw_started:
    print("  Starting UW daemon...")
    c._execute('cd /root/stock-bot && bash -c "nohup /root/stock-bot/venv/bin/python uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &"')
    time.sleep(3)
    
if not bot_started:
    print("  Starting trading bot...")
    c._execute('cd /root/stock-bot && bash -c "nohup /root/stock-bot/venv/bin/python main.py > logs/main.log 2>&1 &"')
    time.sleep(3)

print()

# Final verification
print("=" * 80)
print("FINAL STATUS")
print("=" * 80)
print()

time.sleep(2)  # Give services time to fully start

stdout4, _, _ = c._execute('pgrep -f deploy_supervisor')
stdout5, _, _ = c._execute('pgrep -f uw_flow_daemon')
stdout6, _, _ = c._execute('pgrep -f "python.*main.py"')

supervisor_ok = bool(stdout4)
uw_ok = bool(stdout5)
bot_ok = bool(stdout6)

print(f"Supervisor: {'[OK] RUNNING' if supervisor_ok else '[ERROR] NOT RUNNING'}")
if stdout4:
    print(f"  PID: {stdout4.strip().split()[0]}")
print()
print(f"UW Daemon (FP-1.1): {'[OK] RUNNING' if uw_ok else '[ERROR] NOT RUNNING'}")
if stdout5:
    print(f"  PID: {stdout5.strip().split()[0]}")
print()
print(f"Trading Bot (FP-6.1): {'[OK] RUNNING' if bot_ok else '[ERROR] NOT RUNNING'}")
if stdout6:
    print(f"  PID: {stdout6.strip().split()[0]}")
print()

if uw_ok and bot_ok:
    print("[SUCCESS] All services are running!")
    print()
    print("Dashboard should now show:")
    print("  - FP-1.1 (UW Daemon Running): OK")
    print("  - FP-6.1 (Bot Running): OK")
    print()
    print("Next steps:")
    print("  1. Refresh the dashboard to verify status")
    print("  2. Monitor services for stability")
else:
    print("[WARNING] Some services failed to start")
    if not uw_ok:
        print("  - UW daemon failed - check logs/uw_daemon.log")
    if not bot_ok:
        print("  - Trading bot failed - check logs/main.log")

c.close()
