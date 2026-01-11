#!/usr/bin/env python3
"""Test Alpaca Data API v2 access"""
from dotenv import load_dotenv
load_dotenv()

from historical_replay_engine import AlpacaHistoricalDataClient
from datetime import datetime, timedelta

client = AlpacaHistoricalDataClient()
print(f"API Key present: {bool(client.api_key)}")
print(f"API Secret present: {bool(client.api_secret)}")

# Test fetching bars for AAPL (last hour)
end = datetime.now()
start = end - timedelta(hours=1)

print(f"\nFetching bars for AAPL from {start} to {end}...")
bars = client.get_historical_bars("AAPL", start, end, "1Min", 10)

print(f"Got {len(bars)} bars")
if bars:
    print(f"Sample bar: {bars[0]}")
else:
    print("No bars returned")
