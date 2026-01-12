#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from main import Config
import alpaca_trade_api as api

a = api.REST(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
pos = a.list_positions()
print(f"Positions: {len(pos)}")
goog_count = 0
total_pl = 0.0
goog_pl = 0.0
for p in pos:
    pl = float(p.unrealized_pl)
    total_pl += pl
    if 'GOOG' in p.symbol:
        goog_count += 1
        goog_pl += pl
    print(f"{p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f} | P/L: ${pl:.2f}")
print(f"\nTotal P/L: ${total_pl:.2f}")
print(f"GOOG positions: {goog_count}/{len(pos)}")
print(f"GOOG P/L: ${goog_pl:.2f}")
