#!/usr/bin/env python3
"""
Fix trading bot startup - investigate and start trading bot
"""

from droplet_client import DropletClient
import time

c = DropletClient()

print("=" * 80)
print("FIXING TRADING BOT STARTUP")
print("=" * 80)
print()

# Check current status
print("[1/5] Current status:")
stdout1, stderr1, code1 = c._execute('pgrep -f "python.*main.py"')
bot_running = bool(stdout1)
print(f"  Trading Bot: {'RUNNING' if bot_running else 'NOT RUNNING'}")
if stdout1:
    print(f"    PIDs: {stdout1.strip()}")
print()

# Check for multiple UW daemon instances (cleanup)
print("[2/5] Checking for duplicate UW daemon instances...")
stdout2, stderr2, code2 = c._execute('pgrep -f uw_flow_daemon')
if stdout2:
    pids = stdout2.strip().split('\n')
    if len(pids) > 1:
        print(f"  [WARNING] Found {len(pids)} UW daemon instances: {', '.join(pids)}")
        print("  Keeping first one, killing others...")
        for pid in pids[1:]:
            c._execute(f'kill {pid}')
        time.sleep(2)
        print("  [OK] Cleaned up duplicate instances")
    else:
        print(f"  [OK] Single UW daemon instance (PID: {pids[0]})")
else:
    print("  [WARNING] No UW daemon found")
print()

# Check supervisor status
print("[3/5] Checking supervisor...")
stdout3, stderr3, code3 = c._execute('pgrep -f deploy_supervisor')
if stdout3:
    print(f"  Supervisor running (PID: {stdout3.strip()})")
else:
    print("  [ERROR] Supervisor not running - this is critical!")
print()

# Try to start trading bot manually to see errors
print("[4/5] Testing trading bot startup (capturing first 20 lines of output)...")
# Use a simpler command that won't timeout
stdout4, stderr4, code4 = c._execute('cd /root/stock-bot && /root/stock-bot/venv/bin/python -c "import sys; sys.path.insert(0, \'.\'); import main; print(\'Import successful\')" 2>&1 | head -20')
if stdout4:
    print("  Import test output:")
    print(f"    {stdout4[:500]}")
else:
    print("  No output from import test")
print()

# Start trading bot
print("[5/5] Starting trading bot...")
if not bot_running:
    print("  Starting trading bot via supervisor restart trigger...")
    # Instead of starting manually, trigger supervisor to restart it
    # Check supervisor logs to see if it's trying to restart
    stdout5, stderr5, code5 = c._execute('cd /root/stock-bot && tail -100 logs/supervisor.jsonl | grep trading-bot | tail -5')
    if stdout5:
        print("  Recent trading-bot events in supervisor:")
        for line in stdout5.strip().split('\n')[:3]:
            print(f"    {line[:100]}")
    
    # Manually start the bot
    print("  Manually starting trading bot...")
    stdout6, stderr6, code6 = c._execute('cd /root/stock-bot && nohup /root/stock-bot/venv/bin/python main.py > logs/main_manual_start.log 2>&1 &')
    time.sleep(3)
    
    # Verify it started
    stdout7, stderr7, code7 = c._execute('pgrep -f "python.*main.py"')
    if stdout7:
        print(f"  [OK] Trading bot started (PID: {stdout7.strip()})")
    else:
        print("  [ERROR] Trading bot failed to start")
        print("  Check logs/main_manual_start.log for errors")
else:
    print("  Trading bot already running, no action needed")
print()

# Final verification
print("=" * 80)
print("FINAL VERIFICATION")
print("=" * 80)
print()

stdout8, stderr8, code8 = c._execute('pgrep -f uw_flow_daemon')
stdout9, stderr9, code9 = c._execute('pgrep -f "python.*main.py"')
stdout10, stderr10, code10 = c._execute('pgrep -f deploy_supervisor')

uw_final = bool(stdout8)
bot_final = bool(stdout9)
supervisor_final = bool(stdout10)

print(f"Supervisor: {'RUNNING' if supervisor_final else 'NOT RUNNING'}")
print(f"UW Daemon (FP-1.1): {'RUNNING' if uw_final else 'NOT RUNNING'}")
if stdout8:
    pids = stdout8.strip().split('\n')
    print(f"  PIDs: {', '.join(pids)}")
print(f"Trading Bot (FP-6.1): {'RUNNING' if bot_final else 'NOT RUNNING'}")
if stdout9:
    print(f"  PID: {stdout9.strip()}")
print()

if uw_final and bot_final:
    print("[SUCCESS] Both critical services are running!")
    print("  Dashboard should show FP-1.1 and FP-6.1 as OK")
elif uw_final:
    print("[PARTIAL] UW daemon running, but trading bot failed")
    print("  Check: tail -50 /root/stock-bot/logs/main_manual_start.log")
else:
    print("[FAILED] Services not running properly")
    print("  Check supervisor logs and service-specific logs")

c.close()
