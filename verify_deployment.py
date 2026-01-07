#!/usr/bin/env python3
"""Verify deployment - wait for new cycle and check gate events"""
from droplet_client import DropletClient
import time

print("="*80)
print("VERIFYING DEPLOYMENT - Waiting for new cycle")
print("="*80)

c = DropletClient()

# Get timestamp before waiting
print("\n[1] Checking current status...")
result = c._execute_with_cd('cd /root/stock-bot && tail -1 logs/run.jsonl 2>&1 | python3 -c "import sys, json; d=json.loads(sys.stdin.read()); print(d.get(\"ts\", \"?\")[:19])" 2>&1', 30)
last_cycle = ''.join(c if ord(c) < 128 else '?' for c in (result[0] if result[0] else result[1]))
print(f"Last cycle: {last_cycle.strip()}")

# Wait 30 seconds for new cycle
print("\n[2] Waiting 30 seconds for next cycle...")
time.sleep(30)

# Check new cycles
print("\n[3] Checking new cycles...")
result = c._execute_with_cd('cd /root/stock-bot && tail -3 logs/run.jsonl 2>&1 | python3 -c "import sys, json; [print(f\"{json.loads(l).get(\"ts\", \"?\")[:19]}: clusters={json.loads(l).get(\"clusters\", 0)}, orders={json.loads(l).get(\"orders\", 0)}\") for l in sys.stdin if l.strip()]" 2>&1', 30)
output = ''.join(c if ord(c) < 128 else '?' for c in (result[0] if result[0] else result[1]))
print(output)

# Check recent gate events - should NOT see portfolio_delta with 0 positions
print("\n[4] Checking recent gate events (last 10)...")
result = c._execute_with_cd('cd /root/stock-bot && tail -10 logs/gate.jsonl 2>&1 | python3 -c "import sys, json; events=[json.loads(l) for l in sys.stdin if l.strip()]; reasons=[e.get(\"reason\", \"?\") for e in events]; from collections import Counter; print(Counter(reasons))" 2>&1', 30)
output = ''.join(c if ord(c) < 128 else '?' for c in (result[0] if result[0] else result[1]))
print(output)

# Verify fix in code
print("\n[5] Verifying fix in code...")
result = c._execute_with_cd('cd /root/stock-bot && grep -n "len(open_positions) > 0 and net_delta_pct > 70.0" main.py 2>&1 | head -1', 30)
fix_line = ''.join(c if ord(c) < 128 else '?' for c in (result[0] if result[0] else result[1]))
print(f"Fix location: {fix_line.strip()}")

# Check positions
print("\n[6] Checking current positions...")
result = c._execute_with_cd('cd /root/stock-bot && python3 -c "import json; d=json.load(open(\"state/position_metadata.json\")); print(f\"Positions: {len(d)}\")" 2>&1', 30)
positions = ''.join(c if ord(c) < 128 else '?' for c in (result[0] if result[0] else result[1]))
print(positions.strip())

c.close()
print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
