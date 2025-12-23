#!/bin/bash
# Restart bot and diagnose signal generation issues

echo "=================================================================================="
echo "RESTARTING BOT AND DIAGNOSING ISSUES"
echo "=================================================================================="

cd ~/stock-bot

# 1. Stop supervisor
echo ""
echo "1. Stopping supervisor..."
pkill -f deploy_supervisor
sleep 2

# 2. Check for stuck processes
echo ""
echo "2. Checking for stuck processes..."
ps aux | grep -E "main.py|dashboard.py|uw_flow_daemon" | grep -v grep

# 3. Kill any stuck processes
echo ""
echo "3. Killing stuck processes..."
pkill -f "python.*main.py"
pkill -f "python.*dashboard.py"
pkill -f "python.*uw_flow_daemon"
sleep 2

# 4. Check UW daemon status
echo ""
echo "4. Checking UW daemon status..."
if [ -f "state/uw_daemon_heartbeat.json" ]; then
    echo "  UW daemon heartbeat found"
    cat state/uw_daemon_heartbeat.json | head -5
else
    echo "  ⚠️  No UW daemon heartbeat found"
fi

# 5. Check recent signal scores
echo ""
echo "5. Checking recent signal scores..."
if [ -f "logs/signals.jsonl" ]; then
    echo "  Last 5 signals:"
    tail -5 logs/signals.jsonl | while read line; do
        if [ ! -z "$line" ]; then
            symbol=$(echo "$line" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('cluster', {}).get('ticker', 'unknown'))" 2>/dev/null || echo "unknown")
            score=$(echo "$line" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('cluster', {}).get('score', 0))" 2>/dev/null || echo "0")
            echo "    $symbol: score=$score"
        fi
    done
fi

# 6. Check UW attribution for recent signals
echo ""
echo "6. Checking UW attribution (signal generation)..."
if [ -f "data/uw_attribution.jsonl" ]; then
    recent_count=$(tail -100 data/uw_attribution.jsonl | grep -c "\"score\"" || echo "0")
    echo "  Recent UW attribution records with scores: $recent_count"
    
    echo "  Last 3 UW attribution records:"
    tail -3 data/uw_attribution.jsonl | while read line; do
        if [ ! -z "$line" ]; then
            symbol=$(echo "$line" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('symbol', 'unknown'))" 2>/dev/null || echo "unknown")
            score=$(echo "$line" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('score', 0))" 2>/dev/null || echo "0")
            decision=$(echo "$line" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('decision', 'unknown'))" 2>/dev/null || echo "unknown")
            echo "    $symbol: score=$score, decision=$decision"
        fi
    done
fi

# 7. Restart supervisor
echo ""
echo "7. Restarting supervisor..."
source venv/bin/activate
screen -dmS supervisor bash -c "cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py"
sleep 3

# 8. Verify processes started
echo ""
echo "8. Verifying processes started..."
sleep 2
ps aux | grep -E "deploy_supervisor|main.py|dashboard.py|uw_flow_daemon" | grep -v grep

echo ""
echo "=================================================================================="
echo "RESTART COMPLETE"
echo "=================================================================================="
echo ""
echo "Next steps:"
echo "1. Wait 30 seconds for services to start"
echo "2. Check supervisor logs: screen -r supervisor"
echo "3. Run diagnostic again: python3 diagnose_no_orders.py"
echo "4. Check if signals now have non-zero scores"
echo ""
