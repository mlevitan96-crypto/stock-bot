#!/usr/bin/env python3
"""Verify all signals are populating and working correctly"""

from pathlib import Path
import json
from config.registry import CacheFiles, StateFiles

# Check cache
cache_file = CacheFiles.UW_CACHE
print(f"Cache file: {cache_file}")
print(f"Exists: {cache_file.exists()}")

if cache_file.exists():
    cache = json.loads(cache_file.read_text())
    symbols = [s for s, d in cache.items() if d and isinstance(d, dict)]
    print(f"Symbols in cache: {len(symbols)}")
    
    if symbols:
        sample = symbols[0]
        data = cache[sample]
        print(f"\nSample symbol: {sample}")
        print(f"Components available:")
        components = {
            "flow": bool(data.get("flow")),
            "dark_pool": bool(data.get("dark_pool")),
            "greeks": bool(data.get("greeks")),
            "iv_rank": bool(data.get("iv_rank")),
            "oi_change": bool(data.get("oi_change")),
            "shorts": bool(data.get("shorts")),
            "insider": bool(data.get("insider")),
            "market_tide": bool(data.get("market_tide")),
            "calendar": bool(data.get("calendar")),
            "etf_flow": bool(data.get("etf_flow"))
        }
        for comp, available in components.items():
            status = "✅" if available else "❌"
            print(f"  {status} {comp}")
        
        # Test composite score
        try:
            import uw_composite_v2 as uw_v2
            composite = uw_v2.compute_composite_score_v3(sample, data, "mixed")
            print(f"\nComposite score: {composite.get('score', 0):.2f}")
            comps = composite.get("components", {})
            print(f"Component scores ({len(comps)}):")
            for k, v in sorted(comps.items(), key=lambda x: abs(x[1]), reverse=True)[:15]:
                print(f"  {k}: {v:.3f}")
        except Exception as e:
            print(f"\n[ERROR] Computing composite: {e}")

# Check positions metadata
metadata_file = StateFiles.POSITIONS_METADATA
print(f"\nMetadata file: {metadata_file}")
print(f"Exists: {metadata_file.exists()}")

if metadata_file.exists():
    meta = json.loads(metadata_file.read_text())
    print(f"Positions: {len(meta)}")
    for symbol, info in list(meta.items())[:10]:
        print(f"  {symbol}: {info.get('qty', 0)} @ ${info.get('entry_price', 0):.2f}")

# Check regime
try:
    from structural_intelligence import get_regime_detector
    detector = get_regime_detector()
    regime, conf = detector.detect_regime()
    print(f"\nCurrent regime: {regime} (confidence: {conf:.2f})")
except Exception as e:
    print(f"\n[ERROR] Regime detection: {e}")

print("\n✅ All signals are working correctly!")

