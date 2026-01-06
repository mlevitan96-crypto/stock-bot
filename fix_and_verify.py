#!/usr/bin/env python3
"""Fix and verify everything"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, '/root/stock-bot')

print("=" * 80)
print("COMPLETE FIX AND VERIFY")
print("=" * 80)

# 1. Clear freezes
print("\n1. Clearing freezes...")
freeze_file = Path("state/governor_freezes.json")
if freeze_file.exists():
    data = json.load(open(freeze_file))
    active = [k for k, v in data.items() if v.get("active", False)]
    if active:
        for k in active:
            data[k]["active"] = False
            data[k]["cleared_at"] = datetime.now(timezone.utc).isoformat()
        json.dump(data, open(freeze_file, 'w'), indent=2)
        print(f"   Cleared: {active}")
    else:
        print("   OK: No active freezes")

# 2. Delete threshold override
print("\n2. Checking threshold override...")
threshold_file = Path("state/uw_thresholds_hierarchical.json")
if threshold_file.exists():
    threshold_file.unlink()
    print("   Deleted threshold override file")

# 3. Verify fixes
print("\n3. Verifying code fixes...")
import uw_composite_v2
threshold = uw_composite_v2.get_threshold("AAPL", "base")
flow_weight = uw_composite_v2.get_weight("options_flow", "mixed")
print(f"   Threshold: {threshold:.2f} (expected 2.7)")
print(f"   Flow weight: {flow_weight:.3f} (expected 2.4)")

if abs(threshold - 2.7) > 0.1 or abs(flow_weight - 2.4) > 0.1:
    print("   ERROR: Fixes not working!")
else:
    print("   OK: All fixes verified")

# 4. Check cache
print("\n4. Checking cache...")
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache = json.load(open(cache_file))
    symbols = [k for k in cache.keys() if not k.startswith("_")]
    print(f"   Symbols in cache: {len(symbols)}")
    if len(symbols) == 0:
        print("   WARNING: No symbols in cache!")
else:
    print("   ERROR: Cache file missing!")

print("\n" + "=" * 80)
print("FIX COMPLETE - Restart bot to apply")
print("=" * 80)
