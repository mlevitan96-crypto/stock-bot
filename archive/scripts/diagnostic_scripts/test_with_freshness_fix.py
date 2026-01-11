#!/usr/bin/env python3
"""Test scoring WITH freshness adjustment (simulating main.py)"""

import json
import sys
from pathlib import Path
sys.path.insert(0, '/root/stock-bot')

print("TESTING WITH FRESHNESS ADJUSTMENT")
print("=" * 80)

# Load cache
cache = json.load(open("data/uw_flow_cache.json"))
syms = [k for k in cache.keys() if not k.startswith("_")][:5]

print(f"Testing {len(syms)} symbols\n")

import uw_enrichment_v2 as uw_enrich
import uw_composite_v2 as uw_v2

for symbol in syms:
    # Simulate main.py's enrichment + freshness adjustment
    enriched = uw_enrich.enrich_signal(symbol, cache, "mixed")
    
    # Apply freshness adjustment (like main.py does)
    current_freshness = enriched.get("freshness", 1.0)
    if current_freshness < 0.5:
        enriched["freshness"] = 0.9
    elif current_freshness < 0.8:
        enriched["freshness"] = 0.95
    
    # Score
    composite = uw_v2.compute_composite_score_v3(symbol, enriched, "mixed")
    if not composite:
        continue
        
    score = composite.get("score", 0.0)
    threshold = uw_v2.get_threshold(symbol, "base")
    comps = composite.get("components", {})
    gate_result = uw_v2.should_enter_v2(composite, symbol, "base")
    
    print(f"{symbol}:")
    print(f"  Score: {score:.2f} | Threshold: {threshold:.2f} | Gate: {gate_result}")
    print(f"  Flow: {comps.get('flow', 0):.2f} | DP: {comps.get('dark_pool', 0):.2f} | Freshness: {enriched.get('freshness', 1.0):.2f}")
    print()
