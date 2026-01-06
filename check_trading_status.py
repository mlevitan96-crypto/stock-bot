#!/usr/bin/env python3
"""Check why trading isn't happening"""

import json
from pathlib import Path
from datetime import datetime
try:
    import pytz
except ImportError:
    pytz = None

print("=" * 80)
print("TRADING STATUS CHECK")
print("=" * 80)
print()

# 1. Check weights file
weights_file = Path("data/uw_weights.json")
if weights_file.exists():
    w = json.load(weights_file.open())
    print(f"✅ Weights file: {len(w.get('weights', {}))} components")
else:
    print("❌ Weights file: MISSING")

# 2. Check today's signals
signals_file = Path("logs/signals.jsonl")
today_signals = []
if signals_file.exists():
    with signals_file.open() as f:
        for line in f:
            try:
                data = json.loads(line)
                if "2026-01-06" in data.get("ts", ""):
                    today_signals.append(data)
            except:
                continue
print(f"\n📊 Signals today: {len(today_signals)}")
if today_signals:
    for sig in today_signals[-5:]:
        ticker = sig.get("cluster", {}).get("ticker", "UNK")
        ts = sig.get("ts", "")[:19]
        print(f"   {ticker} at {ts}")

# 3. Check today's gate events
gates_file = Path("logs/gate.jsonl")
today_gates = []
if gates_file.exists():
    with gates_file.open() as f:
        for line in f:
            try:
                data = json.loads(line)
                if "2026-01-06" in data.get("ts", ""):
                    today_gates.append(data)
            except:
                continue
print(f"\n🚪 Gate events today: {len(today_gates)}")
if today_gates:
    for gate in today_gates[-10:]:
        symbol = gate.get("symbol", "UNK")
        msg = gate.get("msg", "unknown")
        print(f"   {symbol}: {msg}")

# 4. Check run cycles
run_file = Path("logs/run.jsonl")
today_runs = []
if run_file.exists():
    with run_file.open() as f:
        for line in f:
            try:
                data = json.loads(line)
                if "2026-01-06" in data.get("ts", ""):
                    today_runs.append(data)
            except:
                continue
print(f"\n🔄 Run cycles today: {len(today_runs)}")
if today_runs:
    for run in today_runs[-5:]:
        clusters = run.get("clusters", 0)
        orders = run.get("orders", 0)
        market_open = run.get("market_open", False)
        print(f"   clusters={clusters}, orders={orders}, market_open={market_open}")

# 5. Check UW cache
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache = json.load(cache_file.open())
    symbols = [k for k in cache.keys() if not k.startswith("_")]
    print(f"\n💾 UW cache: {len(symbols)} symbols")
    if symbols:
        print(f"   Sample: {', '.join(symbols[:5])}")
else:
    print("\n❌ UW cache: FILE MISSING")

# 6. Check market status
try:
    now = datetime.now(pytz.timezone("America/New_York"))
    is_open = (9 <= now.hour < 16) and (now.weekday() < 5)
    print(f"\n📈 Market status: {'OPEN' if is_open else 'CLOSED'}")
    print(f"   ET time: {now.strftime('%H:%M')}")
except Exception as e:
    print(f"\n⚠️  Market status check failed: {e}")

print("\n" + "=" * 80)
