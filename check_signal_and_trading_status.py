#!/usr/bin/env python3
"""Check signal generation and trading status"""

from droplet_client import DropletClient
import json
from datetime import datetime

def check_status():
    c = DropletClient()
    
    print("="*80)
    print("SIGNAL GENERATION & TRADING STATUS")
    print("="*80)
    print()
    
    # 1. Check if bot process is running
    print("1. Bot Process Status:")
    r = c.execute_command('pgrep -f "python.*main.py" && echo "RUNNING" || echo "NOT RUNNING"', timeout=15)
    status = r['stdout'].strip() if r['stdout'] else 'UNKNOWN'
    print(f"   {status}")
    print()
    
    # 2. Check last attribution entries (trades)
    print("2. Recent Trades (last 5):")
    r = c.execute_command('cd ~/stock-bot && tail -20 logs/attribution.jsonl 2>&1 | tail -5', timeout=20)
    if r['stdout']:
        for line in r['stdout'].strip().split('\n'):
            if line.strip():
                try:
                    data = json.loads(line)
                    ts = data.get('ts', '')[:19]
                    sym = data.get('symbol', '')
                    score = data.get('context', {}).get('score', 0)
                    direction = data.get('context', {}).get('direction', '')
                    size = data.get('context', {}).get('position_size_usd', 0)
                    print(f"   {ts} | {sym:6} | Score: {score:.2f} | {direction:8} | ${size:.2f}")
                except:
                    pass
    else:
        print("   No recent trades")
    print()
    
    # 3. Check current Alpaca positions
    print("3. Current Alpaca Positions:")
    r = c.execute_command('cd ~/stock-bot && source venv/bin/activate && python3 -c "from alpaca_trade_api import REST; import os; from dotenv import load_dotenv; load_dotenv(); api = REST(os.getenv(\'ALPACA_KEY\'), os.getenv(\'ALPACA_SECRET\'), os.getenv(\'ALPACA_BASE_URL\'), api_version=\'v2\'); pos = api.list_positions(); print(f\'{len(pos)} positions\'); [print(f\'  {p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f}\') for p in pos]" 2>&1', timeout=30)
    if r['stdout']:
        print(f"   {r['stdout'].strip()}")
    else:
        print("   Could not check")
    print()
    
    # 4. Check last system activity (run_once calls)
    print("4. Last Bot Activity:")
    r = c.execute_command('cd ~/stock-bot && tail -50 logs/system.jsonl 2>&1 | grep -E "run_once|api_start" | tail -3', timeout=20)
    if r['stdout']:
        for line in r['stdout'].strip().split('\n'):
            if line.strip():
                try:
                    data = json.loads(line)
                    ts = data.get('ts', '')[:19]
                    msg = data.get('msg', '')
                    print(f"   {ts} | {msg}")
                except:
                    print(f"   {line[:80]}")
    else:
        print("   No recent activity logs")
    print()
    
    # 5. Check cockpit API for last order
    print("5. Last Order Info:")
    r = c.execute_command('cd ~/stock-bot && curl -s http://localhost:8081/api/cockpit 2>&1 | python3 -c "import sys, json; d=json.load(sys.stdin); lo=d.get(\'last_order\', {}); print(f\"Age: {lo.get(\'age_sec\', 0)/3600:.2f} hours | Timestamp: {lo.get(\'timestamp\', 0)}\")" 2>&1', timeout=15)
    if r['stdout']:
        print(f"   {r['stdout'].strip()}")
    else:
        print("   Could not check")
    print()
    
    # 6. Check if trading loop is active (recent run_once calls)
    print("6. Trading Loop Activity:")
    r = c.execute_command('cd ~/stock-bot && tail -100 logs/system.jsonl 2>&1 | grep "run_once" | wc -l', timeout=20)
    count = r['stdout'].strip() if r['stdout'] else '0'
    print(f"   Recent run_once calls in last 100 log entries: {count}")
    
    # Check if run_once was called in last hour
    r2 = c.execute_command('cd ~/stock-bot && tail -200 logs/system.jsonl 2>&1 | grep "run_once" | tail -1', timeout=20)
    if r2['stdout']:
        try:
            data = json.loads(r2['stdout'].strip())
            ts_str = data.get('ts', '')
            if ts_str:
                from datetime import datetime, timezone
                last_ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age_min = (now - last_ts).total_seconds() / 60
                print(f"   Last run_once: {age_min:.1f} minutes ago")
        except:
            pass
    print()
    
    # 7. Check freeze state
    print("7. Freeze/Block State:")
    r = c.execute_command('cd ~/stock-bot && test -f state/freeze_active.json && echo "FROZEN" || echo "NOT FROZEN"', timeout=15)
    print(f"   {r['stdout'].strip() if r['stdout'] else 'UNKNOWN'}")
    print()
    
    c.close()
    print("="*80)

if __name__ == "__main__":
    check_status()
