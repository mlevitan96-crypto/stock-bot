#!/usr/bin/env python3
"""
Reset Learning Processing State

Use this if you want to re-process all records from scratch.
This will reset the last processed IDs so all records are processed again.

WARNING: This will cause all records to be re-processed on next run.
"""

import json
from pathlib import Path

STATE_DIR = Path("state")
LEARNING_STATE_FILE = STATE_DIR / "learning_processing_state.json"

if LEARNING_STATE_FILE.exists():
    with open(LEARNING_STATE_FILE, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    print("Current state:")
    print(f"  Last attribution ID: {state.get('last_attribution_id')}")
    print(f"  Last exit ID: {state.get('last_exit_id')}")
    print(f"  Total trades processed: {state.get('total_trades_processed', 0)}")
    print()
    
    response = input("Reset all last processed IDs? (yes/no): ")
    if response.lower() == "yes":
        # Reset last processed IDs and totals (for clean re-processing)
        state["last_attribution_id"] = None
        state["last_exit_id"] = None
        state["last_signal_id"] = None
        state["last_order_id"] = None
        state["last_blocked_trade_id"] = None
        state["last_gate_id"] = None
        state["last_uw_blocked_id"] = None
        # Reset totals for accurate counting after re-processing
        state["total_trades_processed"] = 0
        state["total_trades_learned_from"] = 0
        state["total_exits_processed"] = 0
        state["total_signals_processed"] = 0
        state["total_orders_processed"] = 0
        state["total_blocked_processed"] = 0
        state["total_gates_processed"] = 0
        state["total_uw_blocked_processed"] = 0
        
        with open(LEARNING_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        
        print("Learning state reset. All records will be re-processed on next run.")
    else:
        print("Reset cancelled.")
else:
    print("No learning state file found. Nothing to reset.")
