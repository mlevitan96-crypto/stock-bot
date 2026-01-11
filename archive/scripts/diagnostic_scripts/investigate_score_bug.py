#!/usr/bin/env python3
"""Investigate why scores are so low - trace through scoring pipeline"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def check_cache_data():
    """Check what's actually in the cache"""
    print("=" * 80)
    print("1. CACHE DATA QUALITY CHECK")
    print("=" * 80)
    
    cache_path = Path("data/uw_flow_cache.json")
    if not cache_path.exists():
        print("❌ Cache file not found!")
        return None
    
    cache = json.load(open(cache_path))
    symbols = [k for k in cache.keys() if not k.startswith("_")]
    
    print(f"Total symbols in cache: {len(symbols)}")
    
    # Find symbols with good conviction
    good_symbols = []
    for s in symbols:
        data = cache[s]
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                continue
        
        if not isinstance(data, dict):
            continue
        
        sentiment = data.get("sentiment", "UNKNOWN")
        conviction = data.get("conviction", 0.0)
        
        if isinstance(conviction, (int, float)) and conviction > 0.3:
            good_symbols.append((s, sentiment, conviction))
    
    print(f"\nSymbols with conviction > 0.3: {len(good_symbols)}")
    if good_symbols:
        print("\nTop symbols by conviction:")
        sorted_good = sorted(good_symbols, key=lambda x: x[2], reverse=True)[:10]
        for s, sent, conv in sorted_good:
            print(f"  {s}: sentiment={sent}, conviction={conv:.3f}")
        return sorted_good[0][0]  # Return best symbol
    else:
        print("❌ NO SYMBOLS WITH HIGH CONVICTION!")
        # Show what we have
        print("\nSample of all symbols:")
        for s in symbols[:10]:
            data = cache[s]
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    continue
            sentiment = data.get("sentiment", "MISSING")
            conviction = data.get("conviction", "MISSING")
            print(f"  {s}: sentiment={sentiment}, conviction={conviction}")
        return None

def trace_scoring(symbol):
    """Manually trace through scoring for one symbol"""
    print("\n" + "=" * 80)
    print(f"2. TRACING SCORE CALCULATION FOR {symbol}")
    print("=" * 80)
    
    cache_path = Path("data/uw_flow_cache.json")
    cache = json.load(open(cache_path))
    data = cache.get(symbol, {})
    
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            print("❌ Failed to parse data")
            return
    
    print("\nRaw cache data:")
    print(f"  sentiment: {data.get('sentiment')}")
    print(f"  conviction: {data.get('conviction')}")
    print(f"  dark_pool: {bool(data.get('dark_pool'))}")
    print(f"  insider: {bool(data.get('insider'))}")
    
    # Test enrich_signal
    print("\n--- Testing enrich_signal ---")
    try:
        import uw_enrichment_v2
        enriched = uw_enrichment_v2.enrich_signal(symbol, cache, "NEUTRAL")
        
        print(f"Enriched output:")
        print(f"  sentiment: {enriched.get('sentiment')}")
        print(f"  conviction: {enriched.get('conviction')}")
        print(f"  dark_pool: {enriched.get('dark_pool')}")
        print(f"  iv_term_skew: {enriched.get('iv_term_skew')}")
        print(f"  freshness: {enriched.get('freshness')}")
        
        # Test compute_composite_score_v3
        print("\n--- Testing compute_composite_score_v3 ---")
        import uw_composite_v2
        result = uw_composite_v2.compute_composite_score_v3(symbol, enriched, "NEUTRAL")
        
        print(f"Composite score result:")
        print(f"  score: {result.get('score')}")
        print(f"  components:")
        components = result.get('components', {})
        print(f"    flow: {components.get('flow')}")
        print(f"    dark_pool: {components.get('dark_pool')}")
        print(f"    insider: {components.get('insider')}")
        print(f"    freshness_factor: {components.get('freshness_factor')}")
        
        # Check why flow_component is low
        print("\n--- Flow Component Analysis ---")
        flow_conv = enriched.get("conviction", 0.0)
        flow_sent = enriched.get("sentiment", "NEUTRAL")
        print(f"  flow_conv from enriched: {flow_conv}")
        print(f"  flow_sent from enriched: {flow_sent}")
        print(f"  flow_component: {components.get('flow')}")
        
        # Calculate what flow_component should be
        weights = uw_composite_v2.WEIGHTS_V3
        flow_weight = weights.get("options_flow", 2.4)
        expected_flow = flow_weight * flow_conv
        print(f"  Expected flow_component (weight={flow_weight} * conviction={flow_conv}): {expected_flow:.3f}")
        print(f"  Actual flow_component: {components.get('flow')}")
        
        if abs(components.get('flow', 0) - expected_flow) > 0.01:
            print(f"  ❌ MISMATCH! Flow component is wrong!")
        
        # Check threshold
        thresholds = uw_composite_v2.ENTRY_THRESHOLDS
        print(f"\n--- Threshold Check ---")
        print(f"  Thresholds: {thresholds}")
        print(f"  Score: {result.get('score')}")
        print(f"  Should pass: {result.get('score') >= thresholds.get('base', 2.7)}")
        
    except Exception as e:
        print(f"❌ ERROR during scoring: {e}")
        import traceback
        traceback.print_exc()

def check_recent_attribution():
    """Check recent attribution to see what scores are actually being generated"""
    print("\n" + "=" * 80)
    print("3. RECENT ATTRIBUTION ANALYSIS")
    print("=" * 80)
    
    attr_path = Path("data/uw_attribution.jsonl")
    if not attr_path.exists():
        print("❌ Attribution file not found")
        return
    
    records = []
    with open(attr_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except:
                    pass
    
    if not records:
        print("❌ No attribution records")
        return
    
    recent = records[-20:]
    print(f"Recent records (last 20):")
    
    for r in recent:
        symbol = r.get("symbol", "UNKNOWN")
        score = r.get("score", 0.0)
        components = r.get("components", {})
        flow = components.get("flow", 0.0)
        decision = r.get("decision", "unknown")
        
        print(f"  {symbol}: score={score:.3f}, flow={flow:.3f}, decision={decision}")

def main():
    print("\n" + "=" * 80)
    print("SCORE BUG INVESTIGATION")
    print("=" * 80)
    
    # 1. Check cache
    best_symbol = check_cache_data()
    
    # 2. Trace scoring for best symbol
    if best_symbol:
        trace_scoring(best_symbol)
    else:
        print("\n❌ No good symbols found - cache quality issue!")
    
    # 3. Check recent attribution
    check_recent_attribution()

if __name__ == "__main__":
    main()
