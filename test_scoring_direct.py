#!/usr/bin/env python3
import json
import sys
sys.path.insert(0, '/root/stock-bot')

print("TESTING COMPOSITE SCORING DIRECTLY")
print("=" * 80)

# Load cache
cache_file = "/root/stock-bot/data/uw_flow_cache.json"
try:
    cache = json.load(open(cache_file))
    syms = [k for k in cache.keys() if not k.startswith("_")]
    print(f"Cache has {len(syms)} symbols")
    
    if not syms:
        print("ERROR: No symbols in cache!")
        sys.exit(1)
    
    # Test first symbol
    symbol = syms[0]
    print(f"\nTesting symbol: {symbol}")
    
    data = cache[symbol]
    print(f"Data keys: {list(data.keys())[:10]}")
    print(f"Sentiment: {data.get('sentiment')}")
    print(f"Conviction: {data.get('conviction')}")
    
    # Test enrichment
    import uw_enrichment_v2 as uw_enrich
    enriched = uw_enrich.enrich_signal(symbol, cache, "mixed")
    print(f"\nEnriched keys: {list(enriched.keys())[:10]}")
    print(f"Enriched sentiment: {enriched.get('sentiment')}")
    print(f"Enriched conviction: {enriched.get('conviction')}")
    print(f"Enriched freshness: {enriched.get('freshness')}")
    
    # Test scoring
    import uw_composite_v2 as uw_v2
    composite = uw_v2.compute_composite_score_v3(symbol, enriched, "mixed")
    
    if composite:
        score = composite.get("score", 0.0)
        threshold = uw_v2.get_threshold(symbol, "base")
        print(f"\nSCORE: {score:.2f}")
        print(f"THRESHOLD: {threshold:.2f}")
        print(f"WOULD PASS: {score >= threshold}")
        
        components = composite.get("components", {})
        print(f"\nComponents:")
        print(f"  flow_component: {components.get('flow_component', 0):.2f}")
        print(f"  dp_component: {components.get('dp_component', 0):.2f}")
        print(f"  insider_component: {components.get('insider_component', 0):.2f}")
    else:
        print("ERROR: Composite scoring returned None!")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
