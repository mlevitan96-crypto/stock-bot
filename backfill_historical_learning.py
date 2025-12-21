#!/usr/bin/env python3
"""
Backfill Historical Learning Data

Run this once to process ALL historical trades and events for learning.
This will feed all past data into the learning system.

Usage:
    python3 backfill_historical_learning.py
"""

from comprehensive_learning_orchestrator_v2 import run_historical_backfill
import json

print("=" * 80)
print("HISTORICAL LEARNING BACKFILL")
print("=" * 80)
print()
print("This will process ALL historical data:")
print("  - All trades from logs/attribution.jsonl")
print("  - All exit events from logs/exit.jsonl")
print("  - All signal events from logs/signals.jsonl")
print("  - All order events from logs/orders.jsonl")
print()
print("This may take a few minutes depending on data volume...")
print()

try:
    results = run_historical_backfill()
    
    print()
    print("=" * 80)
    print("BACKFILL COMPLETE")
    print("=" * 80)
    print()
    print(f"Trades processed: {results.get('attribution', 0)}")
    print(f"Exits processed: {results.get('exits', 0)}")
    print(f"Signals processed: {results.get('signals', 0)}")
    print(f"Orders processed: {results.get('orders', 0)}")
    print(f"Weights updated: {results.get('weights_updated', 0)}")
    print()
    print("All historical data has been processed for learning!")
    print("The learning system will now continue with incremental updates.")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
