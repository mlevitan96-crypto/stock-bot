#!/usr/bin/env python3
"""Check Alpaca positions and signal generation"""

import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from main import Config, tradeapi
    import alpaca_trade_api as tradeapi
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def check_alpaca_positions():
    """Check actual Alpaca positions"""
    print("=" * 80)
    print("ALPACA POSITIONS CHECK")
    print("=" * 80)
    
    try:
        api = tradeapi.REST(
            Config.ALPACA_KEY,
            Config.ALPACA_SECRET,
            Config.ALPACA_BASE_URL,
            api_version='v2'
        )
        
        positions = api.list_positions()
        print(f"Open positions: {len(positions)}")
        
        if len(positions) > 0:
            for pos in positions:
                print(f"  {pos.symbol}: {pos.qty} shares, side={pos.side}, market_value=${float(pos.market_value):.2f}")
        else:
            print("  ⚠️  NO OPEN POSITIONS")
        
        # Check orders
        orders = api.list_orders(status='all', limit=10)
        print(f"\nRecent orders: {len(orders)}")
        for o in orders[:5]:
            print(f"  {o.symbol}: {o.side} {o.qty} @ {o.status}")
        
        return len(positions)
        
    except Exception as e:
        print(f"ERROR checking Alpaca: {e}")
        import traceback
        traceback.print_exc()
        return -1

def check_recent_scores():
    """Check recent composite scores"""
    print("\n" + "=" * 80)
    print("RECENT COMPOSITE SCORES")
    print("=" * 80)
    
    attr_path = Path("data/uw_attribution.jsonl")
    if not attr_path.exists():
        print("  ⚠️  No attribution file found")
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
        print("  ⚠️  No attribution records")
        return
    
    recent = records[-30:]
    print(f"Total records: {len(records)}")
    print(f"Recent (last 30):")
    
    signals = [r for r in recent if r.get("decision") == "signal"]
    rejected = [r for r in recent if r.get("decision") == "rejected"]
    
    print(f"  Signals: {len(signals)}")
    print(f"  Rejected: {len(rejected)}")
    
    if recent:
        scores = [r.get("score", 0.0) for r in recent]
        print(f"\nScore statistics:")
        print(f"  Min: {min(scores):.2f}")
        print(f"  Max: {max(scores):.2f}")
        print(f"  Avg: {sum(scores)/len(scores):.2f}")
        print(f"  >= 2.7: {len([s for s in scores if s >= 2.7])}/{len(scores)}")
        print(f"  >= 3.5: {len([s for s in scores if s >= 3.5])}/{len(scores)}")
        
        print(f"\nRecent records (last 10):")
        for r in recent[-10:]:
            symbol = r.get("symbol", "UNKNOWN")
            score = r.get("score", 0.0)
            decision = r.get("decision", "unknown")
            threshold = r.get("threshold", 2.7)
            print(f"  {symbol}: score={score:.2f}, decision={decision}, threshold={threshold:.2f}")

if __name__ == "__main__":
    check_alpaca_positions()
    check_recent_scores()
