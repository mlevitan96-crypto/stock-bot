#!/usr/bin/env python3
"""
Diagnose and Fix No Positions Issue - Run on Droplet
This script checks actual Alpaca positions, signal generation, and fixes issues.
"""

import json
import subprocess
import os
from pathlib import Path
from datetime import datetime, timezone

def run_command(cmd):
    """Run command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def check_alpaca_positions():
    """Check actual Alpaca positions."""
    print("=" * 60)
    print("CHECKING ACTUAL ALPACA POSITIONS")
    print("=" * 60)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    import alpaca_trade_api as tradeapi
    api = tradeapi.REST(
        os.getenv('ALPACA_API_KEY'),
        os.getenv('ALPACA_API_SECRET'),
        os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
        api_version='v2'
    )
    
    try:
        positions = api.list_positions()
        print(f"Alpaca API positions: {len(positions)}")
        for p in positions:
            print(f"  {p.symbol}: {p.qty} shares @ ${float(p.avg_entry_price):.2f} (side: {'long' if float(p.qty) > 0 else 'short'})")
        
        account = api.get_account()
        print(f"\nAccount Info:")
        print(f"  Cash: ${float(account.cash):.2f}")
        print(f"  Portfolio Value: ${float(account.portfolio_value):.2f}")
        print(f"  Buying Power: ${float(account.buying_power):.2f}")
        print(f"  Equity: ${float(account.equity):.2f}")
        
        return len(positions)
    except Exception as e:
        print(f"[ERROR] Failed to check Alpaca: {e}")
        return 0

def check_executor_opens():
    """Check executor.opens state."""
    print("\n" + "=" * 60)
    print("CHECKING EXECUTOR.OPENS STATE")
    print("=" * 60)
    
    executor_state = Path("state/executor_state.json")
    if executor_state.exists():
        with open(executor_state) as f:
            data = json.load(f)
            opens = data.get("opens", {})
            print(f"executor.opens has {len(opens)} positions")
            if opens:
                for symbol, info in opens.items():
                    print(f"  {symbol}: {info}")
            else:
                print("  [INFO] executor.opens is empty (no internal positions tracked)")
    else:
        print("  [WARNING] executor_state.json does not exist")

def check_recent_signals():
    """Check if signals are being generated recently."""
    print("\n" + "=" * 60)
    print("CHECKING RECENT SIGNAL GENERATION")
    print("=" * 60)
    
    signals_file = Path("logs/signals.jsonl")
    if not signals_file.exists():
        print("  [ERROR] signals.jsonl does not exist")
        return
    
    # Get last signal timestamp
    with open(signals_file) as f:
        lines = f.readlines()
        if lines:
            last_line = lines[-1]
            try:
                sig = json.loads(last_line)
                cluster = sig.get("cluster", {})
                timestamp = sig.get("ts") or cluster.get("timestamp", "unknown")
                ticker = cluster.get("ticker", "unknown")
                score = cluster.get("composite_score", 0)
                print(f"  Last signal: {ticker} (score={score:.2f}) at {timestamp}")
                
                # Check if recent (within last hour)
                try:
                    if isinstance(timestamp, str):
                        from dateutil import parser
                        last_signal_time = parser.parse(timestamp)
                        now = datetime.now(timezone.utc)
                        age_minutes = (now - last_signal_time.replace(tzinfo=timezone.utc)).total_seconds() / 60
                        print(f"  Signal age: {age_minutes:.1f} minutes ago")
                        if age_minutes > 60:
                            print(f"  [WARNING] Last signal is {age_minutes/60:.1f} hours old - signals may not be generating")
                except:
                    pass
            except Exception as e:
                print(f"  [ERROR] Could not parse last signal: {e}")

def check_uw_flow_cache():
    """Check UW flow cache."""
    print("\n" + "=" * 60)
    print("CHECKING UW FLOW CACHE")
    print("=" * 60)
    
    uw_cache = Path("data/uw_flow_cache.json")
    if uw_cache.exists():
        with open(uw_cache) as f:
            data = json.load(f)
            print(f"UW cache has {len(data)} symbols")
            if data:
                # Check cache age
                cache_time = data.get("_cache_timestamp")
                if cache_time:
                    print(f"Cache timestamp: {cache_time}")
                # Show sample
                sample = list(data.items())[:3]
                for symbol, cache in sample:
                    if isinstance(cache, dict):
                        print(f"  {symbol}: conviction={cache.get('conviction', 0):.2f}, sentiment={cache.get('sentiment', 'unknown')}")
    else:
        print("  [WARNING] UW cache file does not exist")

def check_main_py_logs():
    """Check main.py recent output."""
    print("\n" + "=" * 60)
    print("CHECKING MAIN.PY RECENT LOGS")
    print("=" * 60)
    
    # Check run.jsonl for recent activity
    run_file = Path("logs/run.jsonl")
    if run_file.exists():
        with open(run_file) as f:
            lines = f.readlines()
            recent = lines[-10:] if len(lines) > 10 else lines
            print(f"Last {len(recent)} run cycles:")
            for line in recent:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        event = rec.get("event", "unknown")
                        symbol = rec.get("symbol", "")
                        print(f"  {event} {symbol}")
                    except:
                        print(f"  {line[:80]}")

def main():
    print("=" * 60)
    print("DIAGNOSING AND FIXING NO POSITIONS ISSUE")
    print("=" * 60)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    alpaca_count = check_alpaca_positions()
    check_executor_opens()
    check_recent_signals()
    check_uw_flow_cache()
    check_main_py_logs()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS SUMMARY")
    print("=" * 60)
    print(f"Alpaca positions: {alpaca_count}")
    print(f"Max allowed: 16")
    print(f"Can open new: {alpaca_count < 16}")
    
    if alpaca_count == 0:
        print("\n[INFO] No positions in Alpaca - bot should be able to open positions")
        print("[ACTION] Need to check why signals aren't being processed or why gates are blocking")

if __name__ == "__main__":
    main()

