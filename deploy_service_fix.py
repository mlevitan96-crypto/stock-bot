#!/usr/bin/env python3
"""
Deploy service fix to droplet and restart services
"""

from droplet_client import DropletClient
import time

c = DropletClient()

print("=" * 80)
print("DEPLOYING SERVICE FIX TO DROPLET")
print("=" * 80)
print()

# Step 1: Pull latest code
print("[1/4] Pulling latest code from GitHub...")
stdout1, stderr1, code1 = c._execute('cd /root/stock-bot && git pull')
if code1 == 0:
    print("  [OK] Code updated")
    if stdout1:
        print(f"    {stdout1[:200]}")
else:
    print(f"  [WARNING] Git pull had issues: {stderr1[:200]}")
print()

# Step 2: Clean up existing services
print("[2/4] Cleaning up existing service instances...")
c._execute('pkill -f uw_flow_daemon')
c._execute('pkill -f "python.*main.py"')
c._execute('pkill -f deploy_supervisor')
time.sleep(3)
print("  [OK] Services stopped")
print()

# Step 3: Restart supervisor
print("[3/4] Restarting supervisor...")
# Start supervisor in background - use a method that doesn't block
stdout2, stderr2, code2 = c._execute('cd /root/stock-bot && bash -c "nohup /root/stock-bot/venv/bin/python deploy_supervisor.py > logs/supervisor_restart.log 2>&1 &"')
time.sleep(5)
print("  [OK] Supervisor restart command sent")
print()

# Step 4: Verify services started
print("[4/4] Verifying services (waiting 15 seconds)...")
time.sleep(15)

stdout3, _, _ = c._execute('pgrep -f deploy_supervisor')
stdout4, _, _ = c._execute('pgrep -f uw_flow_daemon')
stdout5, _, _ = c._execute('pgrep -f "python.*main.py"')

supervisor_ok = bool(stdout3)
uw_ok = bool(stdout4)
bot_ok = bool(stdout5)

print()
print("=" * 80)
print("DEPLOYMENT COMPLETE - SERVICE STATUS")
print("=" * 80)
print()
print(f"Supervisor: {'[OK] RUNNING' if supervisor_ok else '[ERROR] NOT RUNNING'}")
if stdout3:
    print(f"  PID: {stdout3.strip().split()[0]}")
print()
print(f"UW Daemon (FP-1.1): {'[OK] RUNNING' if uw_ok else '[ERROR] NOT RUNNING'}")
if stdout4:
    print(f"  PID: {stdout4.strip().split()[0]}")
print()
print(f"Trading Bot (FP-6.1): {'[OK] RUNNING' if bot_ok else '[ERROR] NOT RUNNING'}")
if stdout5:
    print(f"  PID: {stdout5.strip().split()[0]}")
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
    print("[WARNING] Some services did not start automatically")
    print()
    print("Manual start commands (run on droplet):")
    print("  cd /root/stock-bot")
    if not uw_ok:
        print("  nohup /root/stock-bot/venv/bin/python uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &")
    if not bot_ok:
        print("  nohup /root/stock-bot/venv/bin/python main.py > logs/main.log 2>&1 &")

c.close()
