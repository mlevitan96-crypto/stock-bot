#!/bin/bash
cd ~/stock-bot
source venv/bin/activate
python3 -c "
from alpaca_trade_api import REST
import os
from dotenv import load_dotenv
load_dotenv()
api = REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), os.getenv('ALPACA_BASE_URL'), api_version='v2')
pos = api.list_positions()
print(f'Alpaca positions: {len(pos)}')
for p in pos:
    print(f'  {p.symbol}: {p.qty} shares @ ${float(p.avg_entry_price):.2f}')
"
