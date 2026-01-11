#!/usr/bin/env python3
"""Test Alpaca Data API v2 directly"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "APCA-API-KEY-ID": os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY", ""),
    "APCA-API-SECRET-KEY": os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET", "")
}

url = "https://data.alpaca.markets/v2/stocks/bars"
params = {
    "symbols": "AAPL",
    "timeframe": "1Min",
    "limit": 5
}

print(f"Testing Alpaca Data API v2...")
print(f"Key present: {bool(headers['APCA-API-KEY-ID'])}")
print(f"Secret present: {bool(headers['APCA-API-SECRET-KEY'])}")

try:
    r = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"\nStatus: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        bars = data.get("bars", {}).get("AAPL", [])
        print(f"Got {len(bars)} bars")
        if bars:
            print(f"Sample bar: {bars[0]}")
    else:
        print(f"Error: {r.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")
