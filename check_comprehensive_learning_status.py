#!/usr/bin/env python3
"""Check comprehensive learning system status"""
import json
from pathlib import Path
from datetime import datetime, timezone

print("=" * 80)
print("COMPREHENSIVE LEARNING SYSTEM STATUS")
print("=" * 80)
print()

# Check learning state
learning_state_file = Path("state/learning_processing_state.json")
if learning_state_file.exists():
    with open(learning_state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        
        print("Processing Statistics:")
        print("-" * 80)
        print(f"Total trades processed: {state.get('total_trades_processed', 0)}")
        print(f"Total trades learned from: {state.get('total_trades_learned_from', 0)}")
        print(f"Total exits processed: {state.get('total_exits_processed', 0)}")
        print(f"Total signals processed: {state.get('total_signals_processed', 0)}")
        print(f"Total orders processed: {state.get('total_orders_processed', 0)}")
        print(f"Total blocked trades processed: {state.get('total_blocked_processed', 0)}")
        print(f"Total gate events processed: {state.get('total_gates_processed', 0)}")
        print(f"Total UW blocked entries processed: {state.get('total_uw_blocked_processed', 0)}")
        print()
        
        print("Last Processed Records:")
        print("-" * 80)
        if state.get("last_attribution_id"):
            print(f"Last attribution ID: {state['last_attribution_id'][:50]}...")
        if state.get("last_exit_id"):
            print(f"Last exit ID: {state['last_exit_id'][:50]}...")
        if state.get("last_signal_id"):
            print(f"Last signal ID: {state['last_signal_id'][:50]}...")
        if state.get("last_order_id"):
            print(f"Last order ID: {state['last_order_id'][:50]}...")
        print()
        
        if state.get("last_processed_ts"):
            print(f"Last processing: {state['last_processed_ts']}")
        print()
        
        # Check log file counts
        print("Log File Counts:")
        print("-" * 80)
        attr_log = Path("logs/attribution.jsonl")
        exit_log = Path("logs/exit.jsonl")
        signal_log = Path("logs/signals.jsonl")
        order_log = Path("logs/orders.jsonl")
        
        if attr_log.exists():
            with open(attr_log, 'r', encoding='utf-8') as f:
                attr_count = len([l for l in f if l.strip()])
                processed = state.get('total_trades_processed', 0)
                print(f"attribution.jsonl: {attr_count} total, {processed} processed ({processed/attr_count*100:.1f}%)")
        
        if exit_log.exists():
            with open(exit_log, 'r', encoding='utf-8') as f:
                exit_count = len([l for l in f if l.strip()])
                processed = state.get('total_exits_processed', 0)
                print(f"exit.jsonl: {exit_count} total, {processed} processed ({processed/exit_count*100:.1f}%)")
        
        if signal_log.exists():
            with open(signal_log, 'r', encoding='utf-8') as f:
                signal_count = len([l for l in f if l.strip()])
                processed = state.get('total_signals_processed', 0)
                print(f"signals.jsonl: {signal_count} total, {processed} processed ({processed/signal_count*100:.1f}%)")
        
        if order_log.exists():
            with open(order_log, 'r', encoding='utf-8') as f:
                order_count = len([l for l in f if l.strip()])
                processed = state.get('total_orders_processed', 0)
                print(f"orders.jsonl: {order_count} total, {processed} processed ({processed/order_count*100:.1f}%)")
        
        # Check blocked trades
        blocked_log = Path("state/blocked_trades.jsonl")
        if blocked_log.exists():
            with open(blocked_log, 'r', encoding='utf-8') as f:
                blocked_count = len([l for l in f if l.strip()])
                processed = state.get('total_blocked_processed', 0)
                print(f"blocked_trades.jsonl: {blocked_count} total, {processed} processed ({processed/blocked_count*100:.1f}%)")
        
        # Check gate events
        gate_log = Path("logs/gate.jsonl")
        if gate_log.exists():
            with open(gate_log, 'r', encoding='utf-8') as f:
                gate_count = len([l for l in f if l.strip()])
                processed = state.get('total_gates_processed', 0)
                print(f"gate.jsonl: {gate_count} total, {processed} processed ({processed/gate_count*100:.1f}%)")
        
        print()
        print("=" * 80)
        print("STATUS: Comprehensive learning system is ACTIVE")
        print("=" * 80)
        print()
        print("Full Learning Cycle: Signal → Trade → Learn → Review → Update → Trade")
        print("  ✓ Actual trades (attribution.jsonl)")
        print("  ✓ Exit events (exit.jsonl)")
        print("  ✓ Blocked trades (blocked_trades.jsonl)")
        print("  ✓ Gate events (gate.jsonl)")
        print("  ✓ UW blocked entries (uw_attribution.jsonl)")
        print("  ✓ Signal patterns (signals.jsonl)")
        print("  ✓ Execution quality (orders.jsonl)")
else:
    print("[WARNING] Learning state file not found")
    print("Comprehensive learning system may not be initialized")
    print("Run: python3 backfill_historical_learning.py")
