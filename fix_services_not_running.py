#!/usr/bin/env python3
"""
Fix services not running - restart UW daemon and trading bot
"""

from droplet_client import DropletClient
import time

c = DropletClient()

print("=" * 80)
print("FIXING SERVICES NOT RUNNING")
print("=" * 80)
print()

# The issue: Services are actually NOT running (not a mapping issue)
# Supervisor started them but they're not in process list
# This means they crashed or failed to start

print("Diagnosis: Services are ACTUALLY NOT RUNNING")
print("  - FP-1.1 (UW Daemon): NOT FOUND in process list")
print("  - FP-6.1 (Bot): NOT FOUND in process list")
print("  - Supervisor is running but services aren't")
print("  - This is NOT a mapping issue - services need to be restarted")
print()

# Option 1: Restart via supervisor (kill and let it restart)
print("[1/3] Restarting supervisor to trigger service restart...")
stdout, stderr, code = c._execute('pkill -f deploy_supervisor')
print("   Killed supervisor (systemd or manual restart will bring it back)")
time.sleep(3)
print()

# Option 2: Manually start services
print("[2/3] Manually starting UW daemon...")
stdout2, stderr2, code2 = c._execute('cd /root/stock-bot && nohup /root/stock-bot/venv/bin/python uw_flow_daemon.py > logs/uw_daemon_manual.log 2>&1 &')
time.sleep(2)
stdout3, stderr3, code3 = c._execute('pgrep -f uw_flow_daemon')
if stdout3:
    print(f"   [OK] UW daemon started (PID: {stdout3.strip()})")
else:
    print("   [WARNING] UW daemon may not have started - check logs")
print()

print("[3/3] Manually starting trading bot...")
stdout4, stderr4, code4 = c._execute('cd /root/stock-bot && nohup /root/stock-bot/venv/bin/python main.py > logs/main_manual.log 2>&1 &')
time.sleep(2)
stdout5, stderr5, code5 = c._execute('pgrep -f "python.*main.py"')
if stdout5:
    print(f"   [OK] Trading bot started (PID: {stdout5.strip()})")
else:
    print("   [WARNING] Trading bot may not have started - check logs")
print()

# Verify
print("Verifying services are now running...")
stdout6, stderr6, code6 = c._execute('pgrep -f uw_flow_daemon')
stdout7, stderr7, code7 = c._execute('pgrep -f "python.*main.py"')

uw_running = bool(stdout6)
bot_running = bool(stdout7)

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print()
print(f"UW Daemon (FP-1.1): {'RUNNING' if uw_running else 'NOT RUNNING'}")
if stdout6:
    print(f"  PID: {stdout6.strip()}")
print()
print(f"Trading Bot (FP-6.1): {'RUNNING' if bot_running else 'NOT RUNNING'}")
if stdout7:
    print(f"  PID: {stdout7.strip()}")
print()

if uw_running and bot_running:
    print("[OK] Both services are now running")
    print("     Dashboard should show them as OK after next refresh")
else:
    print("[WARNING] Some services still not running")
    print("     Check logs for errors:")
    print("     - tail -50 /root/stock-bot/logs/uw_daemon_manual.log")
    print("     - tail -50 /root/stock-bot/logs/main_manual.log")

c.close()
