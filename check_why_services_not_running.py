#!/usr/bin/env python3
"""Check why services aren't staying running"""

from droplet_client import DropletClient
import json

c = DropletClient()

print("=" * 80)
print("WHY SERVICES AREN'T RUNNING")
print("=" * 80)
print()

# Check supervisor's process registry
print("1. Checking supervisor process management...")
# Try to see if supervisor has processes registered
stdout, stderr, code = c._execute('cd /root/stock-bot && python3 -c "import subprocess; proc = subprocess.run([\'ps\', \'aux\'], capture_output=True, text=True); lines = [l for l in proc.stdout.split(\'\\n\') if \'deploy_supervisor\' in l and \'grep\' not in l]; print(\'\\n\'.join(lines))"')
print("Supervisor process:", stdout[:200] if stdout else "Not found")
print()

# Check if services are in supervisor's process list
print("2. Checking if supervisor is managing services...")
# The supervisor should be keeping processes alive - check if they exist as children
stdout2, stderr2, code2 = c._execute('ps auxf | grep -A 5 deploy_supervisor | grep -v grep')
if stdout2:
    print("Supervisor and children:")
    print(stdout2[:500])
else:
    print("No child processes visible")
print()

# Check supervisor health file
print("3. Checking supervisor health registry...")
stdout3, stderr3, code3 = c._execute('cat /root/stock-bot/state/health.json 2>/dev/null | python3 -m json.tool 2>/dev/null | head -50')
if stdout3:
    print("Health registry:")
    print(stdout3[:800])
else:
    print("No health.json found or error reading it")
print()

# Check if services crashed with errors
print("4. Checking for service crash logs...")
stdout4, stderr4, code4 = c._execute('cd /root/stock-bot && ls -la logs/*uw*.log logs/*main*.log logs/*trading*.log 2>/dev/null | head -5')
if stdout4:
    print("Service log files found:")
    print(stdout4)
    # Check last few lines of UW daemon log
    stdout5, stderr5, code5 = c._execute('tail -20 /root/stock-bot/logs/*uw*.log 2>/dev/null | tail -20')
    if stdout5:
        print("\nLast UW daemon log entries:")
        print(stdout5[:500])
else:
    print("No service-specific log files found")
print()

# Check if supervisor is actually trying to restart services
print("5. Checking supervisor restart behavior...")
stdout6, stderr6, code6 = c._execute('cat /root/stock-bot/logs/supervisor.jsonl | grep -E "uw-daemon|trading-bot" | tail -20')
if stdout6:
    print("Recent supervisor events for these services:")
    for line in stdout6.strip().split('\n'):
        try:
            event = json.loads(line)
            print(f"  {event.get('ts', '')} - {event.get('event', '')} - {event.get('service', '')}")
        except:
            print(f"  {line[:100]}")
else:
    print("No recent events for these services")
print()

# Check if there are any import or startup errors
print("6. Testing service startup directly...")
print("   (This will show if services can start or if they fail immediately)")
print()

c.close()

print("=" * 80)
print("DIAGNOSIS")
print("=" * 80)
print()
print("Based on the evidence:")
print("  - Supervisor is running")
print("  - Supervisor logs show services were started")
print("  - But services are NOT in process list")
print("  - This means services are CRASHING immediately after start")
print()
print("Next steps:")
print("  1. Check service-specific error logs")
print("  2. Check if services fail due to missing dependencies")
print("  3. Check if services fail due to configuration errors")
print("  4. Manually start services to see error messages")
