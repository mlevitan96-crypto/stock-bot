#!/bin/bash
# Clear risk management freeze to allow trading to resume

cd /root/stock-bot

echo "=========================================="
echo "CLEARING RISK MANAGEMENT FREEZE"
echo "=========================================="

# Check current freeze state
if [ -f "state/governor_freezes.json" ]; then
    echo "Current freeze state:"
    cat state/governor_freezes.json | python3 -m json.tool 2>/dev/null || cat state/governor_freezes.json
    echo ""
fi

# Check peak equity
if [ -f "state/peak_equity.json" ]; then
    echo "Current peak equity:"
    cat state/peak_equity.json | python3 -m json.tool 2>/dev/null || cat state/peak_equity.json
    echo ""
fi

# Check current account equity
echo "Checking current account equity from Alpaca..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
import alpaca_trade_api as tradeapi
api = tradeapi.REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), 'https://paper-api.alpaca.markets')
account = api.get_account()
current_equity = float(account.equity)
print(f'Current equity: \${current_equity:,.2f}')
"

echo ""
echo "=========================================="
echo "OPTIONS TO CLEAR FREEZE:"
echo "=========================================="
echo ""
echo "Option 1: Clear ALL freezes (recommended for testing)"
echo "  rm -f state/governor_freezes.json"
echo ""
echo "Option 2: Reset peak equity (if drawdown is false positive)"
echo "  python3 -c \""
echo "  from pathlib import Path"
echo "  import json"
echo "  import alpaca_trade_api as tradeapi"
echo "  from dotenv import load_dotenv"
echo "  load_dotenv()"
echo "  api = tradeapi.REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), 'https://paper-api.alpaca.markets')"
echo "  account = api.get_account()"
echo "  current_equity = float(account.equity)"
echo "  Path('state/peak_equity.json').write_text(json.dumps({'peak_equity': current_equity, 'timestamp': '$(date -u +%Y-%m-%dT%H:%M:%SZ)'}))"
echo "  print('Peak equity reset to current equity')"
echo "  \""
echo ""
echo "Option 3: Manual edit (edit state/governor_freezes.json and set all to false)"
echo ""
echo "=========================================="
echo "QUICK FIX (clears all freezes):"
echo "=========================================="
echo ""
echo "Run this command to clear the freeze:"
echo "  rm -f state/governor_freezes.json && echo '✅ Freeze cleared'"
echo ""
