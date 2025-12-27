#!/usr/bin/env python3
"""
Fix No Positions Issues - Run on Droplet
This script diagnoses and fixes the issues preventing positions from opening.
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

def check_alpaca_positions():
    """Check actual Alpaca positions."""
    print("=" * 60)
    print("CHECKING ALPACA POSITIONS")
    print("=" * 60)
    
    stdout, stderr, code = run_command(
        "cd ~/stock-bot && python3 -c \""
        "import os; from dotenv import load_dotenv; load_dotenv(); "
        "import alpaca_trade_api as tradeapi; "
        "api = tradeapi.REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_API_SECRET'), os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'), api_version='v2'); "
        "positions = api.list_positions(); "
        "print(f'Open positions in Alpaca: {len(positions)}'); "
        "for p in positions: print(f'  {p.symbol}: {p.qty} shares @ ${float(p.avg_entry_price):.2f}')\""
    )
    print(stdout)
    if stderr:
        print(f"[ERROR] {stderr}")
    return stdout

def check_signal_generation():
    """Check why signals show as unknown."""
    print("\n" + "=" * 60)
    print("CHECKING SIGNAL GENERATION")
    print("=" * 60)
    
    # Check recent signals file
    signals_file = Path("logs/signals.jsonl")
    if signals_file.exists():
        print("Checking last 5 signals from file:")
        with open(signals_file) as f:
            lines = f.readlines()
            for line in lines[-5:]:
                if line.strip():
                    try:
                        sig = json.loads(line)
                        print(f"  Symbol: {sig.get('symbol')}, Score: {sig.get('composite_score')}, Timestamp: {sig.get('timestamp')}")
                    except:
                        print(f"  [ERROR] Could not parse: {line[:50]}")
    
    # Check if UW API is working
    stdout, stderr, code = run_command(
        "cd ~/stock-bot && python3 -c \""
        "import requests; import os; from dotenv import load_dotenv; load_dotenv(); "
        "api_key = os.getenv('UW_API_KEY'); "
        "if api_key: "
        "  r = requests.get('https://api.unusualwhales.com/api/market/top-net-impact', headers={'Authorization': api_key}, timeout=5); "
        "  print(f'UW API status: {r.status_code}'); "
        "  print(f'Response length: {len(r.text)}'); "
        "else: "
        "  print('UW API key not found')\""
    )
    print("\nUW API Check:")
    print(stdout)
    if stderr:
        print(f"[ERROR] {stderr}")

def check_max_positions_logic():
    """Check why max_positions_reached when no positions exist."""
    print("\n" + "=" * 60)
    print("CHECKING MAX POSITIONS LOGIC")
    print("=" * 60)
    
    stdout, stderr, code = run_command(
        "cd ~/stock-bot && python3 -c \""
        "import os; from dotenv import load_dotenv; load_dotenv(); "
        "import alpaca_trade_api as tradeapi; "
        "api = tradeapi.REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_API_SECRET'), os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'), api_version='v2'); "
        "positions = api.list_positions(); "
        "print(f'Actual Alpaca positions: {len(positions)}'); "
        "max_pos = 16; "
        "print(f'Max positions allowed: {max_pos}'); "
        "print(f'Can open new position: {len(positions) < max_pos}')\""
    )
    print(stdout)
    if stderr:
        print(f"[ERROR] {stderr}")

def check_bot_state():
    """Check bot's internal state."""
    print("\n" + "=" * 60)
    print("CHECKING BOT INTERNAL STATE")
    print("=" * 60)
    
    # Check if there are any state files
    state_files = [
        "state/positions.json",
        "state/internal_positions.json",
        "state/alpaca_positions.json",
        "state/executor_state.json"
    ]
    
    for state_file in state_files:
        path = Path(state_file)
        if path.exists():
            print(f"{state_file}: EXISTS ({path.stat().st_size} bytes)")
            try:
                with open(path) as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        print(f"  Keys: {list(data.keys())[:10]}")
                    elif isinstance(data, list):
                        print(f"  Items: {len(data)}")
            except:
                print(f"  [ERROR] Could not read")
        else:
            print(f"{state_file}: DOES NOT EXIST")

def main():
    print("=" * 60)
    print("FIXING NO POSITIONS ISSUES")
    print("=" * 60)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    check_alpaca_positions()
    check_signal_generation()
    check_max_positions_logic()
    check_bot_state()
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

