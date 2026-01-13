#!/usr/bin/env python3
"""Manually start services on droplet"""

from droplet_client import DropletClient
import time

c = DropletClient()

print("Starting services manually...")

# Pull latest code
print("Pulling latest code...")
c._execute('cd /root/stock-bot && git pull origin main')
time.sleep(2)

# Start UW daemon
print("Starting UW daemon...")
c._execute('cd /root/stock-bot && nohup /root/stock-bot/venv/bin/python uw_flow_daemon.py > logs/uw_daemon.log 2>&1 &')
time.sleep(3)

# Start trading bot
print("Starting trading bot...")
c._execute('cd /root/stock-bot && nohup /root/stock-bot/venv/bin/python main.py > logs/main.log 2>&1 &')
time.sleep(3)

# Verify
print("Verifying...")
stdout1, _, _ = c._execute('pgrep -f uw_flow_daemon')
stdout2, _, _ = c._execute('pgrep -f "python.*main.py"')

print(f"UW Daemon: {'RUNNING' if stdout1 else 'NOT RUNNING'}")
if stdout1:
    print(f"  PID: {stdout1.strip().split()[0]}")
print(f"Trading Bot: {'RUNNING' if stdout2 else 'NOT RUNNING'}")
if stdout2:
    print(f"  PID: {stdout2.strip().split()[0]}")

c.close()
