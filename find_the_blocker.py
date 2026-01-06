#!/usr/bin/env python3
"""Find the actual blocker preventing trades"""

import json
import sys
from pathlib import Path
sys.path.insert(0, '/root/stock-bot')

print("=" * 80)
print("FINDING THE BLOCKER")
print("=" * 80)

# 1. Check cache
cache_file = Path("data/uw_flow_cache.json")
if not cache_file.exists():
    print("\nBLOCKER #1: Cache file missing!")
    sys.exit(1)

cache = json.load(open(cache_file))
syms = [k for k in cache.keys() if not k.startswith("_")]
print(f"\nCache: {len(syms)} symbols")

if len(syms) == 0:
    print("BLOCKER #2: Cache has no symbol keys!")
    print(f"Total keys: {len(cache)}")
    print(f"Keys: {list(cache.keys())[:10]}")
    sys.exit(1)

# 2. Test one symbol
symbol = syms[0]
print(f"\nTesting symbol: {symbol}")

data = cache[symbol]
print(f"Sentiment: {data.get('sentiment')}")
print(f"Conviction: {data.get('conviction')}")

if not data.get('sentiment'):
    print(f"BLOCKER #3: Symbol {symbol} has no sentiment!")
if data.get('conviction', 0) == 0:
    print(f"BLOCKER #4: Symbol {symbol} has conviction=0!")

# 3. Test enrichment
import uw_enrichment_v2 as uw_enrich
enriched = uw_enrich.enrich_signal(symbol, cache, "mixed")

if not enriched:
    print("BLOCKER #5: enrich_signal returned empty!")
    sys.exit(1)

print(f"Enriched sentiment: {enriched.get('sentiment')}")
print(f"Enriched conviction: {enriched.get('conviction')}")
print(f"Enriched freshness: {enriched.get('freshness')}")

# 4. Test scoring
import uw_composite_v2 as uw_v2
composite = uw_v2.compute_composite_score_v3(symbol, enriched, "mixed")

if not composite:
    print("BLOCKER #6: Composite scoring returned None!")
    sys.exit(1)

score = composite.get("score", 0.0)
threshold = uw_v2.get_threshold(symbol, "base")
components = composite.get("components", {})

print(f"\nScore: {score:.2f}")
print(f"Threshold: {threshold:.2f}")
print(f"Flow component: {components.get('flow', 0):.2f}")
print(f"DP component: {components.get('dark_pool', 0):.2f}")

if score < threshold:
    print(f"\nBLOCKER #7: Score {score:.2f} < threshold {threshold:.2f}")
    if components.get('flow', 0) == 0:
        print("  - Flow component is 0 (conviction=0?)")

# 5. Test gate
gate_result = uw_v2.should_enter_v2(composite, symbol, "base")
print(f"\nGate result: {gate_result}")

if not gate_result:
    toxicity = composite.get("toxicity", 0.0)
    freshness = composite.get("freshness", 1.0)
    print(f"  Toxicity: {toxicity:.2f} (must be <= 0.90)")
    print(f"  Freshness: {freshness:.2f} (must be >= 0.30)")
    
    if toxicity > 0.90:
        print("BLOCKER #8: Toxicity too high!")
    if freshness < 0.30:
        print("BLOCKER #9: Freshness too low!")

print("\n" + "=" * 80)
