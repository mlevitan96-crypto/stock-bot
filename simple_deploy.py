#!/usr/bin/env python3
"""Simple deployment script - avoids Unicode issues"""
from droplet_client import DropletClient
import sys

print("Deploying hardened code to droplet...")
c = DropletClient()

# Step 1: Pull code
print("\n[1] Pulling latest code...")
result = c._execute_with_cd('cd /root/stock-bot && git pull origin main 2>&1', 30)
output = result[0] if result[0] else result[1]
# Filter out Unicode characters for display
clean_output = ''.join(c if ord(c) < 128 else '?' for c in output)
print(clean_output[:500])

# Step 2: Verify git status
print("\n[2] Verifying git status...")
result = c._execute_with_cd('cd /root/stock-bot && git rev-parse HEAD 2>&1', 30)
commit_hash = (result[0] if result[0] else result[1]).strip()[:8]
print(f"Current commit: {commit_hash}")

# Step 3: Restart service
print("\n[3] Restarting trading-bot service...")
result = c._execute('systemctl restart trading-bot.service 2>&1', 30)
print("Service restarted")

# Step 4: Wait and check status
print("\n[4] Waiting for service to start...")
import time
time.sleep(5)

# Step 5: Check bot status
print("\n[5] Checking bot status...")
result = c._execute_with_cd('cd /root/stock-bot && python3 check_current_status.py 2>&1', 60)
output = result[0] if result[0] else result[1]
clean_output = ''.join(c if ord(c) < 128 else '?' for c in output)
print(clean_output[:2000])

c.close()
print("\nDeployment complete!")
