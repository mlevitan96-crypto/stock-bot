#!/usr/bin/env python3
"""Force deployment - reset hard to origin/main"""
from droplet_client import DropletClient
import time

print("="*80)
print("FORCE DEPLOYMENT TO DROPLET")
print("="*80)

c = DropletClient()

# Step 1: Hard reset to latest
print("\n[1] Resetting to latest code from origin/main...")
result = c._execute_with_cd('cd /root/stock-bot && git fetch origin && git reset --hard origin/main 2>&1', 60)
output = ''.join(c if ord(c) < 128 else '?' for c in (result[0] if result[0] else result[1]))
print(output[:800])

# Step 2: Verify latest commit
print("\n[2] Verifying latest commit...")
result = c._execute_with_cd('cd /root/stock-bot && git log --oneline -1 2>&1', 30)
commit = ''.join(c if ord(c) < 128 else '?' for c in (result[0] if result[0] else result[1]))
print(f"Latest commit: {commit.strip()}")

# Step 3: Verify fix is present
print("\n[3] Verifying portfolio delta gate fix...")
result = c._execute_with_cd('cd /root/stock-bot && grep -c "len(open_positions) > 0 and net_delta_pct > 70.0" main.py 2>&1', 30)
fix_found = (result[0] if result[0] else result[1]).strip()
print(f"Fix found: {fix_found} times")

# Step 4: Restart service
print("\n[4] Restarting trading-bot service...")
c._execute('systemctl restart trading-bot.service 2>&1', 30)
print("Service restarted")

# Step 5: Wait and check status
print("\n[5] Waiting 5 seconds for service to start...")
time.sleep(5)

# Step 6: Check status
print("\n[6] Checking bot status...")
result = c._execute_with_cd('cd /root/stock-bot && python3 check_current_status.py 2>&1', 60)
output = ''.join(c if ord(c) < 128 else '?' for c in (result[0] if result[0] else result[1]))
print(output[:2500])

c.close()
print("\n" + "="*80)
print("DEPLOYMENT COMPLETE")
print("="*80)
