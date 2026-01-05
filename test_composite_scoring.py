#!/usr/bin/env python3
"""Test composite scoring to see why scores are 0.0"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from signals import uw_composite_v2 as uw_v2
    from uw_enrichment_v2 import UWEnricher
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

cache_file = Path("data/uw_flow_cache.json")
if not cache_file.exists():
    print(f"ERROR: Cache file not found: {cache_file}")
    sys.exit(1)

with open(cache_file, 'r') as f:
    cache = json.load(f)

symbols = [k for k in cache.keys() if not k.startswith("_")][:10]

print("="*80)
print("COMPOSITE SCORING DIAGNOSTIC")
print("="*80)
print()

enricher = UWEnricher()
market_regime = "mixed"

for symbol in symbols:
    print(f"Testing {symbol}:")
    symbol_data = cache.get(symbol, {})
    
    if not symbol_data:
        print(f"  ERROR: No data for {symbol}")
        continue
    
    # Check basic fields
    sentiment = symbol_data.get("sentiment", "N/A")
    conviction = symbol_data.get("conviction", 0.0)
    print(f"  sentiment={sentiment}, conviction={conviction}")
    
    # Enrich
    enriched = enricher.enrich_signal(symbol, cache, market_regime)
    print(f"  enriched keys: {list(enriched.keys())[:10]}")
    
    # Compute composite score
    composite = uw_v2.compute_composite_score_v3(symbol, enriched, market_regime)
    
    if composite is None:
        print(f"  ERROR: compute_composite_score_v3 returned None")
        continue
    
    score = composite.get("score", 0.0)
    components = composite.get("components", {})
    
    print(f"  FINAL SCORE: {score:.2f}")
    print(f"  Components: {list(components.keys())[:5]}")
    
    # Show key component values
    if components:
        key_comps = ["options_flow", "dark_pool", "insider", "flow_conviction"]
        for comp in key_comps:
            if comp in components:
                print(f"    {comp}: {components[comp]}")
    
    print()
