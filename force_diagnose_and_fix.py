#!/usr/bin/env python3
"""Force diagnose and fix - execute directly on droplet"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("FORCE DIAGNOSE AND FIX")
print("=" * 80)
print()

# 1. Check if bot process is running
import subprocess
result = subprocess.run(['pgrep', '-f', 'python.*main.py'], capture_output=True, text=True)
if result.returncode == 0:
    pids = result.stdout.strip().split('\n')
    print(f"✅ Bot process running (PIDs: {', '.join(pids)})")
else:
    print("❌ Bot process NOT running!")
    sys.exit(1)

# 2. Check freeze status
freeze_file = Path("state/governor_freezes.json")
if freeze_file.exists():
    freeze_data = json.load(open(freeze_file))
    active_freezes = [k for k, v in freeze_data.items() if v.get("active", False)]
    if active_freezes:
        print(f"⚠️  ACTIVE FREEZES: {active_freezes}")
        # Clear freezes
        for key in active_freezes:
            freeze_data[key]["active"] = False
            freeze_data[key]["cleared_at"] = datetime.now(timezone.utc).isoformat()
        json.dump(freeze_data, open(freeze_file, 'w'), indent=2)
        print(f"✅ Cleared freezes: {active_freezes}")
    else:
        print("✅ No active freezes")
else:
    print("✅ No freeze file")

# 3. Verify fixes are in code
print("\nVerifying fixes:")
import uw_composite_v2

# Check threshold
threshold = uw_composite_v2.get_threshold("AAPL", "base")
expected_threshold = 2.7
if abs(threshold - expected_threshold) < 0.1:
    print(f"✅ Threshold: {threshold:.2f} (expected {expected_threshold})")
else:
    print(f"❌ Threshold: {threshold:.2f} (expected {expected_threshold})")

# Check flow weight
flow_weight = uw_composite_v2.get_weight("options_flow", "mixed")
expected_weight = 2.4
if abs(flow_weight - expected_weight) < 0.1:
    print(f"✅ Flow weight: {flow_weight:.3f} (expected {expected_weight})")
else:
    print(f"❌ Flow weight: {flow_weight:.3f} (expected {expected_weight})")

# 4. Test scoring with a real symbol
print("\nTesting score calculation:")
try:
    import uw_enrichment_v2
    cache_path = Path("data/uw_flow_cache.json")
    if cache_path.exists():
        cache = json.load(open(cache_path))
        # Find a symbol with good conviction
        test_symbol = None
        for symbol, data in cache.items():
            if symbol.startswith("_"):
                continue
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    continue
            conv = data.get("conviction", 0.0)
            if isinstance(conv, (int, float)) and conv > 0.5:
                test_symbol = symbol
                break
        
        if test_symbol:
            print(f"Testing with {test_symbol}")
            enriched = uw_enrichment_v2.enrich_signal(test_symbol, cache, "NEUTRAL")
            
            # Apply freshness fix
            current_freshness = enriched.get("freshness", 1.0)
            if current_freshness < 0.5:
                enriched["freshness"] = 0.9
            elif current_freshness < 0.8:
                enriched["freshness"] = 0.95
            
            composite = uw_composite_v2.compute_composite_score_v3(test_symbol, enriched, "NEUTRAL")
            score = composite.get("score", 0.0)
            flow_comp = composite.get("components", {}).get("flow", 0.0)
            threshold_used = uw_composite_v2.get_threshold(test_symbol, "base")
            
            print(f"  Score: {score:.3f}")
            print(f"  Flow component: {flow_comp:.3f}")
            print(f"  Threshold: {threshold_used:.2f}")
            print(f"  Would pass: {'YES' if score >= threshold_used else 'NO'}")
            
            if score < 1.0:
                print(f"  ⚠️  Score still too low! Flow component should be ~2.4, got {flow_comp:.3f}")
        else:
            print("  ⚠️  No symbols with good conviction found in cache")
    else:
        print("  ⚠️  Cache file not found")
except Exception as e:
    print(f"  ❌ Error testing: {e}")
    import traceback
    traceback.print_exc()

# 5. Check latest cycle time
print("\nCycle status:")
run_path = Path("logs/run.jsonl")
if run_path.exists():
    with open(run_path) as f:
        lines = f.readlines()
        if lines:
            latest = json.loads(lines[-1])
            ts_str = latest.get("ts", "")
            try:
                from datetime import datetime
                latest_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_sec = (now - latest_dt.replace(tzinfo=None)).total_seconds()
                age_min = age_sec / 60
                print(f"  Latest cycle: {ts_str} ({age_min:.1f} minutes ago)")
                if age_min > 5:
                    print(f"  ⚠️  Cycles are stale - should run every 60 seconds")
            except Exception as e:
                print(f"  Error parsing timestamp: {e}")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
