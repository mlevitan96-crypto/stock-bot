#!/bin/bash
# Check actual Alpaca positions vs bot metadata

cd ~/stock-bot
source venv/bin/activate

echo "=== ACTUAL ALPACA POSITIONS ==="
python3 << 'PYEOF'
from alpaca_trade_api import REST
import os
from dotenv import load_dotenv
load_dotenv()

api = REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), os.getenv('ALPACA_BASE_URL'), api_version='v2')
positions = api.list_positions()
print(f"ACTUAL POSITIONS: {len(positions)}")
for p in positions:
    print(f"  - {p.symbol}: {p.qty} shares")
PYEOF

echo ""
echo "=== BOT'S METADATA ==="
python3 << 'PYEOF'
import json
with open('state/position_metadata.json') as f:
    d = json.load(f)
    positions = {k:v for k,v in d.items() if not k.startswith('_')}
    print(f"BOT METADATA: {len(positions)} positions")
    for symbol in positions.keys():
        print(f"  - {symbol}")
PYEOF
