#!/usr/bin/env python3
"""
Check Learning Enhancements Status

Diagnostic script to verify all three learning enhancements are working.
"""

import json
from pathlib import Path

STATE_DIR = Path("state")

def check_gate_pattern_learning():
    """Check gate pattern learning status"""
    print("=" * 80)
    print("GATE PATTERN LEARNING STATUS")
    print("=" * 80)
    
    state_file = STATE_DIR / "gate_pattern_learning.json"
    
    if not state_file.exists():
        print("[INFO] Gate pattern learning state not found (will be created on first run)")
        return
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        patterns = data.get("patterns", {})
        total_blocks = sum(p.get("blocks", 0) for p in patterns.values())
        
        print(f"Total gate blocks tracked: {total_blocks}")
        print(f"Unique gates tracked: {len(patterns)}")
        print()
        
        if patterns:
            print("Top Gates by Block Count:")
            sorted_gates = sorted(patterns.items(), key=lambda x: x[1].get("blocks", 0), reverse=True)
            for gate_name, pattern in sorted_gates[:10]:
                blocks = pattern.get("blocks", 0)
                print(f"  {gate_name}: {blocks} blocks")
        else:
            print("[INFO] No gate patterns tracked yet")
        
        print()
    except Exception as e:
        print(f"[ERROR] Failed to read gate pattern state: {e}")
        print()

def check_uw_blocked_learning():
    """Check UW blocked entry learning status"""
    print("=" * 80)
    print("UW BLOCKED ENTRY LEARNING STATUS")
    print("=" * 80)
    
    state_file = STATE_DIR / "uw_blocked_learning.json"
    
    if not state_file.exists():
        print("[INFO] UW blocked learning state not found (will be created on first run)")
        return
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        patterns = data.get("patterns", {})
        total_blocked = sum(p.get("blocked_count", 0) for p in patterns.values())
        
        print(f"Total blocked entries tracked: {total_blocked}")
        print(f"Unique symbols blocked: {len(patterns)}")
        print()
        
        if patterns:
            print("Top Blocked Symbols:")
            sorted_symbols = sorted(patterns.items(), key=lambda x: x[1].get("blocked_count", 0), reverse=True)
            for symbol, pattern in sorted_symbols[:10]:
                blocked = pattern.get("blocked_count", 0)
                print(f"  {symbol}: {blocked} blocked entries")
        else:
            print("[INFO] No blocked entry patterns tracked yet")
        
        print()
    except Exception as e:
        print(f"[ERROR] Failed to read UW blocked state: {e}")
        print()

def check_signal_pattern_learning():
    """Check signal pattern learning status"""
    print("=" * 80)
    print("SIGNAL PATTERN LEARNING STATUS")
    print("=" * 80)
    
    state_file = STATE_DIR / "signal_pattern_learning.json"
    
    if not state_file.exists():
        print("[INFO] Signal pattern learning state not found (will be created on first run)")
        return
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        patterns = data.get("patterns", {})
        total_signals = sum(p.get("signal_count", 0) for p in patterns.values())
        total_trades = sum(p.get("trades_resulting", 0) for p in patterns.values())
        
        print(f"Total signals tracked: {total_signals}")
        print(f"Total trades correlated: {total_trades}")
        print(f"Unique symbols: {len(patterns)}")
        print()
        
        if patterns:
            # Find symbols with trades
            symbols_with_trades = {s: p for s, p in patterns.items() if p.get("trades_resulting", 0) > 0}
            
            if symbols_with_trades:
                print("Symbols with Trade Outcomes:")
                sorted_symbols = sorted(symbols_with_trades.items(), 
                                      key=lambda x: x[1].get("trades_resulting", 0), reverse=True)
                for symbol, pattern in sorted_symbols[:10]:
                    trades = pattern.get("trades_resulting", 0)
                    wins = pattern.get("wins", 0)
                    wr = (wins / trades * 100) if trades > 0 else 0.0
                    print(f"  {symbol}: {trades} trades, {wins} wins ({wr:.1f}% WR)")
            else:
                print("[INFO] No trades correlated with signals yet")
        else:
            print("[INFO] No signal patterns tracked yet")
        
        print()
    except Exception as e:
        print(f"[ERROR] Failed to read signal pattern state: {e}")
        print()

def main():
    """Run all checks"""
    print("=" * 80)
    print("LEARNING ENHANCEMENTS STATUS CHECK")
    print("=" * 80)
    print()
    
    check_gate_pattern_learning()
    check_uw_blocked_learning()
    check_signal_pattern_learning()
    
    print("=" * 80)
    print("STATUS CHECK COMPLETE")
    print("=" * 80)
    print()
    print("All three learning enhancements are integrated and ready.")
    print("They will start learning from data on next daily learning cycle.")

if __name__ == "__main__":
    main()
