#!/usr/bin/env python3
"""Debug flow component calculation"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Get TSLA data
cache_path = Path("data/uw_flow_cache.json")
cache = json.load(open(cache_path))

symbol = "TSLA"
data = cache[symbol]
if isinstance(data, str):
    data = json.loads(data)

print(f"Raw cache data for {symbol}:")
print(f"  conviction: {data.get('conviction')}")
print(f"  sentiment: {data.get('sentiment')}")

# Enrich
import uw_enrichment_v2
enriched = uw_enrichment_v2.enrich_signal(symbol, cache, "NEUTRAL")

print(f"\nAfter enrich_signal:")
print(f"  conviction: {enriched.get('conviction')}")
print(f"  sentiment: {enriched.get('sentiment')}")

# Check what compute_composite_score_v3 sees
import uw_composite_v2

# Manually check what it gets
flow_conv = enriched.get("conviction", 0.0)
flow_sent = enriched.get("sentiment", "NEUTRAL")

print(f"\nIn compute_composite_score_v3:")
print(f"  enriched_data.get('conviction'): {flow_conv}")
print(f"  enriched_data.get('sentiment'): {flow_sent}")

# Check weights
flow_weight = uw_composite_v2.WEIGHTS_V3.get("options_flow", 2.4)
print(f"  flow_weight: {flow_weight}")

# Check stealth flow boost
flow_magnitude = "LOW" if flow_conv < 0.3 else ("MEDIUM" if flow_conv < 0.7 else "HIGH")
stealth_flow_boost = 0.2 if flow_magnitude == "LOW" else 0.0
flow_conv_adjusted = min(1.0, flow_conv + stealth_flow_boost)

print(f"  flow_magnitude: {flow_magnitude}")
print(f"  stealth_flow_boost: {stealth_flow_boost}")
print(f"  flow_conv_adjusted: {flow_conv_adjusted}")
print(f"  Expected flow_component: {flow_weight * flow_conv_adjusted}")

# Now compute actual
result = uw_composite_v2.compute_composite_score_v3(symbol, enriched, "NEUTRAL")
actual_flow = result.get("components", {}).get("flow", 0.0)

print(f"\nActual result:")
print(f"  flow_component: {actual_flow}")
print(f"  Match: {'YES' if abs(flow_weight * flow_conv_adjusted - actual_flow) < 0.01 else 'NO'}")
