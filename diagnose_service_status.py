#!/usr/bin/env python3
"""Diagnose why services aren't detected"""

from droplet_client import DropletClient

c = DropletClient()

print("=" * 80)
print("SERVICE DIAGNOSIS")
print("=" * 80)
print()

# Check what pgrep actually finds
print("1. FP-1.1 Detection Pattern Check:")
stdout, stderr, code = c._execute('pgrep -f uw_flow_daemon')
print(f"   Command: pgrep -f uw_flow_daemon")
print(f"   Result: {'FOUND' if stdout else 'NOT FOUND'}")
if stdout:
    print(f"   PIDs: {stdout.strip()}")
print()

print("2. FP-6.1 Detection Pattern Check:")
stdout2, stderr2, code2 = c._execute('pgrep -f "python.*main.py"')
print(f"   Command: pgrep -f 'python.*main.py'")
print(f"   Result: {'FOUND' if stdout2 else 'NOT FOUND'}")
if stdout2:
    print(f"   PIDs: {stdout2.strip()}")
print()

# Check all processes that might be these services
print("3. All processes that might be UW daemon or bot:")
stdout3, stderr3, code3 = c._execute('ps aux | grep -E "uw_flow|main\.py" | grep -v grep')
if stdout3:
    for line in stdout3.strip().split('\n'):
        print(f"   {line}")
else:
    print("   None found")
print()

# Check supervisor process management
print("4. Supervisor process management:")
stdout4, stderr4, code4 = c._execute('ps aux | grep deploy_supervisor | grep -v grep')
if stdout4:
    print(f"   Supervisor running: YES")
    print(f"   {stdout4.strip()[:150]}")
else:
    print("   Supervisor running: NO")
print()

# Check if services crashed (look for recent exits in supervisor logs)
print("5. Recent service exit events:")
stdout5, stderr5, code5 = c._execute('cat /root/stock-bot/logs/supervisor.jsonl | grep -E "EXITED|CRASHED|FAILED" | tail -10')
if stdout5:
    print("   Recent exits/crashes:")
    for line in stdout5.strip().split('\n'):
        print(f"   {line}")
else:
    print("   No exit events found in recent logs")
print()

# Check if services are running but with different command patterns
print("6. Alternative process name checks:")
checks = [
    ('pgrep -f "uw_flow_daemon.py"', 'uw_flow_daemon.py'),
    ('pgrep -f "main.py"', 'main.py'),
    ('pgrep -f "venv.*uw_flow"', 'venv.*uw_flow'),
    ('pgrep -f "venv.*main"', 'venv.*main'),
]
for cmd, desc in checks:
    stdout, stderr, code = c._execute(cmd)
    result = 'FOUND' if stdout else 'NOT FOUND'
    print(f"   {desc}: {result}")
    if stdout:
        print(f"     PIDs: {stdout.strip()}")
print()

# Check supervisor's actual running processes
print("7. Supervisor child processes:")
stdout6, stderr6, code6 = c._execute('ps aux | grep -E "deploy_supervisor|dashboard|uw_flow|main\.py" | grep -v grep')
if stdout6:
    print("   Processes:")
    for line in stdout6.strip().split('\n'):
        print(f"   {line}")
else:
    print("   No related processes found")
print()

c.close()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("If pgrep patterns don't match but supervisor started services:")
print("  - Services may have crashed immediately after start")
print("  - Services may be running but command line doesn't match pattern")
print("  - Check service-specific log files for errors")
print("  - Check supervisor stdout/stderr for startup errors")
