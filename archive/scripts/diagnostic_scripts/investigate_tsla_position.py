#!/usr/bin/env python3
"""
Investigate TSLA position to check entry_score and understand why it was entered.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from config.registry import StateFiles

def load_metadata_with_lock(path: Path) -> dict:
    """Load metadata (simplified for Windows compatibility)"""
    if not path.exists():
        return {}
    
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load metadata: {e}")
        return {}

def investigate_tsla_position():
    """Check TSLA position metadata and entry details."""
    
    print("=" * 80)
    print("TSLA POSITION INVESTIGATION")
    print("=" * 80)
    print()
    
    # Load position metadata
    metadata_path = StateFiles.POSITION_METADATA
    if not metadata_path.exists():
        print(f"[ERROR] Position metadata file not found: {metadata_path}")
        return
    
    try:
        metadata = load_metadata_with_lock(metadata_path)
    except Exception as e:
        print(f"[ERROR] Failed to load metadata: {e}")
        return
    
    # Check TSLA position
    tsla_meta = metadata.get("TSLA", {})
    
    if not tsla_meta:
        print("[ERROR] TSLA position not found in metadata")
        print(f"\nAll positions in metadata: {list(metadata.keys())}")
        return
    
    print("[OK] TSLA position found in metadata")
    print()
    print("Position Details:")
    print("-" * 80)
    
    entry_score = tsla_meta.get("entry_score", 0.0)
    entry_ts = tsla_meta.get("entry_ts", "unknown")
    entry_price = tsla_meta.get("entry_price", 0.0)
    qty = tsla_meta.get("qty", 0)
    side = tsla_meta.get("side", "unknown")
    direction = tsla_meta.get("direction", "unknown")
    market_regime = tsla_meta.get("market_regime", "unknown")
    components = tsla_meta.get("components", {})
    
    print(f"Entry Score: {entry_score}")
    if entry_score == 0.0:
        print("  [WARNING] Entry score is 0.00 - this is suspicious!")
    else:
        print(f"  [OK] Entry score is {entry_score:.2f}")
    
    print(f"Entry Timestamp: {entry_ts}")
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"Quantity: {qty}")
    print(f"Side: {side}")
    print(f"Direction: {direction}")
    print(f"Market Regime: {market_regime}")
    
    if components:
        print(f"\nSignal Components ({len(components)} components):")
        for comp, value in sorted(components.items(), key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0, reverse=True):
            if isinstance(value, (int, float)) and value != 0:
                print(f"  {comp}: {value:.4f}")
    
    # Check if entry_ts is recent
    try:
        if entry_ts and entry_ts != "unknown":
            entry_dt = datetime.fromisoformat(entry_ts.replace('Z', '+00:00'))
            now = datetime.now(entry_dt.tzinfo) if entry_dt.tzinfo else datetime.utcnow()
            age_hours = (now - entry_dt).total_seconds() / 3600
            print(f"\nPosition Age: {age_hours:.2f} hours")
    except Exception as e:
        print(f"\nCould not calculate position age: {e}")
    
    # Check logs for TSLA entry
    print("\n" + "=" * 80)
    print("Checking logs for TSLA entry...")
    print("=" * 80)
    
    from config.registry import LogFiles
    import os
    
    # Check orders log
    orders_log = LogFiles.ORDERS
    if orders_log.exists():
        print(f"\nRecent TSLA orders from {orders_log}:")
        with open(orders_log, 'r') as f:
            lines = f.readlines()
            tsla_orders = [json.loads(l) for l in lines[-50:] if 'TSLA' in l.upper()]
            if tsla_orders:
                for order in tsla_orders[-5:]:  # Last 5 TSLA orders
                    print(f"  {order.get('timestamp', 'unknown')}: {order.get('action', 'unknown')} - {order.get('symbol', 'unknown')}")
            else:
                print("  No recent TSLA orders found")
    
    # Check signals log
    signals_log = LogFiles.SIGNALS
    if signals_log.exists():
        print(f"\nRecent TSLA signals from {signals_log}:")
        with open(signals_log, 'r') as f:
            lines = f.readlines()
            tsla_signals = [json.loads(l) for l in lines[-50:] if 'TSLA' in l.upper()]
            if tsla_signals:
                for signal in tsla_signals[-3:]:  # Last 3 TSLA signals
                    score = signal.get('composite_score', signal.get('score', 'unknown'))
                    print(f"  Score: {score}, Direction: {signal.get('direction', 'unknown')}")
            else:
                print("  No recent TSLA signals found")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)
    
    if entry_score == 0.0:
        print("[CRITICAL] Entry score is 0.00")
        print("   This could indicate:")
        print("   1. A bug where score wasn't properly passed to mark_open()")
        print("   2. Position was entered via reconciliation loop without score")
        print("   3. Score was 0.0 when position was entered (should be blocked by gates)")
        print("\n   Action: Check decide_and_execute() logs around entry time")
    else:
        print(f"[OK] Entry score is {entry_score:.2f}")
        if entry_score < 2.0:
            print("   [WARNING] Low entry score - position may have been entered during bootstrap mode")
        elif entry_score < 2.5:
            print("   [WARNING] Entry score below typical minimum (2.5)")

if __name__ == "__main__":
    investigate_tsla_position()
