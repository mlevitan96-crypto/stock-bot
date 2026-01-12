#!/usr/bin/env python3
"""Get positions using .env file directly"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_file = Path(".env")
if env_file.exists():
    load_dotenv(env_file)

# Get credentials
api_key = os.getenv('ALPACA_KEY') or os.getenv('APCA_API_KEY_ID')
api_secret = os.getenv('ALPACA_SECRET') or os.getenv('APCA_API_SECRET_KEY')
api_url = os.getenv('ALPACA_BASE_URL') or os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets')

if not api_key or not api_secret:
    print("ERROR: Could not find Alpaca credentials")
    exit(1)

import alpaca_trade_api as api
a = api.REST(api_key, api_secret, api_url)

print("=" * 80)
print("CURRENT POSITIONS FROM ALPACA API")
print("=" * 80)
print()

try:
    positions = a.list_positions()
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
