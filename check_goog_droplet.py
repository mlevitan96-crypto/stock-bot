#!/usr/bin/env python3
"""Quick GOOG investigation on droplet"""
import json
from pathlib import Path

print("=" * 80)
print("GOOG INVESTIGATION")
print("=" * 80)
print()

# Check UW cache
print("1. GOOG in UW Cache:")
print("-" * 80)
try:
    cache_file = Path("data/uw_flow_cache.json")
    if cache_file.exists():
        cache = json.load(open(cache_file))
        goog_symbols = [k for k in cache.keys() if 'GOOG' in k]
        print(f"GOOG symbols found: {goog_symbols}")
        for sym in goog_symbols:
            d = cache[sym]
            print(f"\n{sym}:")
            print(f"  sentiment: {d.get('sentiment', 'MISS')}")
            print(f"  conviction: {d.get('conviction', 0):.3f}")
            print(f"  freshness: {d.get('freshness', 0):.3f}")
            print(f"  flow_conv: {d.get('flow_conv', 0):.3f}")
            print(f"  flow_magnitude: {d.get('flow_magnitude', 0):.3f}")
    else:
        print("UW cache file not found")
except Exception as e:
    print(f"Error: {e}")

print()

# Check recent orders
print("2. Recent Orders (last 50):")
print("-" * 80)
try:
    order_file = Path("data/order.jsonl")
    if order_file.exists():
        orders = []
        with open(order_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-50:]:
                if line.strip():
                    try:
                        orders.append(json.loads(line))
                    except:
                        pass
        
        goog_orders = [o for o in orders if 'GOOG' in o.get('symbol', '')]
        print(f"Total orders in last 50 lines: {len(orders)}")
        print(f"GOOG orders: {len(goog_orders)}")
        
        if goog_orders:
            print("\nGOOG orders:")
            for o in goog_orders[-10:]:
                print(f"  {o.get('symbol', '')} {o.get('side', '')} {o.get('qty', 0)} @ ${o.get('price', 0):.2f} - {o.get('ts', '')[:19]}")
    else:
        print("order.jsonl not found")
except Exception as e:
    print(f"Error: {e}")

print()

# Check state files
print("3. Position State:")
print("-" * 80)
try:
    state_file = Path("state/position_metadata.json")
    if state_file.exists() and state_file.stat().st_size > 0:
        state = json.load(open(state_file))
        print(f"Position metadata keys: {list(state.keys())}")
        goog_positions = {k: v for k, v in state.items() if 'GOOG' in k}
        if goog_positions:
            print(f"\nGOOG positions in state: {len(goog_positions)}")
            for sym, pos in goog_positions.items():
                print(f"  {sym}: {pos}")
        else:
            print("No GOOG positions in state file")
    else:
        print("Position metadata file not found or empty")
except Exception as e:
    print(f"Error: {e}")

print()

# Check logs if available
print("4. Recent Log Activity:")
print("-" * 80)
try:
    log_file = Path("logs/trading.log")
    if log_file.exists():
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent = lines[-100:] if len(lines) > 100 else lines
        
        goog_mentions = [l for l in recent if 'GOOG' in l.upper()]
        print(f"GOOG mentions in last 100 log lines: {len(goog_mentions)}")
        if goog_mentions:
            print("\nRecent GOOG activity:")
            for line in goog_mentions[-5:]:
                print(f"  {line.strip()[:150]}")
    else:
        print("Log file not found")
except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
