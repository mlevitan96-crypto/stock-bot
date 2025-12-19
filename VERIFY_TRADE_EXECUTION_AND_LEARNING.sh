#!/bin/bash
# Verify trade execution and learning engine are working

cd ~/stock-bot

echo "=========================================="
echo "VERIFYING TRADE EXECUTION & LEARNING ENGINE"
echo "=========================================="
echo ""

# 1. Check if bot is running
echo "1. Checking if bot is running..."
echo "----------------------------------------"
BOT_PID=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$BOT_PID" ]; then
    echo "✅ Bot running (PID: $BOT_PID)"
else
    echo "❌ Bot not running - cannot verify"
    exit 1
fi
echo ""

# 2. Check recent order activity
echo "2. Checking recent order activity..."
echo "----------------------------------------"
if [ -f "data/live_orders.jsonl" ]; then
    ORDERS_24H=$(tail -1000 data/live_orders.jsonl 2>/dev/null | python3 -c "
import sys, json, time
now = time.time()
cutoff = now - 86400
count = 0
for line in sys.stdin:
    try:
        event = json.loads(line.strip())
        if event.get('_ts', 0) > cutoff:
            count += 1
    except:
        pass
print(count)
" 2>/dev/null || echo "0")
    echo "   Orders in last 24h: $ORDERS_24H"
    if [ "$ORDERS_24H" -gt 0 ]; then
        echo "✅ Order activity found"
    else
        echo "⚠️  No orders in last 24h (may be normal if market closed)"
    fi
else
    echo "⚠️  Order log file not found"
fi
echo ""

# 3. Check exit activity
echo "3. Checking exit/close activity..."
echo "----------------------------------------"
if [ -f "logs/exit.jsonl" ]; then
    EXITS_24H=$(tail -500 logs/exit.jsonl 2>/dev/null | python3 -c "
import sys, json, time
now = time.time()
cutoff = now - 86400
count = 0
for line in sys.stdin:
    try:
        event = json.loads(line.strip())
        if event.get('_ts', 0) > cutoff or event.get('ts'):
            count += 1
    except:
        pass
print(count)
" 2>/dev/null || echo "0")
    echo "   Exits in last 24h: $EXITS_24H"
    if [ "$EXITS_24H" -gt 0 ]; then
        echo "✅ Exit activity found"
    else
        echo "⚠️  No exits in last 24h (may be normal if no positions to close)"
    fi
else
    echo "⚠️  Exit log file not found"
fi
echo ""

# 4. Check learning engine status
echo "4. Checking learning engine..."
echo "----------------------------------------"
LEARNING_HEALTH=$(curl -s http://localhost:8081/health 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    learning = data.get('comprehensive_learning', {})
    running = learning.get('running', False)
    last_run = learning.get('last_run_age_sec')
    errors = learning.get('error_count', 0)
    success = learning.get('success_count', 0)
    print(f'{running},{last_run},{errors},{success}')
except:
    print('error,0,0,0')
" 2>/dev/null || echo "error,0,0,0")

IFS=',' read -r running last_run errors success <<< "$LEARNING_HEALTH"
if [ "$running" = "True" ] || [ "$running" = "true" ]; then
    echo "✅ Learning engine is running"
else
    echo "⚠️  Learning engine not running (may be normal if waiting for next cycle)"
fi
echo "   Last run: ${last_run:-N/A} seconds ago"
echo "   Success count: $success"
echo "   Error count: $errors"
echo ""

# 5. Check trade execution logs for errors
echo "5. Checking for execution errors..."
echo "----------------------------------------"
if [ -f "logs/worker_error.jsonl" ]; then
    ERRORS_24H=$(tail -200 logs/worker_error.jsonl 2>/dev/null | python3 -c "
import sys, json, time
now = time.time()
cutoff = now - 86400
count = 0
for line in sys.stdin:
    try:
        event = json.loads(line.strip())
        if 'order' in event.get('event', '').lower() or 'execution' in event.get('event', '').lower():
            ts = event.get('_ts', 0)
            if ts > cutoff:
                count += 1
    except:
        pass
print(count)
" 2>/dev/null || echo "0")
    echo "   Execution errors in last 24h: $ERRORS_24H"
    if [ "$ERRORS_24H" -eq 0 ]; then
        echo "✅ No execution errors"
    else
        echo "⚠️  Found $ERRORS_24H execution errors"
    fi
else
    echo "⚠️  Error log file not found"
fi
echo ""

# 6. Verify API connectivity (proves execution can work)
echo "6. Verifying API connectivity..."
echo "----------------------------------------"
HEALTH=$(curl -s http://localhost:8081/health 2>/dev/null)
if [ ! -z "$HEALTH" ]; then
    ALPACA_STATUS=$(echo "$HEALTH" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    checks = data.get('health_checks', {}).get('checks', [])
    for check in checks:
        if check.get('name') == 'alpaca_connectivity':
            print(check.get('status', 'unknown'))
            break
    else:
        print('not_found')
except:
    print('error')
" 2>/dev/null || echo "error")
    
    if [ "$ALPACA_STATUS" = "HEALTHY" ]; then
        echo "✅ Alpaca API connectivity healthy"
    else
        echo "⚠️  Alpaca connectivity: $ALPACA_STATUS"
    fi
else
    echo "❌ Cannot check health endpoint"
fi
echo ""

# 7. Check learning orchestrator import
echo "7. Verifying learning orchestrator availability..."
echo "----------------------------------------"
python3 -c "
try:
    from comprehensive_learning_orchestrator import get_learning_orchestrator
    orchestrator = get_learning_orchestrator()
    health = orchestrator.get_health()
    print('✅ Learning orchestrator available')
    print(f'   Running: {health.get(\"running\", False)}')
    print(f'   Components: {len(health.get(\"components_available\", {}))}')
except Exception as e:
    print(f'❌ Learning orchestrator error: {e}')
" 2>&1
echo ""

# Summary
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
echo "Trade Execution:"
echo "  - Bot running: ✅"
echo "  - API connectivity: ${ALPACA_STATUS:-unknown}"
echo "  - Recent orders: $ORDERS_24H"
echo "  - Recent exits: $EXITS_24H"
echo "  - Execution errors: $ERRORS_24H"
echo ""
echo "Learning Engine:"
echo "  - Status: ${running:-unknown}"
echo "  - Success count: $success"
echo "  - Error count: $errors"
echo ""
echo "Note: If market is closed, some checks may show 0 activity (normal)."
echo "When market opens Monday, verify:"
echo "  1. Orders are being placed (check logs/orders.jsonl)"
echo "  2. Positions are being closed when exit criteria met (check logs/exit.jsonl)"
echo "  3. Learning engine runs daily cycle (check logs/comprehensive_learning.jsonl)"
echo ""
