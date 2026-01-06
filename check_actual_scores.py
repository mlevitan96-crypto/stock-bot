#!/usr/bin/env python3
"""Check actual composite scores being generated"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, '/root/stock-bot')

print("=" * 80)
print("ACTUAL SCORES CHECK")
print("=" * 80)

# 1. Check recent signals with scores
print("\n1. RECENT SIGNALS WITH SCORES:")
signal_file = Path("logs/signals.jsonl")
if signal_file.exists():
    with open(signal_file) as f:
        lines = f.readlines()
        recent = []
        for l in lines[-100:]:
            if l.strip():
                try:
                    sig = json.loads(l)
                    score = sig.get('composite_score', sig.get('score', 'N/A'))
                    if score != 'N/A':
                        recent.append(sig)
                except:
                    pass
        
        print(f"   Found {len(recent)} signals with scores (last 100 lines)")
        for sig in recent[-10:]:
            cluster = sig.get('cluster', {})
            ts = sig.get('ts', '')[:19] if sig.get('ts') else 'N/A'
            symbol = cluster.get('ticker', 'N/A')
            score = sig.get('composite_score', sig.get('score', 'N/A'))
            direction = cluster.get('direction', 'N/A')
            print(f"   {ts} | {symbol:6} | {direction:8} | score: {score}")

# 2. Check gate events with scores
print("\n2. GATE EVENTS WITH SCORES:")
gate_file = Path("logs/gate.jsonl")
if gate_file.exists():
    with open(gate_file) as f:
        lines = f.readlines()
        recent = []
        for l in lines[-100:]:
            if l.strip():
                try:
                    gate = json.loads(l)
                    score = gate.get('score', gate.get('composite_score', 'N/A'))
                    if score != 'N/A':
                        recent.append(gate)
                except:
                    pass
        
        print(f"   Found {len(recent)} gate events with scores")
        for gate in recent[-10:]:
            symbol = gate.get('symbol', 'N/A')
            reason = gate.get('reason', gate.get('msg', 'N/A'))[:40]
            score = gate.get('score', gate.get('composite_score', 'N/A'))
            print(f"   {symbol:6} | {reason:40} | score: {score}")

# 3. Check composite scoring directly
print("\n3. TEST COMPOSITE SCORING:")
try:
    import uw_enrichment_v2 as uw_enrich
    import uw_composite_v2 as uw_v2
    from pathlib import Path
    import json
    
    cache_file = Path("data/uw_flow_cache.json")
    if cache_file.exists():
        cache = json.load(open(cache_file))
        symbols = [k for k in cache.keys() if not k.startswith("_")][:5]
        
        print(f"   Testing composite scoring for {len(symbols)} symbols:")
        for ticker in symbols:
            try:
                enriched = uw_enrich.enrich_signal(ticker, cache, "mixed")
                composite = uw_v2.compute_composite_score_v3(ticker, enriched, "mixed")
                if composite:
                    score = composite.get("score", 0.0)
                    threshold = uw_v2.get_threshold(ticker, "base")
                    passed = score >= threshold
                    print(f"   {ticker:6} | score: {score:5.2f} | threshold: {threshold:4.2f} | {'PASS' if passed else 'FAIL'}")
            except Exception as e:
                print(f"   {ticker:6} | ERROR: {str(e)[:50]}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 80)
