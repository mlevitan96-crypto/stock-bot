#!/usr/bin/env python3
"""Check trading status: signals, decisions, and execution"""

from droplet_client import DropletClient
import json
from datetime import datetime, timedelta

def check_trading_status():
    c = DropletClient()
    
    print("="*80)
    print("TRADING STATUS CHECK")
    print("="*80)
    print()
    
    # 1. Check recent signals/clusters
    print("1. Checking recent signal generation...")
    r = c.execute_command('cd ~/stock-bot && tail -200 logs/system.jsonl 2>&1 | grep -E "run_once|clusters|signal" | tail -15', timeout=20)
    if r['stdout']:
        print(r['stdout'][:1000])
    else:
        print("  No recent signal logs")
    print()
    
    # 2. Check recent trade decisions
    print("2. Checking recent trade decisions...")
    r = c.execute_command('cd ~/stock-bot && tail -200 logs/trading.jsonl 2>&1 | grep -E "decide|should_trade|gate|blocked" | tail -20', timeout=20)
    if r['stdout']:
        print(r['stdout'][:1500])
    else:
        print("  No recent decision logs")
    print()
    
    # 3. Check recent orders/executions
    print("3. Checking recent orders/executions...")
    r = c.execute_command('cd ~/stock-bot && tail -100 logs/attribution.jsonl 2>&1 | tail -15', timeout=20)
    if r['stdout']:
        print(r['stdout'][:1500])
    else:
        print("  No recent order logs")
    print()
    
    # 4. Check current positions
    print("4. Checking current positions from Alpaca...")
    r = c.execute_command('cd ~/stock-bot && source venv/bin/activate && python3 -c "from alpaca_trade_api import REST; import os; from dotenv import load_dotenv; load_dotenv(); api = REST(os.getenv(\'ALPACA_KEY\'), os.getenv(\'ALPACA_SECRET\'), os.getenv(\'ALPACA_BASE_URL\'), api_version=\'v2\'); positions = api.list_positions(); print(f\'Positions: {len(positions)}\'); [print(f\"  {p.symbol}: {p.qty} @ {p.avg_entry_price}\") for p in positions]" 2>&1', timeout=30)
    if r['stdout']:
        print(r['stdout'][:500])
    else:
        print("  Could not check positions")
    print()
    
    # 5. Check bot metadata positions
    print("5. Checking bot metadata positions...")
    r = c.execute_command('cd ~/stock-bot && python3 -c "import json; d=json.load(open(\'state/position_metadata.json\')) if __import__(\'os\').path.exists(\'state/position_metadata.json\') else {}; positions = {k:v for k,v in d.items() if not k.startswith(\'_\')}; print(f\'Metadata positions: {len(positions)}\'); [print(f\"  {k}\") for k in positions.keys()]" 2>&1', timeout=20)
    if r['stdout']:
        print(r['stdout'][:500])
    else:
        print("  Could not check metadata")
    print()
    
    # 6. Check freeze state
    print("6. Checking freeze/block state...")
    r = c.execute_command('cd ~/stock-bot && test -f state/freeze_active.json && echo "Freeze file exists" || echo "No freeze file"', timeout=15)
    if r['stdout']:
        print(f"  {r['stdout'].strip()}")
    r2 = c.execute_command('cd ~/stock-bot && tail -50 logs/trading.jsonl 2>&1 | grep -i freeze | tail -5', timeout=20)
    if r2['stdout']:
        print(f"  Recent freeze logs:\n{r2['stdout'][:400]}")
    print()
    
    # 7. Check last run timestamp
    print("7. Checking last bot activity...")
    r = c.execute_command('cd ~/stock-bot && tail -5 logs/system.jsonl 2>&1 | tail -2', timeout=15)
    if r['stdout']:
        print(r['stdout'][:500])
    print()
    
    c.close()
    print("="*80)

if __name__ == "__main__":
    check_trading_status()
