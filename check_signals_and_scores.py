#!/usr/bin/env python3
"""Check signals, scores, and why no orders"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, '/root/stock-bot')

print("=" * 80)
print("SIGNALS AND SCORES CHECK")
print("=" * 80)

# 1. Recent signals
print("\n1. RECENT SIGNALS:")
signal_file = Path("logs/signals.jsonl")
if signal_file.exists():
    with open(signal_file) as f:
        lines = f.readlines()
        recent = [json.loads(l) for l in lines[-50:] if l.strip()]
        print(f"   Found {len(recent)} recent signals")
        for sig in recent[-10:]:
            cluster = sig.get('cluster', {})
            ts = sig.get('ts', '')[:19] if sig.get('ts') else 'N/A'
            symbol = cluster.get('ticker', 'N/A')
            score = sig.get('composite_score', sig.get('score', 'N/A'))
            direction = cluster.get('direction', 'N/A')
            print(f"   {ts} | {symbol:6} | {direction:8} | score: {score}")
else:
    print("   No signals file found")

# 2. Recent gate events
print("\n2. RECENT GATE EVENTS:")
gate_file = Path("logs/gate.jsonl")
if gate_file.exists():
    with open(gate_file) as f:
        lines = f.readlines()
        recent = [json.loads(l) for l in lines[-50:] if l.strip()]
        print(f"   Found {len(recent)} recent gate events")
        blocked = [g for g in recent if 'blocked' in str(g).lower() or 'gate' in str(g).lower()]
        for gate in blocked[-10:]:
            symbol = gate.get('symbol', 'N/A')
            reason = gate.get('reason', gate.get('msg', 'N/A'))
            score = gate.get('score', gate.get('composite_score', 'N/A'))
            print(f"   {symbol:6} | {reason[:50]:50} | score: {score}")
else:
    print("   No gate file found")

# 3. Check cache data quality
print("\n3. CACHE DATA QUALITY:")
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache = json.load(open(cache_file))
    symbols = [k for k in cache.keys() if not k.startswith("_")]
    print(f"   Symbols in cache: {len(symbols)}")
    if symbols:
        sample = symbols[0]
        sample_data = cache.get(sample, {})
        has_flow = 'flow_trades' in sample_data or 'sentiment' in sample_data
        has_conviction = 'conviction' in sample_data
        print(f"   Sample ({sample}): has_flow={has_flow}, has_conviction={has_conviction}")
        if has_flow:
            print(f"      sentiment: {sample_data.get('sentiment', 'N/A')}")
            print(f"      conviction: {sample_data.get('conviction', 'N/A')}")

# 4. Check thresholds and weights
print("\n4. THRESHOLDS AND WEIGHTS:")
try:
    import uw_composite_v2
    threshold = uw_composite_v2.get_threshold("AAPL", "base")
    flow_weight = uw_composite_v2.get_weight("options_flow", "mixed")
    print(f"   Entry threshold (base): {threshold:.2f}")
    print(f"   Flow weight: {flow_weight:.3f}")
except Exception as e:
    print(f"   Error checking: {e}")

# 5. Check recent orders
print("\n5. RECENT ORDERS:")
order_file = Path("logs/order.jsonl")
if order_file.exists():
    with open(order_file) as f:
        lines = f.readlines()
        recent = [json.loads(l) for l in lines[-20:] if l.strip()]
        print(f"   Found {len(recent)} recent orders")
        for o in recent[-10:]:
            ts = o.get('ts', '')[:19] if o.get('ts') else 'N/A'
            symbol = o.get('symbol', 'N/A')
            action = o.get('action', 'N/A')[:30]
            print(f"   {ts} | {symbol:6} | {action}")
else:
    print("   No orders file found")

print("\n" + "=" * 80)
