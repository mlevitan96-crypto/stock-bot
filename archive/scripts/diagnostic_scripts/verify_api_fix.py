#!/usr/bin/env python3
"""Verify Alpaca API fix"""
import sys
sys.path.insert(0, '.')
from historical_replay_engine import AlpacaHistoricalDataClient
from datetime import datetime, timedelta

print("Testing Alpaca Data API v2 fix...")
client = AlpacaHistoricalDataClient()

end = datetime.now()
start = end - timedelta(hours=1)
print(f"Fetching bars for AAPL from {start} to {end}...")

bars = client.get_historical_bars("AAPL", start, end, "1Min", 5)
print(f"Result: Got {len(bars)} bars")
if bars:
    print(f"SUCCESS! First bar: {bars[0]}")
else:
    print("FAILED: No bars returned")
