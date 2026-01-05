#!/usr/bin/env python3
"""Check signal generation and order execution status"""

from droplet_client import DropletClient
import json
from datetime import datetime, timezone

def check_status():
    c = DropletClient()
    
    print("="*80)
    print("SIGNAL GENERATION & ORDER EXECUTION STATUS")
    print("="*80)
    print()
    
    # 1. Check recent signals
    print("1. Recent Signal Generation:")
    r = c.execute_command('cd ~/stock-bot && tail -100 logs/system.jsonl 2>&1 | grep -E "signal|cluster" | tail -10', timeout=20)
    if r['stdout']:
        lines = r['stdout'].strip().split('\n')
        for line in lines[-5:]:
            if line.strip():
                try:
                    data = json.loads(line)
                    ts = data.get('ts', '')[:19] if data.get('ts') else 'N/A'
                    msg = data.get('msg', '')[:60]
                    print(f"   {ts} | {msg}")
                except:
                    print(f"   {line[:80]}")
    else:
        print("   No recent signal logs")
    print()
    
    # 2. Check recent order submissions
    print("2. Recent Order Submissions:")
    r = c.execute_command('cd ~/stock-bot && tail -50 logs/order.jsonl 2>&1 | tail -10', timeout=20)
    if r['stdout']:
        for line in r['stdout'].strip().split('\n'):
            if line.strip():
                try:
                    data = json.loads(line)
                    ts = data.get('ts', '')[:19] if data.get('ts') else 'N/A'
                    action = data.get('action', '')
                    symbol = data.get('symbol', '')
                    status = data.get('entry_status', data.get('status', ''))
                    print(f"   {ts} | {symbol:6} | {action:25} | {status}")
                except:
                    print(f"   {line[:80]}")
    else:
        print("   No recent order logs")
    print()
    
    # 3. Check for API failures (after fix)
    print("3. Recent API Failures (after fix):")
    r = c.execute_command('cd ~/stock-bot && tail -20 logs/critical_api_failure.log 2>&1 | tail -5', timeout=20)
    if r['stdout'] and r['stdout'].strip():
        print("   WARNING: Failures found:")
        for line in r['stdout'].strip().split('\n')[-3:]:
            if line.strip():
                parts = line.split(' | ', 2)
                if len(parts) >= 3:
                    ts = parts[0][:19]
                    event = parts[1]
                    print(f"   {ts} | {event}")
                else:
                    print(f"   {line[:80]}")
    else:
        print("   OK: No recent API failures")
    print()
    
    # 4. Check Alpaca positions
    print("4. Current Alpaca Positions:")
    r = c.execute_command('cd ~/stock-bot && source venv/bin/activate && python3 << \"EOF\"\nfrom alpaca_trade_api import REST\nimport os\nfrom dotenv import load_dotenv\nload_dotenv()\napi = REST(os.getenv(\"ALPACA_KEY\"), os.getenv(\"ALPACA_SECRET\"), os.getenv(\"ALPACA_BASE_URL\"), api_version=\"v2\")\npos = api.list_positions()\nprint(f\"{len(pos)} positions\")\nfor p in pos:\n    print(f\"  {p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f}\")\nEOF\n 2>&1', timeout=30)
    if r['stdout']:
        print(f"   {r['stdout'].strip()}")
    else:
        print("   Could not check positions")
    print()
    
    # 5. Check recent trades (attribution)
    print("5. Recent Trades (last 5):")
    r = c.execute_command('cd ~/stock-bot && tail -20 logs/attribution.jsonl 2>&1 | tail -5', timeout=20)
    if r['stdout']:
        for line in r['stdout'].strip().split('\n'):
            if line.strip():
                try:
                    data = json.loads(line)
                    ts = data.get('ts', '')[:19] if data.get('ts') else 'N/A'
                    symbol = data.get('symbol', '')
                    score = data.get('context', {}).get('score', 0)
                    direction = data.get('context', {}).get('direction', '')
                    print(f"   {ts} | {symbol:6} | Score: {score:.2f} | {direction:8}")
                except:
                    pass
    else:
        print("   No recent trades")
    print()
    
    # 6. Check bot activity (run_once calls)
    print("6. Bot Activity:")
    r = c.execute_command('cd ~/stock-bot && tail -50 logs/system.jsonl 2>&1 | grep "run_once" | tail -3', timeout=20)
    if r['stdout']:
        for line in r['stdout'].strip().split('\n'):
            if line.strip():
                try:
                    data = json.loads(line)
                    ts = data.get('ts', '')[:19] if data.get('ts') else 'N/A'
                    print(f"   {ts} | run_once executed")
                except:
                    print(f"   {line[:60]}")
    else:
        print("   No recent run_once logs")
    print()
    
    c.close()
    print("="*80)

if __name__ == "__main__":
    check_status()
