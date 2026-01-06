#!/usr/bin/env python3
"""Debug why scores are still so low"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Get a symbol with high conviction
cache_path = Path("data/uw_flow_cache.json")
cache = json.load(open(cache_path))

# Find symbol with highest conviction
best_conv = 0
best_symbol = None
for s, data in cache.items():
    if s.startswith("_"):
        continue
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            continue
    conv = data.get("conviction", 0.0)
    if isinstance(conv, (int, float)) and conv > best_conv:
        best_conv = conv
        best_symbol = s

print(f"Testing with {best_symbol} (conviction={best_conv})")

# Test enrichment
import uw_enrichment_v2
enriched = uw_enrichment_v2.enrich_signal(best_symbol, cache, "NEUTRAL")
print(f"\nAfter enrich_signal:")
print(f"  conviction: {enriched.get('conviction')}")
print(f"  sentiment: {enriched.get('sentiment')}")

# Test scoring
import uw_composite_v2
result = uw_composite_v2.compute_composite_score_v3(best_symbol, enriched, "NEUTRAL")

print(f"\nComposite score result:")
print(f"  Total score: {result.get('score')}")
print(f"  Components:")
comps = result.get('components', {})
print(f"    flow: {comps.get('flow')}")
print(f"    dark_pool: {comps.get('dark_pool')}")
print(f"    freshness_factor: {comps.get('freshness_factor')}")

# Calculate what flow should be
flow_conv = enriched.get('conviction', 0.0)
flow_weight = uw_composite_v2.WEIGHTS_V3.get('options_flow', 2.4)
expected_flow = flow_weight * flow_conv
actual_flow = comps.get('flow', 0.0)

print(f"\nFlow component analysis:")
print(f"  conviction from enriched: {flow_conv}")
print(f"  flow_weight: {flow_weight}")
print(f"  Expected flow_component: {expected_flow}")
print(f"  Actual flow_component: {actual_flow}")
print(f"  Match: {'YES' if abs(expected_flow - actual_flow) < 0.01 else 'NO'}")

# Check raw vs final score
raw_score = sum([
    comps.get('flow', 0),
    comps.get('dark_pool', 0),
    comps.get('insider', 0),
    comps.get('iv_skew', 0),
    comps.get('smile', 0),
])
freshness = comps.get('freshness_factor', 1.0)
final_score = result.get('score', 0.0)

print(f"\nScore calculation:")
print(f"  Raw components sum (first 5): {raw_score}")
print(f"  Freshness factor: {freshness}")
print(f"  Expected final (raw * freshness): {raw_score * freshness}")
print(f"  Actual final score: {final_score}")
