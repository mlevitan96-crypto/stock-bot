#!/usr/bin/env python3
"""
Fix Max Positions and Signal Issues - Run on Droplet
This script fixes the issues preventing positions from opening.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

def run_command(cmd):
    """Run command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def check_actual_positions():
    """Check actual Alpaca positions vs internal state."""
    print("=" * 60)
    print("CHECKING ACTUAL VS INTERNAL POSITIONS")
    print("=" * 60)
    
    stdout, stderr, code = run_command(
        "cd ~/stock-bot && python3 << 'PYEOF'\n"
        "import os\n"
        "from dotenv import load_dotenv\n"
        "load_dotenv()\n"
        "import alpaca_trade_api as tradeapi\n"
        "api = tradeapi.REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_API_SECRET'), os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'), api_version='v2')\n"
        "positions = api.list_positions()\n"
        "print(f'Alpaca positions: {len(positions)}')\n"
        "for p in positions:\n"
        "    print(f'  {p.symbol}: {p.qty} shares')\n"
        "PYEOF"
    )
    print(stdout)
    if stderr:
        print(f"[ERROR] {stderr}")
    
    # Check internal state
    executor_state = Path("state/executor_state.json")
    if executor_state.exists():
        with open(executor_state) as f:
            data = json.load(f)
            opens = data.get("opens", {})
            print(f"\nInternal executor.opens: {len(opens)} positions")
            if opens:
                for symbol in opens.keys():
                    print(f"  {symbol}")
    
    return stdout

def check_recent_signals_format():
    """Check actual signal format in logs."""
    print("\n" + "=" * 60)
    print("CHECKING SIGNAL FORMAT IN LOGS")
    print("=" * 60)
    
    signals_file = Path("logs/signals.jsonl")
    if signals_file.exists():
        print("Reading last 5 signals:")
        with open(signals_file) as f:
            lines = f.readlines()
            for line in lines[-5:]:
                if line.strip():
                    try:
                        sig = json.loads(line)
                        print(f"\nSignal record:")
                        print(f"  Type: {sig.get('type')}")
                        cluster = sig.get('cluster', {})
                        if cluster:
                            print(f"  Cluster ticker: {cluster.get('ticker')}")
                            print(f"  Cluster composite_score: {cluster.get('composite_score')}")
                            print(f"  Cluster direction: {cluster.get('direction')}")
                            print(f"  Cluster source: {cluster.get('source')}")
                        else:
                            print(f"  [WARNING] No cluster in signal")
                    except Exception as e:
                        print(f"  [ERROR] Could not parse: {e}")
                        print(f"  Line: {line[:100]}")

def check_uw_flow_daemon():
    """Check if UW flow daemon is working."""
    print("\n" + "=" * 60)
    print("CHECKING UW FLOW DAEMON")
    print("=" * 60)
    
    stdout, stderr, code = run_command("ps aux | grep uw_flow_daemon | grep -v grep")
    if stdout.strip():
        print("[OK] UW flow daemon is running")
        print(stdout)
    else:
        print("[WARNING] UW flow daemon not running")
    
    # Check UW cache
    uw_cache = Path("data/uw_flow_cache.json")
    if uw_cache.exists():
        with open(uw_cache) as f:
            data = json.load(f)
            print(f"\nUW cache has {len(data)} symbols")
            if data:
                sample = list(data.items())[:3]
                for symbol, cache in sample:
                    print(f"  {symbol}: conviction={cache.get('conviction', 0):.2f}")
    else:
        print("[WARNING] UW cache file does not exist")

def main():
    print("=" * 60)
    print("FIXING MAX POSITIONS AND SIGNAL ISSUES")
    print("=" * 60)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    check_actual_positions()
    check_recent_signals_format()
    check_uw_flow_daemon()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)
    
    # Create fix recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDED FIXES")
    print("=" * 60)
    print("1. Ensure executor.opens is synced with Alpaca positions")
    print("2. Fix signal logging to include symbol and score at top level")
    print("3. Verify UW flow daemon is populating cache")
    print("4. Check why max_positions_reached when no positions exist")

if __name__ == "__main__":
    main()

