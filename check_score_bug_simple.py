#!/usr/bin/env python3
"""Simple script to check score bug - no unicode"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

cache_path = Path("data/uw_flow_cache.json")
if cache_path.exists():
    cache = json.load(open(cache_path))
    symbols = [k for k in cache.keys() if not k.startswith("_")]
    print(f"Total symbols: {len(symbols)}")
    
    # Find best symbol
    best = None
    best_conv = 0
    for s in symbols[:50]:
        data = cache[s]
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                continue
        if not isinstance(data, dict):
            continue
        conv = data.get("conviction", 0.0)
        if isinstance(conv, (int, float)) and conv > best_conv:
            best_conv = conv
            best = s
    
    if best:
        print(f"Best symbol: {best} with conviction={best_conv}")
        data = cache[best]
        if isinstance(data, str):
            data = json.loads(data)
        
        print(f"Sentiment: {data.get('sentiment')}")
        print(f"Conviction: {data.get('conviction')}")
        
        # Test enrich_signal
        import uw_enrichment_v2
        enriched = uw_enrichment_v2.enrich_signal(best, cache, "NEUTRAL")
        print(f"\nAfter enrich_signal:")
        print(f"  conviction: {enriched.get('conviction')}")
        print(f"  sentiment: {enriched.get('sentiment')}")
        print(f"  freshness: {enriched.get('freshness')}")
        
        # Test scoring
        import uw_composite_v2
        result = uw_composite_v2.compute_composite_score_v3(best, enriched, "NEUTRAL")
        score = result.get('score', 0.0)
        components = result.get('components', {})
        flow_comp = components.get('flow', 0.0)
        
        print(f"\nComposite score result:")
        print(f"  Total score: {score}")
        print(f"  Flow component: {flow_comp}")
        print(f"  Freshness factor: {components.get('freshness_factor')}")
        
        # Check threshold
        thresholds = uw_composite_v2.ENTRY_THRESHOLDS
        print(f"\nThresholds: {thresholds}")
        print(f"Passes threshold: {score >= thresholds.get('base', 2.7)}")
    else:
        print("No good symbols found")
        # Show samples
        for s in symbols[:5]:
            data = cache[s]
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    continue
            print(f"{s}: conviction={data.get('conviction')}, sentiment={data.get('sentiment')}")
else:
    print("Cache file not found")
