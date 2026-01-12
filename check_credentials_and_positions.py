#!/usr/bin/env python3
"""Check for credentials and get positions"""
import os
import sys
from pathlib import Path

# Try loading .env
env_file = Path(".env")
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)
    print(f"✅ Loaded .env file: {env_file}")
else:
    print(f"⚠️  No .env file found at {env_file.absolute()}")

# Check for credentials
api_key = os.getenv('ALPACA_KEY') or os.getenv('APCA_API_KEY_ID')
api_secret = os.getenv('ALPACA_SECRET') or os.getenv('APCA_API_SECRET_KEY')
api_url = os.getenv('ALPACA_BASE_URL') or os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets')

print(f"\nCredential Check:")
print(f"  ALPACA_KEY: {'✅ SET' if api_key else '❌ NOT SET'}")
print(f"  ALPACA_SECRET: {'✅ SET' if api_secret else '❌ NOT SET'}")
print(f"  ALPACA_BASE_URL: {api_url}")

if not api_key or not api_secret:
    print("\n❌ Cannot proceed without credentials")
    print("\nLooking for credentials in:")
    print(f"  1. Environment variables: ALPACA_KEY, ALPACA_SECRET")
    print(f"  2. .env file: {env_file.absolute()}")
    print(f"  3. Alternative names: APCA_API_KEY_ID, APCA_API_SECRET_KEY")
    sys.exit(1)

# Get positions
print("\n" + "=" * 80)
print("CURRENT POSITIONS FROM ALPACA API")
print("=" * 80)
print()

try:
    import alpaca_trade_api as api
    a = api.REST(api_key, api_secret, api_url)
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
    print(f"ERROR getting positions: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
