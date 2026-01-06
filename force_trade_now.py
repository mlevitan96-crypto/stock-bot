#!/usr/bin/env python3
"""Force a trade to happen NOW - bypass all checks"""

import sys
sys.path.insert(0, '/root/stock-bot')

from main import run_once
import json
from pathlib import Path

print("FORCING TRADE EXECUTION NOW...")
print("=" * 80)

try:
    result = run_once()
    print("\n" + "=" * 80)
    print("RESULT:")
    print(json.dumps(result, indent=2))
    print("=" * 80)
    
    clusters = result.get("clusters", 0)
    orders = result.get("orders", 0)
    
    if clusters == 0:
        print("\n❌ NO CLUSTERS GENERATED")
        print("Checking why...")
        
        # Check cache
        cache_file = Path("data/uw_flow_cache.json")
        if cache_file.exists():
            cache = json.load(open(cache_file))
            syms = [k for k in cache.keys() if not k.startswith("_")]
            print(f"Cache has {len(syms)} symbols: {syms[:10]}")
        else:
            print("Cache file missing!")
            
    if orders == 0 and clusters > 0:
        print(f"\n❌ {clusters} CLUSTERS BUT 0 ORDERS")
        print("Clusters are being blocked by gates")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
