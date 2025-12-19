#!/bin/bash
# Check why trading bot isn't running

cd ~/stock-bot

echo "=========================================="
echo "DIAGNOSING WHY BOT ISN'T RUNNING"
echo "=========================================="
echo ""

# 1. Check supervisor logs
echo "1. Supervisor logs (last 20 lines)..."
echo "----------------------------------------"
if [ -f "logs/supervisor.jsonl" ]; then
    tail -20 logs/supervisor.jsonl | python3 -m json.tool 2>/dev/null | tail -30 || tail -20 logs/supervisor.jsonl
else
    echo "⚠️  No supervisor log file found"
fi
echo ""

# 2. Check if secrets are set
echo "2. Checking environment variables..."
echo "----------------------------------------"
if [ -z "$UW_API_KEY" ]; then
    echo "❌ UW_API_KEY: NOT SET"
else
    echo "✅ UW_API_KEY: SET (${#UW_API_KEY} chars)"
fi

if [ -z "$ALPACA_KEY" ] && [ -z "$ALPACA_API_KEY" ]; then
    echo "❌ ALPACA_KEY: NOT SET"
else
    echo "✅ ALPACA_KEY: SET"
fi

if [ -z "$ALPACA_SECRET" ] && [ -z "$ALPACA_API_SECRET" ]; then
    echo "❌ ALPACA_SECRET: NOT SET"
else
    echo "✅ ALPACA_SECRET: SET"
fi

if [ -z "$TRADING_MODE" ]; then
    echo "⚠️  TRADING_MODE: NOT SET (will default to PAPER)"
else
    echo "✅ TRADING_MODE: $TRADING_MODE"
fi
echo ""

# 3. Check supervisor screen session
echo "3. Checking supervisor output..."
echo "----------------------------------------"
echo "Run this to see supervisor output:"
echo "  screen -r supervisor"
echo ""
echo "Or check if there are error messages:"
screen -r supervisor -X hardcopy /tmp/supervisor_output.txt 2>/dev/null || true
if [ -f "/tmp/supervisor_output.txt" ]; then
    tail -30 /tmp/supervisor_output.txt
    rm /tmp/supervisor_output.txt
else
    echo "   (Attach to screen to see output)"
fi
echo ""

# 4. Try starting bot manually to see error
echo "4. Testing bot startup manually..."
echo "----------------------------------------"
source venv/bin/activate
python3 -c "
import os
import sys
print('Python:', sys.executable)
print('Venv:', os.getenv('VIRTUAL_ENV', 'NOT IN VENV'))
try:
    import alpaca_trade_api
    print('✅ alpaca_trade_api imported')
except ImportError as e:
    print(f'❌ alpaca_trade_api: {e}')

try:
    import flask
    print('✅ flask imported')
except ImportError as e:
    print(f'❌ flask: {e}')

# Check if main.py can be imported
try:
    sys.path.insert(0, '.')
    # Just check imports, don't run
    print('✅ Can access main.py')
except Exception as e:
    print(f'❌ Error accessing main.py: {e}')
" 2>&1
echo ""

# 5. Check if .env file exists
echo "5. Checking for .env file..."
echo "----------------------------------------"
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    echo "   (Secrets should be loaded from here)"
else
    echo "⚠️  .env file not found"
    echo "   Secrets must be set as environment variables"
fi
echo ""

echo "=========================================="
echo "RECOMMENDATIONS"
echo "=========================================="
echo ""
echo "If secrets are missing:"
echo "  1. Create .env file with:"
echo "     UW_API_KEY=your_key"
echo "     ALPACA_KEY=your_key"
echo "     ALPACA_SECRET=your_secret"
echo "     TRADING_MODE=PAPER"
echo ""
echo "  2. Or export them:"
echo "     export UW_API_KEY=your_key"
echo "     export ALPACA_KEY=your_key"
echo "     export ALPACA_SECRET=your_secret"
echo ""
echo "  3. Then restart supervisor:"
echo "     pkill -f deploy_supervisor"
echo "     screen -dmS supervisor bash -c 'cd ~/stock-bot && source venv/bin/activate && python deploy_supervisor.py'"
echo ""
