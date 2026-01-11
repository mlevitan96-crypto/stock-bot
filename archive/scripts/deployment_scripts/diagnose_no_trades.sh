#!/bin/bash
cd ~/stock-bot

echo "=== COMPREHENSIVE TRADE WORKFLOW DIAGNOSIS ==="
echo ""

# 1. Check freeze state
echo "1. FREEZE STATE:"
if [ -f "state/freeze_active.json" ]; then
    echo "   BLOCKED: Freeze file exists"
    cat state/freeze_active.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'   Reason: {d.get(\"reason\", \"unknown\")}')" 2>/dev/null || echo "   (could not parse)"
else
    echo "   OK: No freeze file"
fi
echo ""

# 2. Check run_once activity
echo "2. BOT LOOP (run_once):"
run_once_count=$(grep -c "run_once" logs/system.jsonl 2>/dev/null || echo "0")
echo "   Total run_once calls: $run_once_count"
if [ "$run_once_count" -gt 0 ]; then
    last_run=$(grep "run_once" logs/system.jsonl 2>/dev/null | tail -1 | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('ts', 'N/A')[:19])" 2>/dev/null)
    echo "   Last run_once: $last_run"
else
    echo "   WARNING: No run_once calls found"
fi
echo ""

# 3. Check signals
echo "3. SIGNAL GENERATION:"
signal_count=$(wc -l < logs/signals.jsonl 2>/dev/null || echo "0")
echo "   Total signals: $signal_count"
if [ "$signal_count" -gt 0 ]; then
    last_signal=$(tail -1 logs/signals.jsonl 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); c=d.get('cluster',{}); print(f\"{d.get('ts','N/A')[:19]} | {c.get('ticker','N/A')} | {c.get('direction','N/A')}\")" 2>/dev/null)
    echo "   Last signal: $last_signal"
fi
echo ""

# 4. Check clusters/composite scoring
echo "4. CLUSTERS & COMPOSITE SCORING:"
cluster_logs=$(grep -c "composite.*cluster\|cluster.*composite" logs/system.jsonl 2>/dev/null || echo "0")
echo "   Cluster/composite events: $cluster_logs"
echo ""

# 5. Check decide_and_execute calls
echo "5. DECIDE_AND_EXECUTE:"
decide_logs=$(grep -c "decide_and_execute\|Processing.*clusters" logs/system.jsonl 2>/dev/null || echo "0")
echo "   Decision events: $decide_logs"
echo ""

# 6. Check gate blocks
echo "6. GATE BLOCKS:"
if [ -f "logs/trading.jsonl" ]; then
    blocked_count=$(grep -c "blocked\|BLOCKED" logs/trading.jsonl 2>/dev/null || echo "0")
    echo "   Total blocks: $blocked_count"
    if [ "$blocked_count" -gt 0 ]; then
        echo "   Recent blocks (last 5):"
        grep "blocked\|BLOCKED" logs/trading.jsonl 2>/dev/null | tail -5 | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        sym = d.get('symbol', 'N/A')
        reason = d.get('reason', d.get('msg', 'N/A'))[:50]
        print(f'   {sym}: {reason}')
    except: pass
" 2>/dev/null
    fi
else
    echo "   No trading log found"
fi
echo ""

# 7. Check orders
echo "7. ORDER SUBMISSIONS:"
if [ -f "logs/order.jsonl" ]; then
    order_count=$(wc -l < logs/order.jsonl 2>/dev/null || echo "0")
    echo "   Total orders: $order_count"
    if [ "$order_count" -gt 0 ]; then
        last_order=$(tail -1 logs/order.jsonl 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"{d.get('ts','N/A')[:19]} | {d.get('symbol','N/A')} | {d.get('action',d.get('msg','N/A'))[:30]}\")" 2>/dev/null)
        echo "   Last order: $last_order"
    fi
else
    echo "   No order log found"
fi
echo ""

# 8. Check API failures
echo "8. API FAILURES:"
if [ -f "logs/critical_api_failure.log" ]; then
    failure_count=$(wc -l < logs/critical_api_failure.log 2>/dev/null || echo "0")
    echo "   Total failures: $failure_count"
    if [ "$failure_count" -gt 0 ]; then
        echo "   Last failure:"
        tail -1 logs/critical_api_failure.log 2>/dev/null | python3 -c "
import sys
line = sys.stdin.read().strip()
if ' | ' in line:
    parts = line.split(' | ', 2)
    print(f'   {parts[0][:19]} | {parts[1]}')
" 2>/dev/null
    fi
else
    echo "   No failure log"
fi
echo ""

# 9. Check Alpaca positions
echo "9. ALPACA POSITIONS:"
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
echo "=== DIAGNOSIS COMPLETE ==="
