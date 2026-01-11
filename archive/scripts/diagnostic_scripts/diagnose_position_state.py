#!/usr/bin/env python3
"""Diagnose position state discrepancy - compare Alpaca API vs bot metadata"""

import json
import os
from pathlib import Path
from alpaca_trade_api import REST
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("POSITION STATE DISCREPANCY DIAGNOSIS")
print("=" * 80)
print()

# 1. Get actual Alpaca positions
print("1. ACTUAL ALPACA POSITIONS (authoritative source)")
print("-" * 80)
try:
    api = REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), 
               os.getenv('ALPACA_BASE_URL'), api_version='v2')
    alpaca_positions = api.list_positions()
    alpaca_symbols = {p.symbol for p in alpaca_positions}
    print(f"Alpaca API reports: {len(alpaca_positions)} positions")
    for p in alpaca_positions:
        print(f"  - {p.symbol}: {p.qty} shares")
except Exception as e:
    print(f"ERROR querying Alpaca API: {e}")
    alpaca_symbols = set()
print()

# 2. Get bot's internal metadata
print("2. BOT'S INTERNAL STATE (position_metadata.json)")
print("-" * 80)
try:
    metadata_path = Path("state/position_metadata.json")
    if metadata_path.exists():
        with metadata_path.open() as f:
            metadata = json.load(f)
        bot_positions = {k: v for k, v in metadata.items() if not k.startswith('_')}
        bot_symbols = set(bot_positions.keys())
        print(f"Bot metadata reports: {len(bot_positions)} positions")
        for symbol in bot_symbols:
            print(f"  - {symbol}")
        print(f"Metadata file last modified: {metadata_path.stat().st_mtime}")
    else:
        print("ERROR: position_metadata.json does not exist")
        bot_symbols = set()
except Exception as e:
    print(f"ERROR reading metadata: {e}")
    bot_symbols = set()
print()

# 3. Compare
print("3. COMPARISON")
print("-" * 80)
only_in_bot = bot_symbols - alpaca_symbols
only_in_alpaca = alpaca_symbols - bot_symbols
common = bot_symbols & alpaca_symbols

print(f"Common positions: {len(common)} - {list(common) if common else 'none'}")
print(f"Only in bot metadata (STALE): {len(only_in_bot)} - {list(only_in_bot) if only_in_bot else 'none'}")
print(f"Only in Alpaca (MISSING from bot): {len(only_in_alpaca)} - {list(only_in_alpaca) if only_in_alpaca else 'none'}")
print()

if only_in_bot:
    print("*** CRITICAL DISCREPANCY DETECTED ***")
    print(f"Bot thinks it has {len(only_in_bot)} positions that don't exist in Alpaca:")
    for symbol in only_in_bot:
        print(f"  - {symbol}")
    print("Bot's position_metadata.json is STALE and needs reconciliation")
print()

# 4. Check reconciliation status
print("4. RECONCILIATION STATUS")
print("-" * 80)
try:
    from main import RECONCILE_CHECK_INTERVAL_SEC, _last_reconcile_check_ts
    import time
    now = time.time()
    time_since_last = now - _last_reconcile_check_ts if '_last_reconcile_check_ts' in globals() else None
    if time_since_last is not None:
        print(f"Last reconciliation: {time_since_last:.1f} seconds ago")
        print(f"Throttle interval: {RECONCILE_CHECK_INTERVAL_SEC} seconds")
        if time_since_last < RECONCILE_CHECK_INTERVAL_SEC:
            print(f"Status: THROTTLED (next check in {RECONCILE_CHECK_INTERVAL_SEC - time_since_last:.1f} seconds)")
        else:
            print("Status: Should run on next cycle")
    else:
        print("Could not determine reconciliation status")
except Exception as e:
    print(f"Could not check reconciliation status: {e}")
print()

print("=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
