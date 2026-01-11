#!/bin/bash
# Test Alpaca API fix
cd ~/stock-bot
python3 << 'EOF'
import sys
import os
sys.path.insert(0, '.')
from config.registry import get_env

# Test credential loading
key = get_env("ALPACA_KEY") or get_env("ALPACA_API_KEY", "")
secret = get_env("ALPACA_SECRET") or get_env("ALPACA_API_SECRET", "")
print(f"Key loaded: {bool(key)}")
print(f"Secret loaded: {bool(secret)}")

# Test API call
import requests
from datetime import datetime, timedelta

headers = {
    "APCA-API-KEY-ID": key,
    "APCA-API-SECRET-KEY": secret
}

url = "https://data.alpaca.markets/v2/stocks/bars"
end = datetime.now()
start = end - timedelta(hours=1)

params = {
    "symbols": "AAPL",
    "timeframe": "1Min",
    "start": start.strftime("%Y-%m-%dT%H:%M:%S-00:00"),
    "end": end.strftime("%Y-%m-%dT%H:%M:%S-00:00"),
    "limit": 5,
    "adjustment": "raw",
    "feed": "sip",
    "sort": "asc"
}

print(f"\nTesting API call...")
print(f"URL: {url}")
print(f"Params: {params}")

try:
    r = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"\nStatus: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        bars = data.get("bars", {}).get("AAPL", [])
        print(f"SUCCESS: Got {len(bars)} bars")
        if bars:
            print(f"First bar: {bars[0]}")
    else:
        print(f"ERROR Response: {r.text[:500]}")
except Exception as e:
    print(f"EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
EOF
