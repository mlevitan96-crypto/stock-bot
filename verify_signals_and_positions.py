#!/usr/bin/env python3
"""
Comprehensive verification of signals, positions, and dashboard data
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def check_positions():
    """Check actual Alpaca positions"""
    try:
        import alpaca_trade_api as tradeapi
        api = tradeapi.REST(
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_API_SECRET"),
            os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
            api_version="v2"
        )
        positions = api.list_positions()
        return {
            "count": len(positions),
            "positions": [{
                "symbol": p.symbol,
                "qty": float(p.qty),
                "entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "pnl": float(p.unrealized_pl),
                "pnl_pct": float(p.unrealized_plpc) * 100
            } for p in positions]
        }
    except Exception as e:
        return {"error": str(e)}

def check_metadata_positions():
    """Check positions in metadata"""
    metadata_file = Path("state/positions_metadata.json")
    if not metadata_file.exists():
        return {"error": "Metadata file not found"}
    
    metadata = json.loads(metadata_file.read_text())
    return {
        "count": len(metadata),
        "positions": [{
            "symbol": symbol,
            "qty": info.get("qty", 0),
            "entry_price": info.get("entry_price", 0),
            "entry_score": info.get("entry_score", 0)
        } for symbol, info in metadata.items()]
    }

def check_signal_components():
    """Check if all signal components are populating"""
    cache_file = Path("data/uw_cache.json")
    if not cache_file.exists():
        return {"error": "Cache file not found"}
    
    cache = json.loads(cache_file.read_text())
    symbols = [s for s, d in cache.items() if d and isinstance(d, dict)]
    
    if not symbols:
        return {"error": "No symbols in cache"}
    
    # Check a sample symbol
    sample = symbols[0]
    data = cache[sample]
    
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
    
    # Check composite score
    try:
        import uw_composite_v2 as uw_v2
        composite = uw_v2.compute_composite_score_v3(sample, data, "mixed")
        score = composite.get("score", 0)
        comps = composite.get("components", {})
    except Exception as e:
        score = None
        comps = {}
        error = str(e)
    
    return {
        "symbols_in_cache": len(symbols),
        "sample_symbol": sample,
        "components_available": components,
        "composite_score": score,
        "component_scores": dict(sorted(comps.items(), key=lambda x: abs(x[1]), reverse=True)[:10]) if comps else {},
        "error": error if score is None else None
    }

def check_regime():
    """Check current regime"""
    try:
        from structural_intelligence import get_regime_detector
        detector = get_regime_detector()
        regime, conf = detector.detect_regime()
        return {
            "regime": regime,
            "confidence": conf
        }
    except Exception as e:
        return {"error": str(e)}

def check_xai_regime():
    """Check regime in XAI logs"""
    xai_file = Path("data/explainable_logs.jsonl")
    if not xai_file.exists():
        return {"error": "XAI file not found"}
    
    records = []
    for line in xai_file.read_text().splitlines()[-100:]:
        if line.strip():
            try:
                records.append(json.loads(line))
            except:
                continue
    
    exits = [r for r in records if r.get("type") == "trade_exit" and "TEST" not in str(r.get("symbol", "")).upper()]
    entries = [r for r in records if r.get("type") == "trade_entry" and "TEST" not in str(r.get("symbol", "")).upper()]
    
    exit_regimes = {}
    for e in exits:
        regime = e.get("regime", "unknown")
        exit_regimes[regime] = exit_regimes.get(regime, 0) + 1
    
    entry_regimes = {}
    for e in entries:
        regime = e.get("regime", "unknown")
        entry_regimes[regime] = entry_regimes.get(regime, 0) + 1
    
    return {
        "exits": len(exits),
        "entries": len(entries),
        "exit_regimes": exit_regimes,
        "entry_regimes": entry_regimes,
        "recent_exits_with_regime": [{"symbol": e.get("symbol"), "regime": e.get("regime")} for e in exits[:5]]
    }

def main():
    print("=" * 80)
    print("COMPREHENSIVE SIGNAL & POSITION VERIFICATION")
    print("=" * 80)
    print()
    
    # Check positions
    print("1. ACTUAL ALPACA POSITIONS")
    print("-" * 80)
    positions = check_positions()
    if "error" in positions:
        print(f"   [ERROR] {positions['error']}")
    else:
        print(f"   Count: {positions['count']}")
        for p in positions['positions']:
            pnl_sign = "+" if p['pnl'] >= 0 else ""
            print(f"   {p['symbol']}: {p['qty']} @ ${p['entry_price']:.2f} (Current: ${p['current_price']:.2f}, P&L: {pnl_sign}${p['pnl']:.2f}, {pnl_sign}{p['pnl_pct']:.2f}%)")
    print()
    
    # Check metadata positions
    print("2. METADATA POSITIONS")
    print("-" * 80)
    metadata = check_metadata_positions()
    if "error" in metadata:
        print(f"   [ERROR] {metadata['error']}")
    else:
        print(f"   Count: {metadata['count']}")
        for p in metadata['positions']:
            print(f"   {p['symbol']}: {p['qty']} @ ${p['entry_price']:.2f} (Score: {p['entry_score']:.2f})")
    print()
    
    # Check signal components
    print("3. SIGNAL COMPONENTS")
    print("-" * 80)
    signals = check_signal_components()
    if "error" in signals:
        print(f"   [ERROR] {signals['error']}")
    else:
        print(f"   Symbols in cache: {signals['symbols_in_cache']}")
        print(f"   Sample symbol: {signals['sample_symbol']}")
        print(f"   Components available:")
        for comp, available in signals['components_available'].items():
            status = "✅" if available else "❌"
            print(f"     {status} {comp}: {available}")
        if signals.get("composite_score") is not None:
            print(f"   Composite score: {signals['composite_score']:.2f}")
            print(f"   Component scores:")
            for comp, score in signals['component_scores'].items():
                print(f"     {comp}: {score:.3f}")
        if signals.get("error"):
            print(f"   [ERROR] Computing composite: {signals['error']}")
    print()
    
    # Check regime
    print("4. CURRENT REGIME")
    print("-" * 80)
    regime = check_regime()
    if "error" in regime:
        print(f"   [ERROR] {regime['error']}")
    else:
        print(f"   Regime: {regime['regime']}")
        print(f"   Confidence: {regime['confidence']:.2f}")
    print()
    
    # Check XAI regime
    print("5. REGIME IN XAI LOGS")
    print("-" * 80)
    xai_regime = check_xai_regime()
    if "error" in xai_regime:
        print(f"   [ERROR] {xai_regime['error']}")
    else:
        print(f"   Exits: {xai_regime['exits']}")
        print(f"   Entries: {xai_regime['entries']}")
        print(f"   Exit regimes: {xai_regime['exit_regimes']}")
        print(f"   Entry regimes: {xai_regime['entry_regimes']}")
        print(f"   Recent exits with regime:")
        for e in xai_regime['recent_exits_with_regime']:
            print(f"     {e['symbol']}: {e['regime']}")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    issues = []
    if positions.get("count", 0) == 0 and metadata.get("count", 0) == 0:
        issues.append("No positions found in Alpaca or metadata")
    if positions.get("count", 0) != metadata.get("count", 0):
        issues.append(f"Position mismatch: Alpaca={positions.get('count', 0)}, Metadata={metadata.get('count', 0)}")
    if signals.get("error"):
        issues.append(f"Signal computation error: {signals['error']}")
    missing_components = [k for k, v in signals.get("components_available", {}).items() if not v]
    if missing_components:
        issues.append(f"Missing components: {', '.join(missing_components)}")
    if xai_regime.get("exit_regimes", {}).get("unknown", 0) > xai_regime.get("exits", 0) * 0.5:
        issues.append("Many exits have 'unknown' regime in XAI logs")
    
    if issues:
        print("⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ NO ISSUES DETECTED")
        print("   All signals are populating correctly")
        print("   Positions are tracked correctly")
        print("   Regime is being detected")
    
    print()

if __name__ == "__main__":
    main()

