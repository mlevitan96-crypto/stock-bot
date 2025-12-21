#!/usr/bin/env python3
"""
Process remaining unprocessed trades

This will process any trades that were skipped in the initial backfill
due to missing components or other issues.
"""

from comprehensive_learning_orchestrator_v2 import run_comprehensive_learning
import json
from pathlib import Path

print("=" * 80)
print("PROCESSING REMAINING TRADES")
print("=" * 80)
print()

# Check current state
state_file = Path("state/learning_processing_state.json")
if state_file.exists():
    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        print(f"Current state:")
        print(f"  Trades processed: {state.get('total_trades_processed', 0)}")
        print(f"  Trades learned from: {state.get('total_trades_learned_from', 0)}")
        print()

# Check total trades
attr_log = Path("logs/attribution.jsonl")
if attr_log.exists():
    with open(attr_log, 'r', encoding='utf-8') as f:
        total_trades = len([l for l in f if l.strip()])
        print(f"Total trades in log: {total_trades}")
        print()

print("Processing remaining trades...")
print()

try:
    # Run with process_all=False to only process new/unprocessed records
    results = run_comprehensive_learning(process_all_historical=False)
    
    print()
    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print()
    print(f"Trades processed: {results.get('attribution', 0)}")
    print(f"Exits processed: {results.get('exits', 0)}")
    print(f"Signals processed: {results.get('signals', 0)}")
    print(f"Orders processed: {results.get('orders', 0)}")
    print(f"Weights updated: {results.get('weights_updated', 0)}")
    print()
    
    # Check final state
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
            print(f"Final state:")
            print(f"  Total trades processed: {state.get('total_trades_processed', 0)}")
            print(f"  Total trades learned from: {state.get('total_trades_learned_from', 0)}")
            print()
            
            if attr_log.exists():
                with open(attr_log, 'r', encoding='utf-8') as f:
                    total_trades = len([l for l in f if l.strip()])
                    processed = state.get('total_trades_processed', 0)
                    learned = state.get('total_trades_learned_from', 0)
                    print(f"Coverage:")
                    print(f"  {processed}/{total_trades} trades processed ({processed/total_trades*100:.1f}%)")
                    print(f"  {learned}/{total_trades} trades learned from ({learned/total_trades*100:.1f}%)")
                    print()
                    if processed < total_trades:
                        print(f"  Note: {total_trades - processed} trades not yet processed")
                        print(f"        (may be missing components or have parsing issues)")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
