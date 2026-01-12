#!/usr/bin/env python3
"""
Restart all services properly - comprehensive fix
"""

from droplet_client import DropletClient
import time

c = DropletClient()

print("=" * 80)
print("RESTARTING ALL SERVICES")
print("=" * 80)
print()

# Step 1: Kill all existing instances
print("[1/5] Cleaning up existing service instances...")
c._execute('pkill -f uw_flow_daemon')
c._execute('pkill -f "python.*main.py"')
time.sleep(2)
print("  [OK] Cleaned up existing instances")
print()

# Step 2: Restart supervisor
print("[2/5] Restarting supervisor...")
c._execute('pkill -f deploy_supervisor')
time.sleep(3)
print("  [OK] Supervisor stopped")
print("  Starting supervisor...")
# Start supervisor - it will start services
c._execute('cd /root/stock-bot && /root/stock-bot/venv/bin/python deploy_supervisor.py > /dev/null 2>&1 &')
time.sleep(5)
print("  [OK] Supervisor started")
print()

# Step 3: Wait for services to start
print("[3/5] Waiting for services to start (15 seconds)...")
time.sleep(15)
print("  [OK] Wait complete")
print()

# Step 4: Verify services
print("[4/5] Verifying services...")
stdout1, _, _ = c._execute('pgrep -f deploy_supervisor')
stdout2, _, _ = c._execute('pgrep -f uw_flow_daemon')
stdout3, _, _ = c._execute('pgrep -f "python.*main.py"')

supervisor_ok = bool(stdout1)
uw_ok = bool(stdout2)
bot_ok = bool(stdout3)

print(f"  Supervisor: {'[OK]' if supervisor_ok else '[ERROR]'}")
print(f"  UW Daemon: {'[OK]' if uw_ok else '[ERROR]'}")
if stdout2:
    print(f"    PID: {stdout2.strip().split()[0]}")
print(f"  Trading Bot: {'[OK]' if bot_ok else '[ERROR]'}")
if stdout3:
    print(f"    PID: {stdout3.strip().split()[0]}")
print()

# Step 5: If services didn't start, start them manually
if not uw_ok or not bot_ok:
    print("[5/5] Some services didn't start, starting manually...")
    if not uw_ok:
        print("  Starting UW daemon...")
        c._execute('cd /root/stock-bot && /root/stock-bot/venv/bin/python uw_flow_daemon.py > /dev/null 2>&1 &')
        time.sleep(3)
    if not bot_ok:
        print("  Starting trading bot...")
        c._execute('cd /root/stock-bot && /root/stock-bot/venv/bin/python main.py > /dev/null 2>&1 &')
        time.sleep(3)
    
    # Re-verify
    stdout4, _, _ = c._execute('pgrep -f uw_flow_daemon')
    stdout5, _, _ = c._execute('pgrep -f "python.*main.py"')
    uw_final = bool(stdout4)
    bot_final = bool(stdout5)
    
    print(f"  UW Daemon: {'[OK]' if uw_final else '[ERROR]'}")
    print(f"  Trading Bot: {'[OK]' if bot_final else '[ERROR]'}")
else:
    print("[5/5] All services started successfully, skipping manual start")
    uw_final = uw_ok
    bot_final = bot_ok

print()
print("=" * 80)
print("FINAL STATUS")
print("=" * 80)
print()
print(f"Supervisor: {'[OK] RUNNING' if supervisor_ok else '[ERROR] NOT RUNNING'}")
print(f"UW Daemon (FP-1.1): {'[OK] RUNNING' if uw_final else '[ERROR] NOT RUNNING'}")
print(f"Trading Bot (FP-6.1): {'[OK] RUNNING' if bot_final else '[ERROR] NOT RUNNING'}")
print()

if uw_final and bot_final:
    print("[SUCCESS] All critical services are running!")
    print()
    print("Dashboard should now show:")
    print("  - FP-1.1 (UW Daemon Running): OK")
    print("  - FP-6.1 (Bot Running): OK")
    print()
    print("Next steps:")
    print("  1. Refresh the dashboard to see updated status")
    print("  2. Services should remain running under supervisor management")
else:
    print("[WARNING] Some services failed to start")
    print("  Check logs for errors:")
    print("    - tail -50 /root/stock-bot/logs/supervisor.log")
    print("    - tail -50 /root/stock-bot/logs/run.jsonl")

c.close()
