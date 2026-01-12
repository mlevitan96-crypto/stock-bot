#!/usr/bin/env python3
"""Get positions via StrategyEngine - avoids credential issues"""
import sys
sys.path.insert(0, '.')

try:
    from main import StrategyEngine
    
    print("=" * 80)
    print("CURRENT POSITIONS FROM ALPACA API")
    print("=" * 80)
    print()
    
    engine = StrategyEngine()
    positions = engine.executor.api.list_positions()
    
    print(f"Total positions: {len(positions)}")
    print()
    
    goog_positions = []
    total_pl = 0.0
    goog_pl = 0.0
    
    if positions:
        for p in positions:
            pl = float(p.unrealized_pl)
            total_pl += pl
            is_goog = 'GOOG' in p.symbol
            if is_goog:
                goog_positions.append(p)
                goog_pl += pl
            
            print(f"{p.symbol:6s} {float(p.qty):8.2f} @ ${float(p.avg_entry_price):7.2f} | "
                  f"P/L: ${pl:8.2f} ({float(p.unrealized_plpc)*100:6.2f}%)")
        
        print()
        print(f"Total P/L: ${total_pl:.2f}")
        print(f"GOOG positions: {len(goog_positions)}/{len(positions)} "
              f"({len(goog_positions)/len(positions)*100:.1f}%)" if positions else "0")
        print(f"GOOG P/L: ${goog_pl:.2f}")
        
        if len(goog_positions) > len(positions) * 0.5:
            print()
            print("⚠️  WARNING: GOOG concentration > 50%!")
    else:
        print("No positions open")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
