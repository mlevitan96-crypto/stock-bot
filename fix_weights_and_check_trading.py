#!/usr/bin/env python3
"""
Fix missing weights file and check why trading isn't happening
"""

import json
import time
from pathlib import Path

def create_weights_file():
    """Create default weights file"""
    weights = {
        "weights": {
            "options_flow": 2.4,
            "dark_pool": 1.3,
            "insider": 0.5,
            "iv_term_skew": 0.6,
            "smile_slope": 0.35,
            "whale_persistence": 0.7,
            "event_alignment": 0.4,
            "toxicity_penalty": -0.9,
            "temporal_motif": 0.6,
            "regime_modifier": 0.3,
            "congress": 0.9,
            "shorts_squeeze": 0.7,
            "institutional": 0.5,
            "market_tide": 0.4,
            "calendar_catalyst": 0.45,
            "etf_flow": 0.3,
            "greeks_gamma": 0.4,
            "ftd_pressure": 0.3,
            "iv_rank": 0.2,
            "oi_change": 0.35,
            "squeeze_score": 0.2
        },
        "updated_at": int(time.time()),
        "updated_dt": "2026-01-06 00:00:00 UTC",
        "source": "default_weights_v3"
    }
    
    Path("data").mkdir(exist_ok=True)
    with open("data/uw_weights.json", "w") as f:
        json.dump(weights, f, indent=2)
    print("✅ Created data/uw_weights.json")

def check_today_signals():
    """Check if signals are being generated today"""
    signals_file = Path("logs/signals.jsonl")
    if not signals_file.exists():
        print("⚠️  signals.jsonl not found")
        return
    
    today_signals = []
    with signals_file.open() as f:
        for line in f:
            try:
                data = json.loads(line)
                if "2026-01-06" in data.get("ts", ""):
                    today_signals.append(data)
            except:
                continue
    
    print(f"📊 Signals today: {len(today_signals)}")
    if today_signals:
        print("   Recent signals:")
        for sig in today_signals[-5:]:
            ticker = sig.get("cluster", {}).get("ticker", "UNKNOWN")
            print(f"     {ticker}")

def check_today_gates():
    """Check gate events today"""
    gates_file = Path("logs/gate.jsonl")
    if not gates_file.exists():
        print("⚠️  gate.jsonl not found")
        return
    
    today_gates = []
    with gates_file.open() as f:
        for line in f:
            try:
                data = json.loads(line)
                if "2026-01-06" in data.get("ts", ""):
                    today_gates.append(data)
            except:
                continue
    
    print(f"🚪 Gate events today: {len(today_gates)}")
    if today_gates:
        print("   Recent gate events:")
        for gate in today_gates[-5:]:
            msg = gate.get("msg", "unknown")
            symbol = gate.get("symbol", "UNKNOWN")
            print(f"     {symbol}: {msg}")

def check_uw_cache():
    """Check UW cache status"""
    cache_file = Path("data/uw_flow_cache.json")
    if not cache_file.exists():
        print("⚠️  UW cache file not found")
        return
    
    with cache_file.open() as f:
        cache = json.load(f)
    
    symbol_count = len([k for k in cache.keys() if not k.startswith("_")])
    print(f"💾 UW cache: {symbol_count} symbols")
    
    if symbol_count > 0:
        sample_symbols = [k for k in cache.keys() if not k.startswith("_")][:5]
        print(f"   Sample symbols: {', '.join(sample_symbols)}")

if __name__ == "__main__":
    print("=" * 80)
    print("FIXING WEIGHTS AND CHECKING TRADING STATUS")
    print("=" * 80)
    print()
    
    create_weights_file()
    print()
    check_uw_cache()
    print()
    check_today_signals()
    print()
    check_today_gates()
    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
