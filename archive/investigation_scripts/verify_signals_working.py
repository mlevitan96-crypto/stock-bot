#!/usr/bin/env python3
"""
Quick Signal Verification Script
=================================
Verifies that signals are detected correctly by SRE monitoring.
"""

import json
from pathlib import Path

print("=" * 80)
print("SIGNAL VERIFICATION")
print("=" * 80)

# 1. Check cache directly
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache = json.loads(cache_file.read_text())
    symbols = [k for k in cache.keys() if not k.startswith("_")][:5]
    print(f"\n1. Cache has {len(symbols)} symbols")
    
    for sym in symbols:
        data = cache.get(sym, {})
        print(f"\n   {sym}:")
        print(f"      iv_term_skew: {data.get('iv_term_skew')}")
        print(f"      smile_slope: {data.get('smile_slope')}")
        print(f"      insider: {bool(data.get('insider'))}")
else:
    print("\n❌ Cache file not found!")

# 2. Check SRE monitoring
print("\n" + "=" * 80)
print("2. SRE Monitoring Detection")
print("=" * 80)

try:
    from sre_monitoring import get_sre_health
    health = get_sre_health()
    
    signals = health.get("signal_components", {})
    print(f"\n   Found {len(signals)} signals:")
    
    for name, signal_health in signals.items():
        status = signal_health.get("status", "unknown")
        status_icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
        print(f"   {status_icon} {name}: {status}")
        
        if "found_in_symbols" in signal_health.get("details", {}):
            symbols_found = signal_health["details"]["found_in_symbols"]
            print(f"      Found in: {', '.join(symbols_found)}")
    
    # Check overall health
    overall = health.get("overall_health", "unknown")
    print(f"\n   Overall Health: {overall.upper()}")
    
    warnings = health.get("warnings", [])
    if warnings:
        print(f"   Warnings: {', '.join(warnings)}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# 3. Test dashboard API endpoint
print("\n" + "=" * 80)
print("3. Dashboard API Endpoint")
print("=" * 80)

try:
    import requests
    resp = requests.get("http://localhost:5000/api/sre/health", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        signals = data.get("signal_components", {})
        print(f"\n   Dashboard API returned {len(signals)} signals:")
        
        for name, signal_health in signals.items():
            status = signal_health.get("status", "unknown")
            status_icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"
            print(f"   {status_icon} {name}: {status}")
    else:
        print(f"   ❌ API returned status {resp.status_code}")
except Exception as e:
    print(f"   ❌ Error calling dashboard API: {e}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print("\nIf signals show as 'healthy' above, they should appear healthy on the dashboard.")
print("Refresh your dashboard and check the SRE Monitoring tab.")



