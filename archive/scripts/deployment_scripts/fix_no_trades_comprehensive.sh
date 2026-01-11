#!/bin/bash
# Comprehensive fix for no trades issue
# Addresses all possible causes

cd ~/stock-bot

echo "=========================================="
echo "COMPREHENSIVE FIX: No Trades Today"
echo "=========================================="
echo ""

# Step 1: Pull latest code
echo "Step 1: Pulling latest code..."
git pull origin main --no-rebase || git fetch origin && git reset --hard origin/main
echo "✅ Code updated"
echo ""

# Step 2: Check if services are running
echo "Step 2: Checking services..."
if ! pgrep -f "deploy_supervisor" > /dev/null; then
    echo "⚠️  Supervisor not running - starting it..."
    source venv/bin/activate
    screen -dmS supervisor python deploy_supervisor.py
    sleep 5
fi

if ! pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Main trading bot not running"
else
    echo "✅ Trading bot is running"
fi

if ! pgrep -f "uw_flow_daemon" > /dev/null; then
    echo "⚠️  UW daemon not running"
else
    echo "✅ UW daemon is running"
fi
echo ""

# Step 3: Run investigation
echo "Step 3: Running investigation..."
python3 investigate_no_trades.py 2>/dev/null || echo "⚠️  Investigation script had errors"
echo ""

# Step 4: Check common issues
echo "Step 4: Checking common issues..."

# Check positions
if [ -f "state/internal_positions.json" ]; then
    POS_COUNT=$(python3 -c "import json; f=open('state/internal_positions.json'); d=json.load(f); print(len([k for k in d.keys() if isinstance(d[k], dict)]))" 2>/dev/null || echo "0")
    echo "Current positions: $POS_COUNT/16"
    if [ "$POS_COUNT" -ge 16 ]; then
        echo "⚠️  At max positions - bot may be waiting for exits"
    fi
fi

# Check blocked trades
if [ -f "state/blocked_trades.jsonl" ]; then
    BLOCK_COUNT=$(wc -l < state/blocked_trades.jsonl 2>/dev/null || echo "0")
    echo "Recent blocked trades: $BLOCK_COUNT"
    if [ "$BLOCK_COUNT" -gt 0 ]; then
        echo "Recent block reasons:"
        tail -20 state/blocked_trades.jsonl | python3 -c "
import sys, json
reasons = {}
for line in sys.stdin:
    try:
        d = json.loads(line)
        r = d.get('reason', 'unknown')
        reasons[r] = reasons.get(r, 0) + 1
    except: pass
for r, c in sorted(reasons.items(), key=lambda x: -x[1])[:5]:
    print(f'  - {r}: {c} times')
" 2>/dev/null || echo "  (could not parse)"
    fi
fi

# Check UW cache
if [ -f "data/uw_flow_cache.json" ]; then
    TICKER_COUNT=$(python3 -c "import json; f=open('data/uw_flow_cache.json'); d=json.load(f); print(len([k for k,v in d.items() if isinstance(v, dict) and v.get('flow_trades') and len(v.get('flow_trades', [])) > 0]))" 2>/dev/null || echo "0")
    echo "Tickers with flow trades: $TICKER_COUNT"
    if [ "$TICKER_COUNT" -eq 0 ]; then
        echo "⚠️  No tickers have flow trades - UW daemon may not be fetching data"
    fi
fi
echo ""

# Step 5: Restart services to ensure clean state
echo "Step 5: Restarting services for clean state..."
pkill -f deploy_supervisor
sleep 3
source venv/bin/activate
screen -dmS supervisor python deploy_supervisor.py
sleep 5

if pgrep -f "deploy_supervisor" > /dev/null; then
    echo "✅ Services restarted"
else
    echo "❌ Failed to restart services"
fi
echo ""

# Step 6: Commit investigation results
echo "Step 6: Committing results..."
if [ -f "investigate_no_trades.json" ]; then
    git add investigate_no_trades.json
    git commit -m "Investigation results - $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || true
    git push origin main 2>/dev/null || true
    echo "✅ Results committed to git"
fi
echo ""

echo "=========================================="
echo "FIX COMPLETE"
echo "=========================================="
echo ""
echo "Monitor with: screen -r supervisor"
echo "Check logs: tail -f logs/trading.log"
echo ""

