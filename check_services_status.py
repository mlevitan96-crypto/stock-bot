#!/usr/bin/env python3
"""Check actual service status vs failure point detection"""

from droplet_client import DropletClient

c = DropletClient()

print("=" * 80)
print("SERVICE STATUS CHECK")
print("=" * 80)
print()

# Check FP-1.1: UW Daemon
print("[FP-1.1] UW Daemon Check:")
stdout, stderr, code = c._execute('pgrep -f uw_flow_daemon')
if stdout:
    print(f"  pgrep -f uw_flow_daemon: FOUND (PID: {stdout.strip()})")
else:
    print(f"  pgrep -f uw_flow_daemon: NOT FOUND")
print()

# Check FP-6.1: Bot Running
print("[FP-6.1] Bot Running Check:")
stdout2, stderr2, code2 = c._execute('pgrep -f "python.*main.py"')
if stdout2:
    print(f"  pgrep -f 'python.*main.py': FOUND (PID: {stdout2.strip()})")
else:
    print(f"  pgrep -f 'python.*main.py': NOT FOUND")
print()

# Check all Python processes
print("All Python Processes:")
stdout3, stderr3, code3 = c._execute('ps aux | grep python | grep -v grep')
if stdout3:
    lines = stdout3.strip().split('\n')
    for line in lines:
        print(f"  {line}")
else:
    print("  No Python processes found")
print()

# Check what deploy_supervisor is managing
print("Deploy Supervisor Status:")
stdout4, stderr4, code4 = c._execute('ps aux | grep deploy_supervisor | grep -v grep')
if stdout4:
    print(f"  Supervisor running: {stdout4.strip()[:150]}")
else:
    print("  Supervisor NOT running")
print()

# Check supervisor logs for service status
print("Recent Supervisor Logs (last 20 lines):")
stdout5, stderr5, code5 = c._execute('tail -20 /root/stock-bot/logs/supervisor.jsonl 2>/dev/null || echo "No supervisor logs"')
if stdout5:
    print(stdout5[:500])
else:
    print("  No supervisor logs found")
print()

# Check if services are actually running but with different names
print("Alternative Process Checks:")
stdout6, stderr6, code6 = c._execute('ps aux | grep -E "uw_flow|main.py" | grep -v grep')
if stdout6:
    print(f"  Found processes matching 'uw_flow' or 'main.py':")
    for line in stdout6.strip().split('\n'):
        print(f"    {line}")
else:
    print("  No processes found matching 'uw_flow' or 'main.py'")
print()

c.close()

print("=" * 80)
print("DIAGNOSIS")
print("=" * 80)
print()
print("If pgrep checks fail but supervisor is running:")
print("  - Services may have crashed and not restarted")
print("  - Services may be starting but failing immediately")
print("  - Process names may not match pgrep patterns")
print()
print("Check supervisor logs for service start/failure messages")
