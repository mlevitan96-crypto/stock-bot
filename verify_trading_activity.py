#!/usr/bin/env python3
"""
Comprehensive verification of trading activity after high-velocity learning changes
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta

def check_bot_status():
    """Check if bot is running"""
    print("=" * 80)
    print("BOT STATUS CHECK")
    print("=" * 80)
    
    # Check systemd status
    import subprocess
    try:
        result = subprocess.run(['systemctl', 'is-active', 'trading-bot.service'], 
                               capture_output=True, text=True, timeout=5)
        status = result.stdout.strip()
        print(f"Systemd Status: {status}")
        return status == "active"
    except Exception as e:
        print(f"Error checking systemd: {e}")
        return False

def check_recent_positions():
    """Check current positions"""
    print("\n" + "=" * 80)
    print("CURRENT POSITIONS")
    print("=" * 80)
    
    positions_file = Path("state/positions.json")
    if positions_file.exists():
        with positions_file.open() as f:
            positions = json.load(f)
        print(f"Total positions: {len(positions)}")
        for symbol, info in positions.items():
            entry_price = info.get("entry_price", 0)
            qty = info.get("qty", 0)
            side = info.get("side", "unknown")
            entry_ts = info.get("entry_ts", 0)
            entry_time = datetime.fromtimestamp(entry_ts).strftime("%Y-%m-%d %H:%M:%S") if entry_ts else "unknown"
            print(f"  {symbol}: {side.upper()} {qty} @ ${entry_price:.2f} (entered {entry_time})")
        return len(positions)
    else:
        print("No positions file found")
        return 0

def check_recent_trades():
    """Check recent trades from attribution.jsonl"""
    print("\n" + "=" * 80)
    print("RECENT TRADES (Last 10)")
    print("=" * 80)
    
    attribution_file = Path("logs/attribution.jsonl")
    if not attribution_file.exists():
        attribution_file = Path("data/attribution.jsonl")
    
    if not attribution_file.exists():
        print("No attribution file found")
        return []
    
    trades = []
    try:
        with attribution_file.open() as f:
            lines = f.readlines()
            for line in reversed(lines[-20:]):  # Check last 20 lines
                try:
                    trade = json.loads(line.strip())
                    if trade.get("type") == "attribution":
                        trades.append(trade)
                except:
                    continue
    except Exception as e:
        print(f"Error reading attribution file: {e}")
        return []
    
    print(f"Total trades found: {len(trades)}")
    for trade in trades[:10]:  # Show last 10
        symbol = trade.get("symbol", "unknown")
        entry_ts = trade.get("entry_ts", 0)
        exit_ts = trade.get("exit_ts", 0)
        pnl_pct = trade.get("pnl_pct", 0) or trade.get("context", {}).get("pnl_pct", 0)
        entry_time = datetime.fromtimestamp(entry_ts).strftime("%Y-%m-%d %H:%M:%S") if entry_ts else "unknown"
        exit_time = datetime.fromtimestamp(exit_ts).strftime("%Y-%m-%d %H:%M:%S") if exit_ts else "open"
        print(f"  {symbol}: Entry {entry_time}, Exit {exit_time}, P&L {pnl_pct:.2f}%")
    
    return trades

def check_scoring_activity():
    """Check recent scoring activity"""
    print("\n" + "=" * 80)
    print("RECENT SCORING ACTIVITY")
    print("=" * 80)
    
    # Check main.log for recent scores
    log_file = Path("logs/main.log")
    if not log_file.exists():
        print("No main.log found")
        return
    
    try:
        with log_file.open() as f:
            lines = f.readlines()
            # Look for composite_score entries in last 100 lines
            score_entries = []
            for line in reversed(lines[-100:]):
                if "composite_score" in line.lower() or "score:" in line.lower():
                    score_entries.append(line.strip())
            
            print(f"Found {len(score_entries)} score entries in last 100 log lines")
            for entry in score_entries[:10]:  # Show last 10
                print(f"  {entry[:150]}...")  # Truncate long lines
    except Exception as e:
        print(f"Error reading log file: {e}")

def check_threshold_state():
    """Check self-healing threshold state"""
    print("\n" + "=" * 80)
    print("SELF-HEALING THRESHOLD STATE")
    print("=" * 80)
    
    threshold_file = Path("state/self_healing_threshold.json")
    if threshold_file.exists():
        with threshold_file.open() as f:
            state = json.load(f)
        adjustment = state.get("adjustment", 0.0)
        activated = state.get("is_activated", False) or adjustment > 0
        consecutive_losses = state.get("consecutive_losses", 0)
        activated_at = state.get("activated_at")
        
        if activated_at:
            activated_time = datetime.fromtimestamp(activated_at).strftime("%Y-%m-%d %H:%M:%S")
            hours_since = (time.time() - activated_at) / 3600
        else:
            activated_time = "N/A"
            hours_since = 0
        
        print(f"Adjustment: +{adjustment:.2f}")
        print(f"Activated: {activated}")
        print(f"Consecutive Losses: {consecutive_losses}")
        print(f"Activated At: {activated_time} ({hours_since:.1f} hours ago)")
        
        base_threshold = 2.0
        current_threshold = base_threshold + adjustment
        print(f"Current Threshold: {current_threshold:.2f} (base {base_threshold:.2f} + adjustment {adjustment:.2f})")
        
        return current_threshold
    else:
        print("No threshold state file - using base threshold 2.0")
        return 2.0

def check_adaptive_weights():
    """Check current adaptive weights"""
    print("\n" + "=" * 80)
    print("ADAPTIVE WEIGHTS STATE")
    print("=" * 80)
    
    weights_file = Path("state/signal_weights.json")
    if weights_file.exists():
        with weights_file.open() as f:
            state = json.load(f)
        
        weight_bands = state.get("weight_bands", {})
        print(f"Total components: {len(weight_bands)}")
        
        # Show components with non-1.0 multipliers
        non_default = []
        for component, band in weight_bands.items():
            if isinstance(band, dict):
                mult = band.get("current", 1.0)
                if mult != 1.0:
                    non_default.append((component, mult))
        
        if non_default:
            print(f"\nComponents with non-default multipliers ({len(non_default)}):")
            for component, mult in sorted(non_default, key=lambda x: abs(x[1] - 1.0), reverse=True)[:10]:
                print(f"  {component:25} = {mult:6.3f}")
        else:
            print("\nAll multipliers at default (1.0) - weights reset successful")
        
        return weight_bands
    else:
        print("No weights file found")
        return {}

def check_uw_cache():
    """Check UW cache status"""
    print("\n" + "=" * 80)
    print("UW CACHE STATUS")
    print("=" * 80)
    
    cache_file = Path("data/uw_flow_cache.json")
    if cache_file.exists():
        with cache_file.open() as f:
            cache = json.load(f)
        
        symbols = [k for k in cache.keys() if k != "_metadata"]
        print(f"Symbols in cache: {len(symbols)}")
        
        if symbols:
            print(f"Sample symbols: {', '.join(symbols[:10])}")
            
            # Check one symbol's data
            sample = symbols[0]
            sample_data = cache.get(sample, {})
            print(f"\nSample data for {sample}:")
            for key in ["sentiment", "conviction", "dark_pool", "greeks", "oi_change"]:
                if key in sample_data:
                    print(f"  {key}: present")
                else:
                    print(f"  {key}: missing")
    else:
        print("Cache file not found")

def check_recent_blocked_trades():
    """Check recent blocked trades"""
    print("\n" + "=" * 80)
    print("RECENT BLOCKED TRADES")
    print("=" * 80)
    
    blocked_file = Path("state/blocked_trades.jsonl")
    if not blocked_file.exists():
        print("No blocked trades file found")
        return []
    
    blocked = []
    try:
        with blocked_file.open() as f:
            lines = f.readlines()
            for line in reversed(lines[-20:]):  # Last 20
                try:
                    entry = json.loads(line.strip())
                    blocked.append(entry)
                except:
                    continue
    except Exception as e:
        print(f"Error reading blocked trades: {e}")
        return []
    
    print(f"Total blocked trades found: {len(blocked)}")
    
    # Group by reason
    reasons = {}
    for entry in blocked:
        reason = entry.get("reason", "unknown")
        reasons[reason] = reasons.get(reason, 0) + 1
    
    print("\nBlocked by reason:")
    for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
        print(f"  {reason}: {count}")
    
    return blocked

def main():
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TRADING ACTIVITY VERIFICATION")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Bot status
    is_running = check_bot_status()
    
    # 2. Current positions
    num_positions = check_recent_positions()
    
    # 3. Recent trades
    recent_trades = check_recent_trades()
    
    # 4. Scoring activity
    check_scoring_activity()
    
    # 5. Threshold state
    current_threshold = check_threshold_state()
    
    # 6. Adaptive weights
    weights = check_adaptive_weights()
    
    # 7. UW cache
    check_uw_cache()
    
    # 8. Blocked trades
    blocked = check_recent_blocked_trades()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Bot Running: {'YES' if is_running else 'NO'}")
    print(f"Current Positions: {num_positions}")
    print(f"Recent Trades (last 20): {len(recent_trades)}")
    print(f"Current Threshold: {current_threshold:.2f}")
    print(f"Blocked Trades (last 20): {len(blocked)}")
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    if not is_running:
        print("[WARN] BOT IS NOT RUNNING - This is the primary issue!")
    elif num_positions < 3:
        print(f"[WARN] LOW POSITION COUNT - Only {num_positions} positions active")
        print("   Possible causes:")
        print("   1. Threshold too high (current: {:.2f})".format(current_threshold))
        print("   2. Not enough signals meeting threshold")
        print("   3. Max positions limit reached")
        print("   4. Market conditions not favorable")
    else:
        print("✅ Position count looks normal")
    
    if current_threshold > 2.5:
        print(f"[WARN] THRESHOLD RAISED - Current threshold {current_threshold:.2f} may be blocking trades")
        print("   Self-healing threshold activated due to recent losses")
    
    if len(blocked) > 10:
        print(f"[WARN] MANY BLOCKED TRADES - {len(blocked)} trades blocked recently")
        print("   Review blocked trade reasons above")

if __name__ == "__main__":
    main()

