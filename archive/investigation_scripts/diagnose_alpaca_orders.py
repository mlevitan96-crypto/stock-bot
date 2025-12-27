#!/usr/bin/env python3
"""
Diagnose Why Orders Aren't Reaching Alpaca

Checks:
1. Is bot process running?
2. Are signals being generated with non-zero scores?
3. What gates are blocking trades?
4. Is Alpaca API connected?
5. Are orders being submitted to Alpaca?
6. What errors are occurring?
7. Is market open?
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
import time

LOGS_DIR = Path("logs")
STATE_DIR = Path("state")
DATA_DIR = Path("data")

def check_bot_running():
    """Check if bot process is actually running"""
    print("="*80)
    print("1. BOT PROCESS CHECK")
    print("="*80)
    
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python.*main.py"],
            capture_output=True,
            text=True,
            timeout=5
        )
        bot_running = result.returncode == 0
        
        if bot_running:
            print("✓ Bot process (main.py) is RUNNING")
            # Get process details
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.splitlines():
                if "main.py" in line and "grep" not in line:
                    print(f"  Process: {line.strip()[:80]}")
        else:
            print("❌ Bot process (main.py) is NOT RUNNING")
            print("  This is why no orders are being placed!")
        
        return bot_running
    except Exception as e:
        print(f"⚠️  Could not check processes: {e}")
        return None

def check_alpaca_connection():
    """Check if Alpaca API is connected"""
    print("\n" + "="*80)
    print("2. ALPACA API CONNECTION CHECK")
    print("="*80)
    
    # Check environment variables
    alpaca_key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY")
    alpaca_secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_API_SECRET")
    alpaca_url = os.getenv("ALPACA_BASE_URL") or os.getenv("ALPACA_URL")
    
    print(f"\nEnvironment Variables:")
    print(f"  ALPACA_KEY: {'SET' if alpaca_key else 'NOT SET'}")
    print(f"  ALPACA_SECRET: {'SET' if alpaca_secret else 'NOT SET'}")
    print(f"  ALPACA_BASE_URL: {alpaca_url or 'NOT SET'}")
    
    if not alpaca_key or not alpaca_secret:
        print("\n  ❌ CRITICAL: Alpaca credentials not set!")
        print("     Orders cannot be placed without API keys")
        return False
    
    # Try to connect
    try:
        import alpaca_trade_api as tradeapi
        api = tradeapi.REST(alpaca_key, alpaca_secret, alpaca_url or "https://paper-api.alpaca.markets")
        account = api.get_account()
        print(f"\n✓ Alpaca API Connected")
        print(f"  Account Status: {account.status}")
        print(f"  Trading Blocked: {account.trading_blocked}")
        print(f"  Pattern Day Trader: {account.pattern_day_trader}")
        print(f"  Buying Power: ${float(account.buying_power):,.2f}")
        
        if account.trading_blocked:
            print("\n  ⚠️  WARNING: Trading is BLOCKED on this account!")
            print("     No orders can be placed")
            return False
        
        # Check market status
        clock = api.get_clock()
        print(f"\n  Market Status: {clock.is_open}")
        print(f"  Next Open: {clock.next_open}")
        print(f"  Next Close: {clock.next_close}")
        
        if not clock.is_open:
            print("\n  ⚠️  Market is CLOSED")
            print("     Orders won't be placed until market opens")
        
        return True
    except Exception as e:
        print(f"\n  ❌ ERROR connecting to Alpaca: {e}")
        print("     Orders cannot be placed")
        return False

def check_recent_signals():
    """Check recent signals and their scores"""
    print("\n" + "="*80)
    print("3. SIGNAL GENERATION CHECK")
    print("="*80)
    
    signals_log = LOGS_DIR / "signals.jsonl"
    if not signals_log.exists():
        print("\n❌ signals.jsonl does not exist")
        return []
    
    recent_signals = []
    cutoff = time.time() - 3600  # Last hour
    
    with signals_log.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                signal = json.loads(line)
                cluster = signal.get("cluster", {})
                ts = cluster.get("start_ts") or signal.get("ts") or signal.get("timestamp")
                if ts and ts > cutoff:
                    score = cluster.get("score", 0.0)
                    symbol = cluster.get("ticker", "unknown")
                    recent_signals.append({
                        "symbol": symbol,
                        "score": score,
                        "ts": ts
                    })
            except:
                continue
    
    print(f"\nRecent Signals (last hour): {len(recent_signals)}")
    
    if recent_signals:
        non_zero = [s for s in recent_signals if s["score"] > 0]
        zero_scores = [s for s in recent_signals if s["score"] == 0.0]
        
        print(f"  Signals with score > 0: {len(non_zero)}")
        print(f"  Signals with score = 0: {len(zero_scores)}")
        
        if zero_scores:
            print(f"\n  ⚠️  WARNING: {len(zero_scores)} signals have score 0.00")
            print("     These won't pass entry gates")
            print("     Sample zero-score signals:")
            for s in zero_scores[:5]:
                print(f"       {s['symbol']}: score={s['score']}")
        
        if non_zero:
            print(f"\n  ✓ {len(non_zero)} signals with non-zero scores")
            print("     Sample signals:")
            for s in sorted(non_zero, key=lambda x: x["score"], reverse=True)[:5]:
                print(f"       {s['symbol']}: score={s['score']:.2f}")
        else:
            print(f"\n  ❌ CRITICAL: NO signals with non-zero scores!")
            print("     This is why no orders are being placed")
    else:
        print("\n  ⚠️  No recent signals found")
        print("     Bot may not be generating signals")
    
    return recent_signals

def check_gate_blocks():
    """Check what gates are blocking trades"""
    print("\n" + "="*80)
    print("4. GATE BLOCKS CHECK")
    print("="*80)
    
    gate_log = LOGS_DIR / "gate.jsonl"
    if not gate_log.exists():
        print("\n❌ gate.jsonl does not exist")
        return {}
    
    recent_blocks = []
    cutoff = time.time() - 3600  # Last hour
    
    with gate_log.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                gate = json.loads(line)
                ts = gate.get("_ts") or gate.get("ts") or gate.get("timestamp")
                if ts and ts > cutoff:
                    recent_blocks.append(gate)
            except:
                continue
    
    print(f"\nRecent Gate Blocks (last hour): {len(recent_blocks)}")
    
    if recent_blocks:
        by_reason = {}
        for block in recent_blocks:
            reason = block.get("msg") or block.get("reason") or block.get("event") or "unknown"
            by_reason[reason] = by_reason.get(reason, 0) + 1
        
        print("\nBlocks by Reason:")
        for reason, count in sorted(by_reason.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {reason}: {count} blocks")
    else:
        print("\n  ✓ No recent gate blocks (or gates not logging)")
    
    return recent_blocks

def check_order_submission():
    """Check if orders are being submitted to Alpaca"""
    print("\n" + "="*80)
    print("5. ORDER SUBMISSION CHECK")
    print("="*80)
    
    # Check orders.jsonl
    orders_log = LOGS_DIR / "orders.jsonl"
    if orders_log.exists():
        recent_orders = []
        cutoff = time.time() - 3600  # Last hour
        
        with orders_log.open("r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    order = json.loads(line)
                    ts = order.get("_ts") or order.get("ts") or order.get("timestamp")
                    if ts and ts > cutoff:
                        recent_orders.append(order)
                except:
                    continue
        
        print(f"\nRecent Orders in logs (last hour): {len(recent_orders)}")
        
        if recent_orders:
            print("\nMost Recent Orders:")
            for order in recent_orders[-10:]:
                symbol = order.get("symbol", "unknown")
                qty = order.get("qty", 0)
                status = order.get("status", "unknown")
                ts = order.get("_ts") or order.get("ts", "unknown")
                print(f"  {symbol}: {qty} shares, status={status}, ts={ts}")
        else:
            print("\n  ⚠️  NO recent orders in logs")
            print("     Orders are not being submitted")
    else:
        print("\n❌ orders.jsonl does not exist")
    
    # Check for Alpaca order errors
    error_logs = [
        LOGS_DIR / "error.jsonl",
        LOGS_DIR / "alpaca_error.jsonl",
        STATE_DIR / "alpaca_errors.jsonl"
    ]
    
    print("\nChecking for Alpaca API errors...")
    for error_log in error_logs:
        if error_log.exists():
            recent_errors = []
            cutoff = time.time() - 3600
            
            with error_log.open("r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        error = json.loads(line)
                        ts = error.get("_ts") or error.get("ts") or error.get("timestamp")
                        if ts and ts > cutoff:
                            if "alpaca" in str(error).lower() or "order" in str(error).lower():
                                recent_errors.append(error)
                    except:
                        continue
            
            if recent_errors:
                print(f"\n  ⚠️  Found {len(recent_errors)} Alpaca-related errors in {error_log.name}")
                print("     Recent errors:")
                for err in recent_errors[-5:]:
                    error_msg = err.get("error") or err.get("message") or str(err)
                    print(f"       {error_msg[:100]}")

def check_entry_criteria():
    """Check entry criteria and thresholds"""
    print("\n" + "="*80)
    print("6. ENTRY CRITERIA CHECK")
    print("="*80)
    
    # Try to find MIN_EXEC_SCORE
    try:
        # Check if we can import config
        import sys
        sys.path.insert(0, str(Path.cwd()))
        
        # Try to find config
        config_files = [
            Path("config/registry.py"),
            Path("main.py")
        ]
        
        min_score = None
        for config_file in config_files:
            if config_file.exists():
                code = config_file.read_text()
                # Look for MIN_EXEC_SCORE
                import re
                match = re.search(r'MIN_EXEC_SCORE\s*=\s*([\d.]+)', code)
                if match:
                    min_score = float(match.group(1))
                    break
        
        if min_score:
            print(f"\n  MIN_EXEC_SCORE: {min_score}")
            print(f"  Signals need score >= {min_score} to pass entry gate")
        else:
            print("\n  ⚠️  Could not determine MIN_EXEC_SCORE")
            print("     Common values: 2.5-3.5")
    except Exception as e:
        print(f"\n  ⚠️  Error checking entry criteria: {e}")

def provide_diagnosis(bot_running, alpaca_connected, signals, gate_blocks):
    """Provide diagnosis and recommendations"""
    print("\n" + "="*80)
    print("DIAGNOSIS & RECOMMENDATIONS")
    print("="*80)
    
    issues = []
    
    if not bot_running:
        issues.append("CRITICAL: Bot process not running")
        print("\n1. BOT NOT RUNNING:")
        print("   ❌ This is the primary issue - bot must be running to place orders")
        print("   Fix: Restart bot with deploy_supervisor")
        print("   Command: pkill -f deploy_supervisor && screen -dmS supervisor bash -c 'cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py'")
        return
    
    if not alpaca_connected:
        issues.append("CRITICAL: Alpaca API not connected")
        print("\n2. ALPACA API NOT CONNECTED:")
        print("   ❌ Cannot place orders without Alpaca connection")
        print("   Fix: Check ALPACA_KEY, ALPACA_SECRET, ALPACA_BASE_URL in .env")
        return
    
    if signals:
        non_zero = [s for s in signals if s["score"] > 0]
        if len(non_zero) == 0:
            issues.append("CRITICAL: All signals have score 0.00")
            print("\n3. NO VALID SIGNALS:")
            print("   ❌ All signals have score 0.00 - they won't pass entry gates")
            print("   Possible causes:")
            print("     - UW daemon not running (no data in cache)")
            print("     - Cache empty or corrupted")
            print("     - Signal generation failing")
            print("   Fix: Check UW daemon status and cache")
        else:
            print(f"\n3. SIGNALS:")
            print(f"   ✓ {len(non_zero)} signals with non-zero scores")
            print(f"   ⚠️  {len(signals) - len(non_zero)} signals with zero scores")
    
    if gate_blocks:
        print(f"\n4. GATE BLOCKS:")
        print(f"   ⚠️  {len(gate_blocks)} signals blocked by gates in last hour")
        print("   Check gate blocks above for most common reasons")
    
    print("\n5. IMMEDIATE ACTIONS:")
    print("   1. Verify bot is running: ps aux | grep main.py")
    print("   2. Check supervisor logs: screen -r supervisor")
    print("   3. Verify Alpaca connection (see above)")
    print("   4. Check if signals have non-zero scores (see above)")
    print("   5. Check gate blocks (see above)")
    print("   6. Verify market is open")

if __name__ == "__main__":
    print("="*80)
    print("DIAGNOSE: WHY NO ORDERS THROUGH ALPACA?")
    print("="*80)
    
    bot_running = check_bot_running()
    alpaca_connected = check_alpaca_connection()
    signals = check_recent_signals()
    gate_blocks = check_gate_blocks()
    check_order_submission()
    check_entry_criteria()
    
    provide_diagnosis(bot_running, alpaca_connected, signals, gate_blocks)
