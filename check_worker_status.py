#!/usr/bin/env python3
"""Check worker thread status"""

import json
from pathlib import Path
import sys
sys.path.insert(0, '/root/stock-bot')

print("Checking worker status...")

# Check for worker started event
log_file = Path("logs/system.jsonl")
if log_file.exists():
    with open(log_file) as f:
        lines = f.readlines()
        worker_events = [json.loads(l) for l in lines[-1000:] if 'worker' in l.lower() or 'started' in l.lower()]
        if worker_events:
            print(f"Found {len(worker_events)} worker-related events")
            for e in worker_events[-5:]:
                msg = e.get('msg', '') or e.get('event', '')
                print(f"  {e.get('ts', 'N/A')[:19]}: {msg}")
        else:
            print("No worker events found")

# Check heartbeat file
heartbeat_file = Path("state/bot_heartbeat.json")
if heartbeat_file.exists():
    hb = json.load(open(heartbeat_file))
    print(f"\nHeartbeat file:")
    print(f"  Last heartbeat: {hb.get('last_heartbeat_dt', 'N/A')}")
    print(f"  Iter count: {hb.get('iter_count', 0)}")
    print(f"  Running: {hb.get('running', False)}")
else:
    print("\nNo heartbeat file - worker not running?")

# Check fail counter
fail_file = Path("state/fail_counter.json")
if fail_file.exists():
    fc = json.load(open(fail_file))
    fail_count = fc.get('fail_count', 0)
    print(f"\nFail counter: {fail_count}")
    if fail_count >= 5:
        print("WARNING: High fail count - may have triggered freeze")
