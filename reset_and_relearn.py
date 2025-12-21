#!/usr/bin/env python3
"""
Reset Learning State and Relearn with Fixed Component Names

This script:
1. Resets the component performance tracking (clears old data with wrong names)
2. Runs full historical backfill with new component name normalization
3. Updates weights based on correctly normalized data

Use this after fixing component name mapping to ensure all historical data
is reprocessed with the correct component names.
"""

import json
from pathlib import Path
from adaptive_signal_optimizer import get_optimizer
from comprehensive_learning_orchestrator_v2 import run_historical_backfill, load_learning_state, save_learning_state

def reset_component_performance():
    """Reset component performance tracking to start fresh"""
    optimizer = get_optimizer()
    if not optimizer:
        print("❌ Optimizer not available")
        return False
    
    learner = optimizer.learner
    
    # Reset all component performance data
    from adaptive_signal_optimizer import SIGNAL_COMPONENTS
    for component in SIGNAL_COMPONENTS:
        if component in learner.component_performance:
            perf = learner.component_performance[component]
            perf["wins"] = 0
            perf["losses"] = 0
            perf["total_pnl"] = 0.0
            perf["ewma_win_rate"] = 0.5
            perf["ewma_pnl"] = 0.0
            perf["contribution_when_win"] = []
            perf["contribution_when_loss"] = []
            perf["sector_performance"] = {}
            perf["regime_performance"] = {}
    
    # Reset learning history
    learner.learning_history = []
    
    # Reset last weight update timestamp
    learner.last_weight_update_ts = None
    
    print("✓ Component performance data reset")
    return True

def reset_learning_state():
    """Reset learning state to reprocess all records"""
    state = load_learning_state()
    
    # Reset all last processed IDs
    state["last_attribution_id"] = None
    state["last_exit_id"] = None
    state["last_signal_id"] = None
    state["last_order_id"] = None
    state["last_blocked_trade_id"] = None
    state["last_gate_id"] = None
    state["last_uw_blocked_id"] = None
    
    # Reset totals (will be recalculated)
    state["total_trades_processed"] = 0
    state["total_trades_learned_from"] = 0
    state["total_exits_processed"] = 0
    state["total_signals_processed"] = 0
    state["total_orders_processed"] = 0
    state["total_blocked_trades_processed"] = 0
    state["total_gate_events_processed"] = 0
    state["total_uw_blocked_processed"] = 0
    
    save_learning_state(state)
    print("✓ Learning state reset (all records will be reprocessed)")

def main():
    print("=" * 80)
    print("RESET AND RELEARN WITH FIXED COMPONENT NAMES")
    print("=" * 80)
    print()
    print("This will:")
    print("  1. Reset component performance tracking (clear old data)")
    print("  2. Reset learning state (reprocess all records)")
    print("  3. Run full historical backfill with new normalization")
    print("  4. Update weights based on correctly normalized data")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() != "yes":
        print("Cancelled")
        return
    
    print()
    print("Step 1: Resetting component performance...")
    if not reset_component_performance():
        print("❌ Failed to reset component performance")
        return
    
    print()
    print("Step 2: Resetting learning state...")
    reset_learning_state()
    
    print()
    print("Step 3: Running full historical backfill with new normalization...")
    results = run_historical_backfill()
    
    print()
    print("=" * 80)
    print("RELEARNING COMPLETE")
    print("=" * 80)
    print()
    print("Results:")
    print(f"  Trades processed:        {results.get('attribution', 0):,}")
    print(f"  Exits processed:         {results.get('exits', 0):,}")
    print(f"  Signals processed:       {results.get('signals', 0):,}")
    print(f"  Orders processed:        {results.get('orders', 0):,}")
    print(f"  Weights updated:          {results.get('weights_updated', 0)}")
    print()
    print("✅ All historical data reprocessed with correct component names")
    print("✅ Component performance tracking reset and rebuilt")
    print("✅ Weights updated based on correctly normalized data")
    print()

if __name__ == "__main__":
    main()
