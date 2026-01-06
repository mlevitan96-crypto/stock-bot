#!/usr/bin/env python3
"""Diagnose why clusters are 0"""

import json
import sys
from pathlib import Path

sys.path.insert(0, '/root/stock-bot')

print("=" * 80)
print("ZERO CLUSTERS DIAGNOSIS")
print("=" * 80)

# 1. Check cache
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache = json.load(open(cache_file))
    symbol_keys = [k for k in cache.keys() if not k.startswith("_")]
    print(f"\n1. CACHE STATUS:")
    print(f"   Total keys: {len(cache)}")
    print(f"   Symbol keys: {len(symbol_keys)}")
    print(f"   Sample symbols: {symbol_keys[:5]}")
    
    # Check if symbols have data
    if symbol_keys:
        sample = symbol_keys[0]
        sample_data = cache.get(sample, {})
        print(f"\n   Sample ({sample}) data:")
        print(f"   - sentiment: {sample_data.get('sentiment', 'N/A')}")
        print(f"   - conviction: {sample_data.get('conviction', 'N/A')}")
        print(f"   - has flow_trades: {bool(sample_data.get('flow_trades'))}")
        print(f"   - has dark_pool: {bool(sample_data.get('dark_pool'))}")
else:
    print("\n1. CACHE STATUS: MISSING!")

# 2. Check if composite scoring should run
print(f"\n2. COMPOSITE SCORING CHECK:")
try:
    cache = json.load(open(cache_file)) if cache_file.exists() else {}
    symbol_keys = [k for k in cache.keys() if not k.startswith("_")]
    use_composite = len(symbol_keys) > 0
    print(f"   use_composite should be: {use_composite}")
    print(f"   (based on {len(symbol_keys)} symbol keys in cache)")
except:
    print("   ERROR checking")

# 3. Test composite scoring
print(f"\n3. TEST COMPOSITE SCORING:")
try:
    import uw_enrichment_v2 as uw_enrich
    import uw_composite_v2 as uw_v2
    
    if symbol_keys:
        test_symbol = symbol_keys[0]
        print(f"   Testing {test_symbol}:")
        
        enriched = uw_enrich.enrich_signal(test_symbol, cache, "mixed")
        print(f"   - Enriched: sentiment={enriched.get('sentiment')}, conviction={enriched.get('conviction')}")
        
        composite = uw_v2.compute_composite_score_v3(test_symbol, enriched, "mixed")
        if composite:
            score = composite.get("score", 0.0)
            threshold = uw_v2.get_threshold(test_symbol, "base")
            passed = score >= threshold
            print(f"   - Score: {score:.2f}, Threshold: {threshold:.2f}, Passed: {passed}")
        else:
            print(f"   - Composite scoring returned None!")
    else:
        print("   - No symbols to test")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

# 4. Check recent run logs
print(f"\n4. RECENT RUN LOGS:")
run_file = Path("logs/run.jsonl")
if run_file.exists():
    with open(run_file) as f:
        lines = f.readlines()
        recent = []
        for l in lines[-10:]:
            if l.strip():
                try:
                    entry = json.loads(l)
                    if entry.get("clusters") is not None:
                        recent.append(entry)
                except:
                    pass
        
        if recent:
            last = recent[-1]
            print(f"   Last cycle: clusters={last.get('clusters', 'N/A')}, orders={last.get('orders', 'N/A')}")
            metrics = last.get('metrics', {})
            if 'composite_enabled' in metrics:
                print(f"   - composite_enabled: {metrics.get('composite_enabled')}")
else:
    print("   No run.jsonl found")

print("\n" + "=" * 80)
