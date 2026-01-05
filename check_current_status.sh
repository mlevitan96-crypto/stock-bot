#!/bin/bash
cd ~/stock-bot

echo "=== SIGNAL GENERATION & ORDER STATUS ==="
echo ""

echo "1. Recent Signals (last 10):"
tail -100 logs/system.jsonl 2>/dev/null | grep -E '"msg".*"(signal|cluster)"' | tail -5 | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        ts = d.get('ts', '')[:19]
        msg = d.get('msg', '')
        print(f'   {ts} | {msg[:60]}')
    except: pass
" 2>/dev/null || echo "   No recent signals"

echo ""
echo "2. Recent Order Attempts (last 10):"
tail -50 logs/order.jsonl 2>/dev/null | tail -10 | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        ts = d.get('ts', '')[:19]
        sym = d.get('symbol', 'N/A')
        action = d.get('action', 'N/A')
        status = d.get('entry_status', d.get('status', 'N/A'))
        print(f'   {ts} | {sym:6} | {action[:20]:20} | {status}')
    except: pass
" 2>/dev/null || echo "   No recent orders"

echo ""
echo "3. API Failures (after fix, last 5):"
tail -20 logs/critical_api_failure.log 2>/dev/null | tail -5 | python3 -c "
import sys
lines = [l.strip() for l in sys.stdin if l.strip()]
if lines:
    print('   Recent failures:')
    for line in lines[-3:]:
        parts = line.split(' | ', 2)
        if len(parts) >= 2:
            print(f'   {parts[0][:19]} | {parts[1]}')
else:
    print('   OK: No failures since fix')
" 2>/dev/null || echo "   OK: No failures logged"

echo ""
echo "4. Current Alpaca Positions:"
source venv/bin/activate 2>/dev/null
python3 << 'PYEOF'
from alpaca_trade_api import REST
import os
from dotenv import load_dotenv
load_dotenv()
try:
    api = REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), os.getenv('ALPACA_BASE_URL'), api_version='v2')
    pos = api.list_positions()
    print(f'   {len(pos)} positions')
    for p in pos:
        print(f'   {p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f}')
except Exception as e:
    print(f'   Error: {e}')
PYEOF

echo ""
echo "5. Bot Process Status:"
if pgrep -f "python.*main.py" > /dev/null; then
    echo "   RUNNING"
else
    echo "   NOT RUNNING"
fi

echo ""
echo "6. Last Bot Activity:"
tail -20 logs/system.jsonl 2>/dev/null | grep "run_once" | tail -1 | python3 -c "
import sys, json
from datetime import datetime, timezone
try:
    line = sys.stdin.read().strip()
    if line:
        d = json.loads(line)
        ts_str = d.get('ts', '')
        if ts_str:
            last_ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age_min = (now - last_ts).total_seconds() / 60
            print(f'   {ts_str[:19]} ({age_min:.1f} min ago)')
    else:
        print('   No recent activity')
except:
    print('   Could not parse')
" 2>/dev/null || echo "   Could not check"
