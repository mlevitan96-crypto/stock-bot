#!/usr/bin/env python3
"""
Trigger Learning Cycle Now

Processes ALL historical data through the learning system immediately,
including the new learning enhancements (gate patterns, UW blocked, signal patterns).

Usage:
    python3 trigger_learning_cycle_now.py
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from comprehensive_learning_orchestrator_v2 import run_historical_backfill, run_comprehensive_learning

def print_section(title):
    """Print a formatted section header"""
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print()

def check_data_files():
    """Check what data files exist"""
    log_dir = Path("logs")
    data_dir = Path("data")
    
    files = {
        "attribution": log_dir / "attribution.jsonl",
        "exits": log_dir / "exit.jsonl",
        "signals": log_dir / "signals.jsonl",
        "orders": log_dir / "orders.jsonl",
        "blocked_trades": Path("state") / "blocked_trades.jsonl",
        "gate": log_dir / "gate.jsonl",
        "uw_attribution": data_dir / "uw_attribution.jsonl"
    }
    
    print_section("DATA FILES CHECK")
    
    file_counts = {}
    for name, path in files.items():
        if path.exists():
            try:
                # Count lines
                with open(path, 'r', encoding='utf-8') as f:
                    count = sum(1 for line in f if line.strip())
                file_counts[name] = count
                print(f"✓ {name:20s}: {path} ({count:,} records)")
            except Exception as e:
                print(f"✗ {name:20s}: {path} (error reading: {e})")
                file_counts[name] = 0
        else:
            print(f"✗ {name:20s}: {path} (not found)")
            file_counts[name] = 0
    
    total_records = sum(file_counts.values())
    print()
    print(f"Total records available: {total_records:,}")
    print()
    
    return file_counts

def run_learning_cycle():
    """Run the full learning cycle"""
    print_section("RUNNING LEARNING CYCLE")
    
    print("Processing ALL historical data through learning system...")
    print("This includes:")
    print("  - Actual trades (attribution.jsonl)")
    print("  - Exit events (exit.jsonl)")
    print("  - Blocked trades (blocked_trades.jsonl)")
    print("  - Gate events (gate.jsonl) ← NEW: Gate Pattern Learning")
    print("  - UW blocked entries (uw_attribution.jsonl) ← NEW: UW Blocked Learning")
    print("  - Signal patterns (signals.jsonl) ← NEW: Signal Pattern Learning")
    print("  - Order execution (orders.jsonl)")
    print()
    print("This may take a few minutes depending on data volume...")
    print()
    
    start_time = time.time()
    
    try:
        # Run historical backfill (processes ALL data)
        results = run_historical_backfill()
        
        elapsed = time.time() - start_time
        
        print()
        print_section("LEARNING CYCLE COMPLETE")
        
        print("Processing Results:")
        print(f"  Trades processed:        {results.get('attribution', 0):,}")
        print(f"  Exits processed:         {results.get('exits', 0):,}")
        print(f"  Signals processed:       {results.get('signals', 0):,}")
        print(f"  Orders processed:        {results.get('orders', 0):,}")
        print(f"  Blocked trades:          {results.get('blocked_trades', 0):,}")
        print(f"  Gate events:             {results.get('gate_events', 0):,}")
        print(f"  UW blocked entries:      {results.get('uw_blocked', 0):,}")
        print(f"  Weights updated:         {results.get('weights_updated', 0)}")
        print()
        print(f"Processing time: {elapsed:.1f} seconds")
        print()
        
        return results
        
    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR DURING LEARNING CYCLE")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_enhancement_state():
    """Check if enhancement state files were created"""
    print_section("LEARNING ENHANCEMENTS STATUS")
    
    state_dir = Path("state")
    enhancement_files = {
        "Gate Pattern Learning": state_dir / "gate_pattern_learning.json",
        "UW Blocked Learning": state_dir / "uw_blocked_learning.json",
        "Signal Pattern Learning": state_dir / "signal_pattern_learning.json"
    }
    
    for name, path in enhancement_files.items():
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if name == "Gate Pattern Learning":
                    patterns = data.get("patterns", {})
                    total_blocks = sum(p.get("blocks", 0) for p in patterns.values())
                    print(f"✓ {name}: {len(patterns)} gates tracked, {total_blocks:,} blocks analyzed")
                
                elif name == "UW Blocked Learning":
                    patterns = data.get("patterns", {})
                    total_blocked = sum(p.get("blocked_count", 0) for p in patterns.values())
                    print(f"✓ {name}: {len(patterns)} symbols tracked, {total_blocked:,} blocked entries analyzed")
                
                elif name == "Signal Pattern Learning":
                    patterns = data.get("patterns", {})
                    total_signals = sum(p.get("signal_count", 0) for p in patterns.values())
                    total_trades = sum(p.get("trades_resulting", 0) for p in patterns.values())
                    print(f"✓ {name}: {len(patterns)} symbols tracked, {total_signals:,} signals, {total_trades:,} trades correlated")
                
            except Exception as e:
                print(f"✗ {name}: Error reading state - {e}")
        else:
            print(f"✗ {name}: State file not created yet (may need data)")

def main():
    """Main execution"""
    print("=" * 80)
    print("TRIGGER LEARNING CYCLE NOW")
    print("=" * 80)
    print()
    print(f"Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Check data files
    file_counts = check_data_files()
    
    # Check if there's any data
    total_records = sum(file_counts.values())
    if total_records == 0:
        print()
        print("WARNING: No data files found. Learning cycle will have nothing to process.")
        print("Make sure log files exist in logs/ and data/ directories.")
        return
    
    # Run learning cycle
    results = run_learning_cycle()
    
    if results:
        # Check enhancement state
        check_enhancement_state()
        
        print()
        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print()
        print("✓ Learning cycle complete!")
        print()
        print("To check status:")
        print("  python3 check_learning_enhancements.py")
        print("  python3 check_comprehensive_learning_status.py")
        print()
        print("The learning system will now continue with incremental updates")
        print("on the next daily learning cycle.")
        print()
    else:
        print()
        print("Learning cycle failed. Check errors above.")
        exit(1)

if __name__ == "__main__":
    main()
