#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0, '/root/stock-bot')

print("CHECKING WHY NO TRADES")
print("=" * 80)

# 1. Check cache
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache = json.load(open(cache_file))
    syms = [k for k in cache.keys() if not k.startswith("_")]
    print(f"Cache: {len(syms)} symbols")
    if syms:
        s = syms[0]
        d = cache[s]
        print(f"Sample {s}: sentiment={d.get('sentiment')}, conviction={d.get('conviction')}")
        print(f"  has dark_pool: {bool(d.get('dark_pool'))}")
        print(f"  has insider: {bool(d.get('insider'))}")
        
        # Test scoring
        import uw_enrichment_v2 as uw_enrich
        import uw_composite_v2 as uw_v2
        
        enriched = uw_enrich.enrich_signal(s, cache, "mixed")
        composite = uw_v2.compute_composite_score_v3(s, enriched, "mixed")
        
        if composite:
            score = composite.get("score", 0.0)
            threshold = uw_v2.get_threshold(s, "base")
            toxicity = composite.get("toxicity", 0.0)
            freshness = composite.get("freshness", 1.0)
            passed = score >= threshold and toxicity <= 0.90 and freshness >= 0.30
            
            print(f"\nScoring test for {s}:")
            print(f"  Score: {score:.2f}")
            print(f"  Threshold: {threshold:.2f}")
            print(f"  Toxicity: {toxicity:.2f} (max 0.90)")
            print(f"  Freshness: {freshness:.2f} (min 0.30)")
            print(f"  Would pass gate: {passed}")
else:
    print("Cache file missing!")

# 2. Check recent run logs
run_file = Path("logs/run.jsonl")
if run_file.exists():
    with open(run_file) as f:
        lines = f.readlines()
        if lines:
            last = json.loads(lines[-1])
            print(f"\nLast cycle: clusters={last.get('clusters')}, orders={last.get('orders')}")

print("=" * 80)
