#!/usr/bin/env python3
"""Comprehensive diagnostic"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, '/root/stock-bot')

print("=" * 80)
print("COMPREHENSIVE DIAGNOSTIC")
print("=" * 80)

# 1. Process check
print("\n1. PROCESSES:")
result = subprocess.run(['pgrep', '-f', 'python.*main.py'], capture_output=True, text=True)
if result.returncode == 0:
    print(f"   Bot running: YES (PIDs: {result.stdout.strip()})")
else:
    print("   Bot running: NO")

# 2. Worker status
print("\n2. WORKER STATUS:")
hb_file = Path("state/bot_heartbeat.json")
if hb_file.exists():
    hb = json.load(open(hb_file))
    print(f"   Running: {hb.get('running', False)}")
    print(f"   Iter count: {hb.get('iter_count', 0)}")
    print(f"   Last heartbeat: {hb.get('last_heartbeat_dt', 'N/A')}")
else:
    print("   No heartbeat file")

# 3. Latest cycle
print("\n3. LATEST CYCLE:")
run_file = Path("logs/run.jsonl")
if run_file.exists():
    with open(run_file) as f:
        lines = f.readlines()
        if lines:
            latest = json.loads(lines[-1])
            ts_str = latest.get("ts", "")
            print(f"   Timestamp: {ts_str}")
            try:
                latest_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_sec = (now - latest_dt.replace(tzinfo=timezone.utc)).total_seconds()
                age_min = age_sec / 60
                print(f"   Age: {age_min:.1f} minutes")
            except:
                pass
            print(f"   Clusters: {latest.get('clusters', 0)}")
            print(f"   Orders: {latest.get('orders', 0)}")

# 4. Market check
print("\n4. MARKET STATUS:")
try:
    from main import is_market_open_now
    market_open = is_market_open_now()
    print(f"   Market open: {market_open}")
except Exception as e:
    print(f"   ERROR checking market: {e}")

# 5. Test run_once import
print("\n5. TESTING RUN_ONCE:")
try:
    from main import run_once
    print("   Import: SUCCESS")
except Exception as e:
    print(f"   Import: FAILED - {e}")

# 6. Recent errors
print("\n6. RECENT ERRORS:")
sys_file = Path("logs/system.jsonl")
if sys_file.exists():
    with open(sys_file) as f:
        lines = f.readlines()
        errors = []
        for line in lines[-200:]:
            try:
                event = json.loads(line)
                if 'error' in str(event).lower() or 'exception' in str(event).lower():
                    errors.append(event)
            except:
                pass
        if errors:
            print(f"   Found {len(errors)} recent error events:")
            for e in errors[-5:]:
                msg = e.get('msg', '') or e.get('event', '')
                error = e.get('error', '')
                print(f"     {e.get('ts', 'N/A')[:19]}: {msg} - {error[:100]}")
        else:
            print("   No errors found")

print("\n" + "=" * 80)
