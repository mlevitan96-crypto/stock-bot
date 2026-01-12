#!/usr/bin/env python3
"""Get positions directly from Alpaca API"""
import os
import sys
from pathlib import Path

# Try to load .env manually
env_file = Path(".env")
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"').strip("'")

# Try to import alpaca
try:
    import alpaca_trade_api as api
except ImportError:
    print("ERROR: alpaca_trade_api not installed")
    sys.exit(1)

# Get credentials from environment (try multiple naming conventions)
api_key = os.getenv('ALPACA_KEY') or os.getenv('APCA_API_KEY_ID')
api_secret = os.getenv('ALPACA_SECRET') or os.getenv('APCA_API_SECRET_KEY')
api_url = os.getenv('ALPACA_BASE_URL') or os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets')

# If not in env, try to load from main.py Config
if not api_key or not api_secret:
    try:
        sys.path.insert(0, '.')
        from main import Config
        api_key = api_key or getattr(Config, 'ALPACA_KEY', None)
        api_secret = api_secret or getattr(Config, 'ALPACA_SECRET', None)
        api_url = api_url or getattr(Config, 'ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    except Exception as e:
        print(f"ERROR: Could not get credentials: {e}")
        sys.exit(1)

if not api_key or not api_secret:
    print("ERROR: Could not find Alpaca API credentials")
    print(f"ALPACA_KEY exists: {bool(os.getenv('ALPACA_KEY'))}")
    print(f"APCA_API_KEY_ID exists: {bool(os.getenv('APCA_API_KEY_ID'))}")
    sys.exit(1)

# Create API client
a = api.REST(api_key, api_secret, api_url)

# Get positions
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
    print(f"ERROR getting positions: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
