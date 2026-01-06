#!/usr/bin/env python3
"""Verify fixes are deployed and check cache data"""

import json
from pathlib import Path

# Check threshold
try:
    import uw_composite_v2
    thresholds = uw_composite_v2.ENTRY_THRESHOLDS
    print(f"ENTRY_THRESHOLDS: {thresholds}")
    if thresholds.get("base") == 2.7:
        print("✅ Threshold fix deployed (base=2.7)")
    else:
        print(f"❌ Threshold NOT fixed (base={thresholds.get('base')})")
except Exception as e:
    print(f"Error checking thresholds: {e}")

# Check enrich_signal fix
try:
    import uw_enrichment_v2
    import inspect
    source = inspect.getsource(uw_enrichment_v2.enrich_signal)
    if 'enriched_symbol["sentiment"]' in source and 'enriched_symbol["conviction"]' in source:
        print("✅ enrich_signal fix deployed (sentiment & conviction included)")
    else:
        print("❌ enrich_signal fix NOT deployed")
except Exception as e:
    print(f"Error checking enrich_signal: {e}")

# Check cache data
cache_path = Path("data/uw_flow_cache.json")
if cache_path.exists():
    cache = json.load(open(cache_path))
    symbols = [k for k in cache.keys() if not k.startswith("_")]
    print(f"\nCache has {len(symbols)} symbols")
    
    # Check sample symbols for sentiment/conviction
    sample_count = min(10, len(symbols))
    samples = symbols[:sample_count]
    
    print(f"\nSample cache data (first {sample_count} symbols):")
    for s in samples:
        data = cache[s]
        sentiment = data.get("sentiment", "MISSING")
        conviction = data.get("conviction", "MISSING")
        has_dp = bool(data.get("dark_pool"))
        has_insider = bool(data.get("insider"))
        print(f"  {s}: sentiment={sentiment}, conviction={conviction}, has_dp={has_dp}, has_insider={has_insider}")
else:
    print("❌ Cache file not found")
