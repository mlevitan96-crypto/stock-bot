#!/usr/bin/env python3
"""
Diagnose Why No Orders Are Being Placed

Checks:
1. Is the bot running?
2. Are signals being generated?
3. Are signals being blocked by gates?
4. Are max positions reached?
5. Is there a freeze active?
6. Are entry criteria too strict?
7. Is the market open?
8. Are there any errors in logs?
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
import subprocess

LOGS_DIR = Path("logs")
STATE_DIR = Path("state")
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"
GATE_LOG = LOGS_DIR / "gate.jsonl"
SIGNALS_LOG = LOGS_DIR / "signals.jsonl"
ORDERS_LOG = LOGS_DIR / "orders.jsonl"
BLOCKED_TRADES_LOG = STATE_DIR / "blocked_trades.jsonl"

def check_bot_running():
    """Check if bot processes are running"""
    print("="*80)
    print("1. BOT PROCESS CHECK")
    print("="*80)
    
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        processes = result.stdout
        
        bot_running = "main.py" in processes or "python.*main" in processes
        supervisor_running = "deploy_supervisor" in processes
        
        print(f"\nBot Process (main.py): {'✓ RUNNING' if bot_running else '❌ NOT RUNNING'}")
        print(f"Supervisor Process: {'✓ RUNNING' if supervisor_running else '❌ NOT RUNNING'}")
        
        if not bot_running:
            print("\n  ⚠️  CRITICAL: Bot is not running!")
            print("     Fix: Restart the bot with deploy_supervisor")
        
        return bot_running
    except Exception as e:
        print(f"\n⚠️  Could not check processes: {e}")
        return None

def check_recent_orders():
    """Check for recent orders in orders.jsonl"""
    print("\n" + "="*80)
    print("2. RECENT ORDERS CHECK")
    print("="*80)
    
    if not ORDERS_LOG.exists():
        print("\n❌ orders.jsonl does not exist")
        return []
    
    recent_orders = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    
    with ORDERS_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                order = json.loads(line)
                ts_str = order.get("ts") or order.get("timestamp") or order.get("_ts")
                if ts_str:
                    if isinstance(ts_str, (int, float)):
                        ts = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                    else:
                        try:
                            ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                        except:
                            continue
                    if ts >= cutoff:
                        recent_orders.append(order)
            except:
                continue
    
    print(f"\nRecent Orders (last 24 hours): {len(recent_orders)}")
    
    if recent_orders:
        print("\nMost Recent Orders:")
        for order in recent_orders[-10:]:
            symbol = order.get("symbol", "unknown")
            status = order.get("status", "unknown")
            qty = order.get("qty", 0)
            ts = order.get("ts") or order.get("timestamp", "unknown")
            print(f"  {symbol}: {qty} shares, status={status}, ts={ts}")
    else:
        print("\n  ⚠️  NO RECENT ORDERS - This is the problem!")
    
    return recent_orders

def check_recent_signals():
    """Check for recent signals"""
    print("\n" + "="*80)
    print("3. RECENT SIGNALS CHECK")
    print("="*80)
    
    if not SIGNALS_LOG.exists():
        print("\n❌ signals.jsonl does not exist")
        return []
    
    recent_signals = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    
    with SIGNALS_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                signal = json.loads(line)
                cluster = signal.get("cluster", {})
                ts = cluster.get("start_ts") or signal.get("ts") or signal.get("timestamp")
                if ts:
                    if isinstance(ts, (int, float)):
                        ts_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    else:
                        try:
                            ts_dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                        except:
                            continue
                    if ts_dt >= cutoff:
                        recent_signals.append(signal)
            except:
                continue
    
    print(f"\nRecent Signals (last 24 hours): {len(recent_signals)}")
    
    if recent_signals:
        print("\nMost Recent Signals:")
        for signal in recent_signals[-10:]:
            cluster = signal.get("cluster", {})
            symbol = cluster.get("ticker", "unknown")
            score = cluster.get("score", 0.0)
            ts = cluster.get("start_ts") or signal.get("ts", "unknown")
            print(f"  {symbol}: score={score:.2f}, ts={ts}")
    else:
        print("\n  ⚠️  NO RECENT SIGNALS - Bot may not be generating signals")
    
    return recent_signals

def check_gate_blocks():
    """Check what gates are blocking trades"""
    print("\n" + "="*80)
    print("4. GATE BLOCKS CHECK")
    print("="*80)
    
    if not GATE_LOG.exists():
        print("\n❌ gate.jsonl does not exist")
        return {}
    
    recent_blocks = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    
    with GATE_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                gate = json.loads(line)
                ts_str = gate.get("ts") or gate.get("timestamp")
                if ts_str:
                    if isinstance(ts_str, (int, float)):
                        ts = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                    else:
                        try:
                            ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                        except:
                            continue
                    if ts >= cutoff:
                        recent_blocks.append(gate)
            except:
                continue
    
    print(f"\nRecent Gate Blocks (last 24 hours): {len(recent_blocks)}")
    
    if recent_blocks:
        # Group by reason
        by_reason = {}
        for block in recent_blocks:
            reason = block.get("reason", "unknown")
            by_reason[reason] = by_reason.get(reason, 0) + 1
        
        print("\nBlocks by Reason:")
        for reason, count in sorted(by_reason.items(), key=lambda x: x[1], reverse=True):
            print(f"  {reason}: {count} blocks")
    else:
        print("\n  ✓ No recent gate blocks (or gates not logging)")
    
    return recent_blocks

def check_blocked_trades():
    """Check recent blocked trades"""
    print("\n" + "="*80)
    print("5. BLOCKED TRADES CHECK")
    print("="*80)
    
    if not BLOCKED_TRADES_LOG.exists():
        print("\n❌ blocked_trades.jsonl does not exist")
        return []
    
    recent_blocks = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    
    with BLOCKED_TRADES_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                block = json.loads(line)
                ts_str = block.get("timestamp")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                        if ts >= cutoff:
                            recent_blocks.append(block)
                    except:
                        continue
            except:
                continue
    
    print(f"\nRecent Blocked Trades (last 24 hours): {len(recent_blocks)}")
    
    if recent_blocks:
        # Group by reason
        by_reason = {}
        for block in recent_blocks:
            reason = block.get("reason", "unknown")
            by_reason[reason] = by_reason.get(reason, 0) + 1
        
        print("\nBlocks by Reason:")
        for reason, count in sorted(by_reason.items(), key=lambda x: x[1], reverse=True):
            print(f"  {reason}: {count} blocks")
    else:
        print("\n  ✓ No recent blocked trades")
    
    return recent_blocks

def check_positions():
    """Check current positions"""
    print("\n" + "="*80)
    print("6. CURRENT POSITIONS CHECK")
    print("="*80)
    
    position_file = STATE_DIR / "position_metadata.json"
    if not position_file.exists():
        print("\n❌ position_metadata.json does not exist")
        return {}
    
    try:
        with position_file.open("r") as f:
            positions = json.load(f)
        
        open_positions = positions.get("open_positions", {})
        count = len(open_positions)
        
        print(f"\nCurrent Open Positions: {count}")
        
        if count > 0:
            print("\nOpen Positions:")
            for symbol, pos in list(open_positions.items())[:10]:
                qty = pos.get("qty", 0)
                entry_price = pos.get("entry_price", 0.0)
                print(f"  {symbol}: {qty} shares @ ${entry_price:.2f}")
        
        # Check max positions
        max_positions = positions.get("max_positions", 16)
        print(f"\nMax Positions: {max_positions}")
        
        if count >= max_positions:
            print(f"\n  ⚠️  MAX POSITIONS REACHED ({count}/{max_positions})")
            print("     This will block new orders!")
        
        return positions
    except Exception as e:
        print(f"\n⚠️  Error reading positions: {e}")
        return {}

def check_freezes():
    """Check for active freezes"""
    print("\n" + "="*80)
    print("7. FREEZE STATUS CHECK")
    print("="*80)
    
    freeze_file = STATE_DIR / "governor_freezes.json"
    if not freeze_file.exists():
        print("\n✓ No freeze file found (no freezes)")
        return {}
    
    try:
        with freeze_file.open("r") as f:
            freezes = json.load(f)
        
        active_freezes = [k for k, v in freezes.items() if v]
        
        if active_freezes:
            print(f"\n⚠️  ACTIVE FREEZES: {', '.join(active_freezes)}")
            print("     This will block new orders!")
        else:
            print("\n✓ No active freezes")
        
        return freezes
    except Exception as e:
        print(f"\n⚠️  Error reading freezes: {e}")
        return {}

def check_entry_criteria():
    """Check entry criteria/thresholds"""
    print("\n" + "="*80)
    print("8. ENTRY CRITERIA CHECK")
    print("="*80)
    
    # Try to find config or check recent signals vs thresholds
    print("\nChecking recent signal scores...")
    
    if SIGNALS_LOG.exists():
        recent_scores = []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        with SIGNALS_LOG.open("r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    signal = json.loads(line)
                    cluster = signal.get("cluster", {})
                    score = cluster.get("score", 0.0)
                    ts = cluster.get("start_ts") or signal.get("ts")
                    if ts:
                        if isinstance(ts, (int, float)):
                            ts_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                        else:
                            try:
                                ts_dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                            except:
                                continue
                        if ts_dt >= cutoff and score > 0:
                            recent_scores.append(score)
                except:
                    continue
        
        if recent_scores:
            avg_score = sum(recent_scores) / len(recent_scores)
            max_score = max(recent_scores)
            min_score = min(recent_scores)
            print(f"\nRecent Signal Scores (last 24h):")
            print(f"  Count: {len(recent_scores)}")
            print(f"  Avg: {avg_score:.2f}")
            print(f"  Min: {min_score:.2f}")
            print(f"  Max: {max_score:.2f}")
            
            # Common thresholds
            print(f"\nCommon Entry Thresholds:")
            print(f"  MIN_EXEC_SCORE: Usually 2.5-3.5")
            print(f"  If signals are below threshold, they'll be blocked")
            
            if avg_score < 3.0:
                print(f"\n  ⚠️  Average score ({avg_score:.2f}) is low")
                print("     Signals may be below entry threshold")
        else:
            print("\n  ⚠️  No recent signal scores found")

def provide_recommendations(bot_running, recent_orders, recent_signals, recent_blocks, positions, freezes):
    """Provide actionable recommendations"""
    print("\n" + "="*80)
    print("DIAGNOSIS & RECOMMENDATIONS")
    print("="*80)
    
    issues = []
    
    if not bot_running:
        issues.append("❌ CRITICAL: Bot is not running")
        print("\n1. BOT NOT RUNNING:")
        print("   Fix: Restart bot with deploy_supervisor")
        print("   Command: pkill -f deploy_supervisor && screen -dmS supervisor bash -c 'cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py'")
        return
    
    if len(recent_orders) == 0:
        issues.append("❌ No recent orders")
        print("\n1. NO RECENT ORDERS:")
        
        if len(recent_signals) == 0:
            print("   Problem: No signals being generated")
            print("   Possible causes:")
            print("     - Market closed")
            print("     - Signal generation failing")
            print("     - UW daemon not running")
            print("   Fix: Check signal generation and UW daemon")
        else:
            print("   Problem: Signals generated but no orders placed")
            print("   Possible causes:")
            
            if positions and len(positions.get("open_positions", {})) >= positions.get("max_positions", 16):
                print("     - ⚠️  MAX POSITIONS REACHED")
                print("       Fix: Wait for positions to close or increase max_positions")
            
            if freezes and any(freezes.values()):
                print("     - ⚠️  ACTIVE FREEZE")
                print("       Fix: Check governor_freezes.json and clear if needed")
            
            if recent_blocks:
                print("     - ⚠️  GATES BLOCKING TRADES")
                print("       Check gate blocks above for most common reasons")
            
            print("     - Entry criteria too strict")
            print("       Check if signal scores are above MIN_EXEC_SCORE threshold")
    
    print("\n2. IMMEDIATE ACTIONS:")
    print("   - Check supervisor logs: screen -r supervisor")
    print("   - Check recent gate blocks (see above)")
    print("   - Check if max positions reached (see above)")
    print("   - Check if freeze is active (see above)")
    print("   - Verify market is open")
    print("   - Check UW daemon is running")

if __name__ == "__main__":
    from datetime import timedelta
    
    print("="*80)
    print("DIAGNOSE: WHY NO ORDERS?")
    print("="*80)
    
    bot_running = check_bot_running()
    recent_orders = check_recent_orders()
    recent_signals = check_recent_signals()
    recent_blocks = check_gate_blocks()
    blocked_trades = check_blocked_trades()
    positions = check_positions()
    freezes = check_freezes()
    check_entry_criteria()
    
    provide_recommendations(bot_running, recent_orders, recent_signals, recent_blocks, positions, freezes)
