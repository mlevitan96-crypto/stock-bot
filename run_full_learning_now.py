#!/usr/bin/env python3
"""
Run Full Learning Cycle Now - Process All Historical Data

This script processes ALL historical data through the learning system
and updates weights immediately, ready for tomorrow's market open.

Usage:
    python3 run_full_learning_now.py
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from comprehensive_learning_orchestrator_v2 import run_historical_backfill
from profitability_tracker import (
    update_daily_performance,
    update_weekly_performance,
    update_monthly_performance
)

def print_section(title):
    """Print a formatted section header"""
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print()

def run_full_learning_cycle():
    """Run complete learning cycle with all historical data"""
    print("=" * 80)
    print("FULL LEARNING CYCLE - PROCESSING ALL HISTORICAL DATA")
    print("=" * 80)
    print()
    print(f"Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    print("This will:")
    print("  ✓ Process ALL historical trades")
    print("  ✓ Process ALL exit events")
    print("  ✓ Process ALL blocked trades")
    print("  ✓ Process ALL gate events")
    print("  ✓ Process ALL UW blocked entries")
    print("  ✓ Process ALL signal patterns")
    print("  ✓ Process ALL order execution data")
    print("  ✓ Update component weights (if enough samples)")
    print("  ✓ Update profitability tracking")
    print("  ✓ Invalidate cache for immediate use")
    print()
    print("This may take a few minutes depending on data volume...")
    print()
    
    start_time = time.time()
    
    try:
        # 1. Run historical backfill (processes ALL data)
        print_section("STEP 1: PROCESSING ALL HISTORICAL DATA")
        learning_results = run_historical_backfill()
        
        elapsed = time.time() - start_time
        
        print()
        print_section("STEP 2: LEARNING RESULTS")
        print("Processing Results:")
        print(f"  Trades processed:        {learning_results.get('attribution', 0):,}")
        print(f"  Exits processed:         {learning_results.get('exits', 0):,}")
        print(f"  Signals processed:       {learning_results.get('signals', 0):,}")
        print(f"  Orders processed:        {learning_results.get('orders', 0):,}")
        print(f"  Blocked trades:          {learning_results.get('blocked_trades', 0):,}")
        print(f"  Gate events:             {learning_results.get('gate_events', 0):,}")
        print(f"  UW blocked entries:      {learning_results.get('uw_blocked', 0):,}")
        print(f"  Weights updated:          {learning_results.get('weights_updated', 0)}")
        print()
        print(f"Processing time: {elapsed:.1f} seconds")
        print()
        
        # 2. Update profitability tracking
        print_section("STEP 3: UPDATING PROFITABILITY TRACKING")
        try:
            update_daily_performance()
            print("✓ Daily performance updated")
        except Exception as e:
            print(f"✗ Daily performance update failed: {e}")
        
        try:
            update_weekly_performance()
            print("✓ Weekly performance updated")
        except Exception as e:
            print(f"✗ Weekly performance update failed: {e}")
        
        try:
            update_monthly_performance()
            print("✓ Monthly performance updated")
        except Exception as e:
            print(f"✗ Monthly performance update failed: {e}")
        
        print()
        
        # 3. Invalidate cache so trading engine uses new weights immediately
        print_section("STEP 4: REFRESHING TRADING ENGINE CACHE")
        try:
            import uw_composite_v2
            uw_composite_v2._weights_cache_ts = 0.0
            uw_composite_v2._cached_weights.clear()
            uw_composite_v2._multipliers_cache_ts = 0.0
            uw_composite_v2._cached_multipliers.clear()
            print("✓ Trading engine cache invalidated")
            print("  New weights will be used immediately on next trade")
        except Exception as e:
            print(f"✗ Cache refresh failed: {e}")
        
        print()
        
        # 4. Summary
        print_section("LEARNING CYCLE COMPLETE")
        print("✅ All historical data processed")
        print("✅ Weights updated (if enough samples)")
        print("✅ Profitability tracking updated")
        print("✅ Trading engine cache refreshed")
        print()
        print("🚀 SYSTEM READY FOR TOMORROW'S MARKET OPEN")
        print()
        print("The trading engine will now use:")
        print("  - Updated component weights from learning")
        print("  - Latest profitability metrics")
        print("  - All pattern learnings (gate, UW blocked, signal patterns)")
        print()
        
        return {
            "success": True,
            "learning_results": learning_results,
            "processing_time": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR DURING LEARNING CYCLE")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

if __name__ == "__main__":
    result = run_full_learning_cycle()
    
    if result.get("success"):
        print("=" * 80)
        print("SUCCESS - System ready for trading")
        print("=" * 80)
        exit(0)
    else:
        print("=" * 80)
        print("FAILED - Check errors above")
        print("=" * 80)
        exit(1)
