#!/usr/bin/env python3
"""
Diagnose why only 1 position is open
Checks all gates and limits that could prevent new positions
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

def check_positions():
    """Check current positions"""
    print("=" * 80)
    print("CURRENT POSITIONS")
    print("=" * 80)
    
    try:
        from alpaca.tradeapi import REST
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        api = REST(
            os.getenv("ALPACA_KEY"),
            os.getenv("ALPACA_SECRET"),
            os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
            api_version='v2'
        )
        
        positions = api.list_positions()
        print(f"\nCurrent positions: {len(positions)}")
        print(f"Max allowed: 16\n")
        
        if positions:
            for pos in positions:
                symbol = getattr(pos, 'symbol', 'UNKNOWN')
                qty = getattr(pos, 'qty', 0)
                entry_price = getattr(pos, 'avg_entry_price', 0)
                current_price = getattr(pos, 'current_price', 0)
                pnl = getattr(pos, 'unrealized_pl', 0)
                print(f"  {symbol}: {qty} shares @ ${entry_price:.2f} (current: ${current_price:.2f}, P&L: ${pnl:.2f})")
        else:
            print("  No positions open")
            
        return len(positions)
    except Exception as e:
        print(f"  Error checking positions: {e}")
        return 0

def check_recent_signals():
    """Check recent signals and why they were rejected"""
    print("\n" + "=" * 80)
    print("RECENT SIGNALS ANALYSIS")
    print("=" * 80)
    
    # Check signals.jsonl
    signals_file = Path("logs/signals.jsonl")
    if not signals_file.exists():
        print("\n❌ signals.jsonl not found")
        return
    
    recent_signals = []
    cutoff = time.time() - 3600  # Last hour
    
    with open(signals_file, 'r') as f:
        for line in f:
            try:
                sig = json.loads(line)
                ts = sig.get("ts", 0)
                if ts > cutoff:
                    recent_signals.append(sig)
            except:
                pass
    
    print(f"\nSignals in last hour: {len(recent_signals)}")
    
    if recent_signals:
        scores = [s.get("score", 0) for s in recent_signals]
        print(f"  Score range: {min(scores):.2f} - {max(scores):.2f}")
        print(f"  Avg score: {sum(scores)/len(scores):.2f}")
        print(f"  Signals >= 3.5: {sum(1 for s in scores if s >= 3.5)}")
        print(f"  Signals >= 3.0: {sum(1 for s in scores if s >= 3.0)}")
        print(f"  Signals >= 2.5: {sum(1 for s in scores if s >= 2.5)}")

def check_blocked_trades():
    """Check why trades were blocked"""
    print("\n" + "=" * 80)
    print("BLOCKED TRADES ANALYSIS (Last Hour)")
    print("=" * 80)
    
    blocked_file = Path("state/blocked_trades.jsonl")
    if not blocked_file.exists():
        print("\n❌ blocked_trades.jsonl not found")
        return
    
    cutoff = time.time() - 3600
    blocked = []
    reasons = Counter()
    
    with open(blocked_file, 'r') as f:
        for line in f:
            try:
                rec = json.loads(line)
                ts = rec.get("ts", rec.get("_ts", 0))
                if ts > cutoff:
                    blocked.append(rec)
                    reason = rec.get("reason", "unknown")
                    reasons[reason] += 1
            except:
                pass
    
    print(f"\nBlocked trades in last hour: {len(blocked)}")
    print("\nBlock reasons:")
    for reason, count in reasons.most_common():
        print(f"  {reason}: {count}")

def check_gate_events():
    """Check gate events"""
    print("\n" + "=" * 80)
    print("GATE EVENTS (Last Hour)")
    print("=" * 80)
    
    gate_file = Path("logs/gate.jsonl")
    if not gate_file.exists():
        print("\n❌ gate.jsonl not found")
        return
    
    cutoff = time.time() - 3600
    gate_events = []
    gate_types = Counter()
    
    with open(gate_file, 'r') as f:
        for line in f:
            try:
                rec = json.loads(line)
                ts = rec.get("ts", rec.get("_ts", 0))
                if ts > cutoff:
                    gate_events.append(rec)
                    gate_type = rec.get("gate_type", rec.get("type", "unknown"))
                    gate_types[gate_type] += 1
            except:
                pass
    
    print(f"\nGate events in last hour: {len(gate_events)}")
    print("\nGate types:")
    for gtype, count in gate_types.most_common():
        print(f"  {gtype}: {count}")

def check_clusters():
    """Check if clusters are being generated"""
    print("\n" + "=" * 80)
    print("CLUSTER GENERATION")
    print("=" * 80)
    
    # Check recent run logs
    run_file = Path("logs/run.jsonl")
    if not run_file.exists():
        print("\n❌ run.jsonl not found")
        return
    
    cutoff = time.time() - 3600
    recent_runs = []
    
    with open(run_file, 'r') as f:
        for line in f:
            try:
                rec = json.loads(line)
                ts = rec.get("ts", rec.get("_ts", 0))
                if ts > cutoff:
                    recent_runs.append(rec)
            except:
                pass
    
    print(f"\nRun cycles in last hour: {len(recent_runs)}")
    
    if recent_runs:
        clusters_counts = [r.get("clusters", 0) for r in recent_runs]
        orders_counts = [r.get("orders", 0) for r in recent_runs]
        
        print(f"  Clusters generated: {sum(clusters_counts)} (avg: {sum(clusters_counts)/len(clusters_counts):.1f})")
        print(f"  Orders placed: {sum(orders_counts)} (avg: {sum(orders_counts)/len(orders_counts):.1f})")
        
        if clusters_counts and max(clusters_counts) == 0:
            print("\n  ⚠️  WARNING: No clusters generated in recent cycles!")
            print("     This means signals are being rejected before clustering")

def check_threshold():
    """Check current threshold"""
    print("\n" + "=" * 80)
    print("THRESHOLD CHECK")
    print("=" * 80)
    
    try:
        from uw_composite_v2 import get_threshold, ENTRY_THRESHOLDS
        print(f"\nBase threshold: {ENTRY_THRESHOLDS.get('base', 'unknown')}")
        print(f"Canary threshold: {ENTRY_THRESHOLDS.get('canary', 'unknown')}")
        print(f"Champion threshold: {ENTRY_THRESHOLDS.get('champion', 'unknown')}")
        
        # Check a sample symbol
        sample_threshold = get_threshold("AAPL", "base")
        print(f"\nSample threshold for AAPL: {sample_threshold}")
    except Exception as e:
        print(f"\nError checking threshold: {e}")

def main():
    print("=" * 80)
    print("TRADING DIAGNOSTIC - Why Only 1 Position?")
    print("=" * 80)
    print(f"\nTime: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    positions = check_positions()
    check_recent_signals()
    check_blocked_trades()
    check_gate_events()
    check_clusters()
    check_threshold()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if positions < 16:
        print(f"\n✓ Position limit not reached ({positions}/16)")
        print("  Possible reasons for no new positions:")
        print("  1. All signals below threshold (3.5)")
        print("  2. Signals failing expectancy gate")
        print("  3. Signals failing other gates (toxicity, freshness, etc.)")
        print("  4. No clusters being generated")
        print("  5. Market closed or other conditions")
    else:
        print(f"\n⚠️  Position limit reached ({positions}/16)")
        print("  Bot cannot open new positions until some close")
    
    print("\nCheck the sections above for specific blocking reasons.")

if __name__ == "__main__":
    main()
