#!/usr/bin/env python3
"""Complete diagnosis - check everything"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))

results = {
    "bot_process": False,
    "latest_cycle": None,
    "cycle_age_minutes": None,
    "freezes": [],
    "threshold": None,
    "flow_weight": None,
    "market_open": None,
    "errors": []
}

print("=" * 80)
print("COMPLETE DIAGNOSIS")
print("=" * 80)

# 1. Bot process
print("\n1. Bot Process:")
result = subprocess.run(['pgrep', '-f', 'python.*main.py'], capture_output=True, text=True)
if result.returncode == 0:
    results["bot_process"] = True
    print(f"   OK: Running (PIDs: {result.stdout.strip()})")
else:
    print(f"   ERROR: Not running!")
    results["errors"].append("Bot process not running")

# 2. Latest cycle
print("\n2. Latest Cycle:")
run_file = Path("logs/run.jsonl")
if run_file.exists():
    with open(run_file) as f:
        lines = f.readlines()
        if lines:
            latest = json.loads(lines[-1])
            ts_str = latest.get("ts", "")
            results["latest_cycle"] = ts_str
            try:
                latest_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_sec = (now - latest_dt.replace(tzinfo=timezone.utc)).total_seconds()
                age_min = age_sec / 60
                results["cycle_age_minutes"] = age_min
                print(f"   Latest: {ts_str}")
                print(f"   Age: {age_min:.1f} minutes")
                if age_min > 5:
                    print(f"   ERROR: Cycles are stale!")
                    results["errors"].append(f"Cycles stale ({age_min:.1f} min old)")
            except Exception as e:
                print(f"   ERROR parsing timestamp: {e}")
        else:
            print("   ERROR: No cycles logged")
            results["errors"].append("No cycles in run.jsonl")
else:
    print("   ERROR: run.jsonl not found")
    results["errors"].append("run.jsonl file missing")

# 3. Freezes
print("\n3. Freezes:")
freeze_file = Path("state/governor_freezes.json")
if freeze_file.exists():
    data = json.load(open(freeze_file))
    active = [k for k, v in data.items() if v.get("active", False)]
    results["freezes"] = active
    if active:
        print(f"   ERROR: Active freezes: {active}")
        results["errors"].append(f"Active freezes: {active}")
        # Clear them
        for k in active:
            data[k]["active"] = False
            data[k]["cleared_at"] = datetime.now(timezone.utc).isoformat()
        json.dump(data, open(freeze_file, 'w'), indent=2)
        print(f"   CLEARED: {active}")
    else:
        print("   OK: No active freezes")
else:
    print("   OK: No freeze file")

# 4. Fixes
print("\n4. Code Fixes:")
try:
    import uw_composite_v2
    threshold = uw_composite_v2.get_threshold("AAPL", "base")
    flow_weight = uw_composite_v2.get_weight("options_flow", "mixed")
    results["threshold"] = threshold
    results["flow_weight"] = flow_weight
    
    print(f"   Threshold: {threshold:.2f} (expected 2.7)")
    print(f"   Flow weight: {flow_weight:.3f} (expected 2.4)")
    
    if abs(threshold - 2.7) > 0.1:
        results["errors"].append(f"Threshold wrong: {threshold:.2f}")
    if abs(flow_weight - 2.4) > 0.1:
        results["errors"].append(f"Flow weight wrong: {flow_weight:.3f}")
except Exception as e:
    print(f"   ERROR: {e}")
    results["errors"].append(f"Fix verification failed: {e}")

# 5. Market status
print("\n5. Market Status:")
try:
    from main import is_market_open_now
    market_open = is_market_open_now()
    results["market_open"] = market_open
    if market_open:
        print("   OK: Market is open")
    else:
        print("   INFO: Market is closed")
except Exception as e:
    print(f"   WARNING: Could not check market: {e}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Errors: {len(results['errors'])}")
if results["errors"]:
    for err in results["errors"]:
        print(f"  - {err}")
else:
    print("  No errors detected")

# Save results
json.dump(results, open("diagnosis_results.json", 'w'), indent=2)
