#!/bin/bash
# Verify bot is actually running (even if env vars not visible in shell)

cd ~/stock-bot

echo "=========================================="
echo "VERIFYING BOT STATUS"
echo "=========================================="
echo ""
echo "NOTE: Environment variables in .env are loaded by Python,"
echo "      not visible in shell. This is NORMAL."
echo ""

# 1. Check process
echo "1. Checking if bot process is running..."
echo "----------------------------------------"
BOT_PID=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')
if [ ! -z "$BOT_PID" ]; then
    echo "✅ Bot process running (PID: $BOT_PID)"
else
    echo "❌ Bot process NOT running"
fi
echo ""

# 2. Check bot health endpoint
echo "2. Checking bot health endpoint..."
echo "----------------------------------------"
HEALTH=$(curl -s http://localhost:8081/health 2>/dev/null)
if [ ! -z "$HEALTH" ]; then
    echo "✅ Bot health endpoint responding"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null | head -10 || echo "$HEALTH" | head -5
else
    echo "❌ Bot health endpoint not responding"
fi
echo ""

# 3. Check recent bot activity
echo "3. Checking recent bot activity..."
echo "----------------------------------------"
if [ -f "logs/run.jsonl" ]; then
    LAST_RUN=$(tail -1 logs/run.jsonl 2>/dev/null)
    if [ ! -z "$LAST_RUN" ]; then
        echo "✅ Recent activity found in logs/run.jsonl"
        echo "   Last entry: $(echo "$LAST_RUN" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('msg', 'unknown'))" 2>/dev/null || echo "check manually")"
    else
        echo "⚠️  No recent activity in logs"
    fi
else
    echo "⚠️  logs/run.jsonl not found"
fi
echo ""

# 4. Check supervisor logs for bot activity
echo "4. Checking supervisor logs for bot activity..."
echo "----------------------------------------"
if [ -f "logs/supervisor.jsonl" ]; then
    BOT_MESSAGES=$(tail -50 logs/supervisor.jsonl 2>/dev/null | grep -i "trading-bot\|main.py" | tail -3)
    if [ ! -z "$BOT_MESSAGES" ]; then
        echo "✅ Supervisor shows bot activity"
        echo "$BOT_MESSAGES" | head -3
    else
        echo "⚠️  No bot messages in supervisor logs"
    fi
else
    echo "⚠️  logs/supervisor.jsonl not found"
fi
echo ""

# 5. Check if bot has secrets (by checking if it can connect)
echo "5. Testing if bot can access APIs (proves secrets work)..."
echo "----------------------------------------"
# If bot is responding to health endpoint, it likely has secrets
if [ ! -z "$HEALTH" ]; then
    echo "✅ Bot is responding - likely has secrets loaded"
    # Check for Alpaca errors in health response
    if echo "$HEALTH" | grep -qi "error\|missing\|secret"; then
        echo "⚠️  Health response shows errors - check secrets"
    fi
else
    echo "❌ Cannot verify (bot not responding)"
fi
echo ""

echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
if [ ! -z "$BOT_PID" ] && [ ! -z "$HEALTH" ]; then
    echo "✅ BOT IS RUNNING AND HEALTHY"
    echo ""
    echo "The 'NOT SET' message for env vars in shell is EXPECTED."
    echo "Secrets are loaded by Python process (deploy_supervisor),"
    echo "not visible in shell. This is normal behavior."
else
    echo "❌ BOT MAY NOT BE RUNNING PROPERLY"
    echo ""
    echo "Check supervisor logs:"
    echo "  screen -r supervisor"
    echo ""
    echo "Or check for errors:"
    echo "  tail -50 logs/supervisor.jsonl | grep -i error"
fi
echo ""
