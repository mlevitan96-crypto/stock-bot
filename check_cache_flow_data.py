#!/usr/bin/env python3
"""Check cache for flow data"""
import json
from pathlib import Path

cache = json.load(open('data/uw_flow_cache.json'))
syms = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'SPY', 'QQQ', 'META', 'GOOGL']

print('Flow Data Check:')
for s in syms:
    if s in cache:
        d = cache[s]
        print(f'{s}: has_sentiment={bool(d.get("sentiment"))}, has_conviction={bool(d.get("conviction"))}, sentiment={d.get("sentiment", "MISSING")}, conviction={d.get("conviction", 0):.3f}, has_flow_trades={bool(d.get("flow_trades"))}, flow_trades_count={len(d.get("flow_trades", []))}')
