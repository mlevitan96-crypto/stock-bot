#!/usr/bin/env python3
"""
Quick check of droplet trading status - positions, trades, and GOOG analysis
"""

import subprocess
import sys
import json
from datetime import datetime

def run_ssh_command(cmd):
    """Run command on droplet via SSH"""
    full_cmd = f'ssh alpaca "{cmd}"'
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def main():
    print("=" * 80)
    print("DROPLET TRADING INVESTIGATION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Step 1: Check current positions
    print("1. CURRENT POSITIONS")
    print("-" * 80)
    cmd = """cd ~/stock-bot && python3 -c "
import os
from dotenv import load_dotenv
import alpaca_trade_api as api
import json
load_dotenv()
a = api.REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), os.getenv('ALPACA_BASE_URL'))
positions = a.list_positions()
data = [{
    'symbol': p.symbol,
    'qty': float(p.qty),
    'side': 'long' if float(p.qty) > 0 else 'short',
    'market_value': float(p.market_value),
    'unrealized_pl': float(p.unrealized_pl),
    'unrealized_plpc': float(p.unrealized_plpc),
    'avg_entry_price': float(p.avg_entry_price),
    'current_price': float(p.current_price)
} for p in positions]
print(json.dumps(data, indent=2))
" """
    stdout, stderr, code = run_ssh_command(cmd)
    if code == 0 and stdout:
        try:
            positions = json.loads(stdout)
            goog_positions = [p for p in positions if 'GOOG' in p.get('symbol', '')]
            total_pl = sum(p.get('unrealized_pl', 0) for p in positions)
            goog_pl = sum(p.get('unrealized_pl', 0) for p in goog_positions)
            
            print(f"Total positions: {len(positions)}")
            print(f"GOOG positions: {len(goog_positions)} ({len(goog_positions)/len(positions)*100:.1f}%)" if positions else "0")
            print(f"Total P/L: ${total_pl:.2f}")
            print(f"GOOG P/L: ${goog_pl:.2f}")
            print()
            print("All positions:")
            for p in positions:
                symbol = p.get('symbol', '')
                pl = p.get('unrealized_pl', 0)
                pl_pct = p.get('unrealized_plpc', 0) * 100
                print(f"  {symbol:6s} {p.get('qty', 0):8.2f} @ ${p.get('avg_entry_price', 0):7.2f} | P/L: ${pl:8.2f} ({pl_pct:6.2f}%)")
        except json.JSONDecodeError:
            print(f"Error parsing: {stdout[:200]}")
    else:
        print(f"Error: {stderr}")
    print()
    
    # Step 2: Recent trades today
    print("2. RECENT TRADES TODAY")
    print("-" * 80)
    cmd = """cd ~/stock-bot && python3 -c "
import os
from dotenv import load_dotenv
import alpaca_trade_api as api
import json
from datetime import datetime
load_dotenv()
a = api.REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), os.getenv('ALPACA_BASE_URL'))
today = datetime.now().date()
orders = a.list_orders(status='all', after=today.isoformat(), limit=100)
trades = []
for o in orders:
    if o.filled_at:
        filled_date = datetime.fromisoformat(o.filled_at.replace('Z', '+00:00')).date()
        if filled_date == today:
            trades.append({
                'symbol': o.symbol,
                'side': o.side,
                'qty': float(o.filled_qty),
                'filled_price': float(o.filled_avg_price) if o.filled_avg_price else 0,
                'filled_at': o.filled_at,
                'status': o.status
            })
print(json.dumps(trades, indent=2))
" """
    stdout, stderr, code = run_ssh_command(cmd)
    if code == 0 and stdout:
        try:
            trades = json.loads(stdout)
            goog_trades = [t for t in trades if 'GOOG' in t.get('symbol', '')]
            print(f"Total trades today: {len(trades)}")
            print(f"GOOG trades: {len(goog_trades)}")
            if trades:
                print("\nRecent trades:")
                for t in trades[-10:]:
                    print(f"  {t.get('symbol', ''):6s} {t.get('side', ''):4s} {t.get('qty', 0):8.2f} @ ${t.get('filled_price', 0):7.2f} ({t.get('filled_at', '')[:19]})")
        except json.JSONDecodeError:
            print(f"Error parsing: {stdout[:200]}")
    else:
        print(f"Error: {stderr}")
    print()
    
    # Step 3: Recent signals and GOOG activity
    print("3. RECENT SIGNALS (last 30 lines)")
    print("-" * 80)
    cmd = "cd ~/stock-bot && tail -500 logs/trading.log | grep -E 'composite_score|GOOG|decide_and_execute.*orders' | tail -30"
    stdout, stderr, code = run_ssh_command(cmd)
    if stdout:
        print(stdout)
    print()
    
    # Step 4: GOOG signals in UW cache
    print("4. GOOG SIGNALS IN UW CACHE")
    print("-" * 80)
    cmd = """cd ~/stock-bot && python3 -c "
import json
from pathlib import Path
try:
    cache = json.load(open('data/uw_flow_cache.json'))
    for sym in ['GOOG', 'GOOGL']:
        if sym in cache:
            d = cache[sym]
            print(f'{sym}: sentiment={d.get(\"sentiment\", \"MISS\")}, conviction={d.get(\"conviction\", 0):.3f}, freshness={d.get(\"freshness\", 0):.3f}')
            print(f'  flow_conv={d.get(\"flow_conv\", 0):.3f}, flow_magnitude={d.get(\"flow_magnitude\", 0):.3f}')
            print(f'  has_dp={bool(d.get(\"dark_pool\"))}, has_insider={bool(d.get(\"insider\"))}')
            print(f'  timestamp={d.get(\"timestamp\", \"MISS\")}')
        else:
            print(f'{sym}: NOT IN CACHE')
except Exception as e:
    print(f'Error: {e}')
" """
    stdout, stderr, code = run_ssh_command(cmd)
    if stdout:
        print(stdout)
    print()
    
    # Step 5: Blocked trades
    print("5. RECENT BLOCKED TRADES")
    print("-" * 80)
    cmd = "cd ~/stock-bot && tail -500 logs/trading.log | grep -E 'blocked|gate.*GOOG|concentration' | tail -20"
    stdout, stderr, code = run_ssh_command(cmd)
    if stdout:
        print(stdout)
    else:
        print("No blocked trades found in recent logs")
    print()
    
    # Step 6: Order.jsonl for today
    print("6. ORDERS FROM ORDER.JSONL (today)")
    print("-" * 80)
    cmd = """cd ~/stock-bot && tail -100 data/order.jsonl 2>/dev/null | python3 -c "
import json
import sys
from datetime import datetime
today = datetime.now().date().isoformat()
orders = []
for line in sys.stdin:
    if line.strip():
        try:
            o = json.loads(line)
            if today in o.get('ts', ''):
                orders.append(o)
        except:
            pass
for o in orders[-10:]:
    print(f\"{o.get('symbol', '')} {o.get('side', '')} {o.get('qty', 0)} @ {o.get('price', 0)} - {o.get('ts', '')[:19]}\")
print(f'Total orders today: {len(orders)}')
" """
    stdout, stderr, code = run_ssh_command(cmd)
    if stdout:
        print(stdout)
    print()
    
    print("=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
