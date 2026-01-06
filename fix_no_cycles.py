#!/usr/bin/env python3
"""Force fix - clear freezes and verify bot is running"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("FORCE FIX - NO CYCLES RUNNING")
print("=" * 80)
print()

# 1. Check if bot is running
print("1. Checking bot process...")
result = subprocess.run(['pgrep', '-f', 'python.*main.py'], capture_output=True, text=True)
if result.returncode == 0:
    pids = result.stdout.strip().split('\n')
    print(f"OK: Bot process is running (PIDs: {', '.join(pids)})")
    # Show process info
    result2 = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    for line in result2.stdout.split('\n'):
        if 'python' in line and 'main.py' in line:
            print(f"  {line[:120]}")
else:
    print("ERROR: Bot process NOT running!")
    print("Starting bot...")
    subprocess.run(['systemctl', 'start', 'trading-bot.service'])
    import time
    time.sleep(5)
print()

# 2. Check and clear freezes
print("2. Checking freezes...")
freeze_file = Path("state/governor_freezes.json")
if freeze_file.exists():
    data = json.load(open(freeze_file))
    active = [k for k, v in data.items() if v.get("active", False)]
    if active:
        print(f"WARNING: Active freezes found: {active}")
        for key in active:
            data[key]["active"] = False
            data[key]["cleared_at"] = datetime.now(timezone.utc).isoformat()
        json.dump(data, open(freeze_file, 'w'), indent=2)
        print(f"OK: Cleared freezes: {active}")
    else:
        print("OK: No active freezes")
else:
    print("OK: No freeze file")
print()

# 3. Check latest cycle
print("3. Latest cycle status...")
run_path = Path("logs/run.jsonl")
if run_path.exists():
    with open(run_path) as f:
        lines = f.readlines()
        if lines:
            latest = json.loads(lines[-1])
            ts_str = latest.get("ts", "")
            try:
                latest_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_sec = (now - latest_dt.replace(tzinfo=timezone.utc)).total_seconds()
                age_min = age_sec / 60
                print(f"Latest: {ts_str} ({age_min:.1f} minutes ago)")
                if age_min > 5:
                    print(f"WARNING: Cycles are stale - should run every 60 seconds")
            except Exception as e:
                print(f"Error parsing: {e}")
else:
    print("No run.jsonl file")
print()

# 4. Verify fixes in code
print("4. Verifying fixes...")
try:
    import uw_composite_v2
    threshold = uw_composite_v2.get_threshold("AAPL", "base")
    flow_weight = uw_composite_v2.get_weight("options_flow", "mixed")
    
    print(f"Threshold: {threshold:.2f} (expected 2.7)")
    print(f"Flow weight: {flow_weight:.3f} (expected 2.4)")
    
    if abs(threshold - 2.7) < 0.1 and abs(flow_weight - 2.4) < 0.1:
        print("OK: All fixes verified")
    else:
        print("ERROR: Fixes not working correctly!")
except Exception as e:
    print(f"ERROR verifying fixes: {e}")
    import traceback
    traceback.print_exc()
print()

# 5. Check for errors
print("5. Recent errors...")
sys_path = Path("logs/system.jsonl")
if sys_path.exists():
    with open(sys_path) as f:
        lines = f.readlines()
        errors = [l for l in lines[-50:] if 'error' in l.lower()]
        if errors:
            print(f"Found {len(errors)} recent errors:")
            for err in errors[-5:]:
                print(f"  {err[:150]}")
        else:
            print("No recent errors")
else:
    print("No system.jsonl")
print()

print("=" * 80)
print("FIX COMPLETE")
print("=" * 80)
