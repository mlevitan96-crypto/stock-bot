#!/usr/bin/env python3
"""
Complete trade flow diagnosis - trace every step from signal to execution
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("COMPLETE TRADE FLOW DIAGNOSIS")
        print("=" * 80)
        print()
        
        # 1. Check if main.py is running
        print("1. MAIN.PY PROCESS STATUS")
        print("-" * 80)
        result = client.execute_command(
            "pgrep -af 'main.py' | grep -v grep || echo 'main.py NOT RUNNING'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 2. Check recent main.py activity
        print("2. RECENT MAIN.PY ACTIVITY")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '30 minutes ago' --no-pager 2>&1 | grep -E 'run_once|decide_and_execute|Composite score|threshold|gate|Order submitted|Position opened' | tail -50",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:6000])
        print()
        
        # 3. Check cache status - do we have data?
        print("3. CACHE DATA STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Cache symbols: {len(symbols)}')\n"
            "print(f'Symbols: {symbols[:10]}')\n"
            "if symbols:\n"
            "    sym = symbols[0]\n"
            "    data = cache.get(sym, {})\n"
            "    print(f'\\n{sym} has:')\n"
            "    print(f'  flow_trades: {bool(data.get(\"flow_trades\"))}')\n"
            "    print(f'  dark_pool: {bool(data.get(\"dark_pool\"))}')\n"
            "    print(f'  market_tide: {bool(data.get(\"market_tide\"))}')\n"
            "    print(f'  insider: {bool(data.get(\"insider\"))}')\n"
            "    print(f'  greeks: {bool(data.get(\"greeks\"))}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 4. Check if clusters are being generated
        print("4. CLUSTER GENERATION")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '30 minutes ago' --no-pager 2>&1 | grep -E 'clusters|cluster_signals|flow_clusters|filtered_clusters|Generated.*clusters' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:4000])
        print()
        
        # 5. Check composite scores
        print("5. COMPOSITE SCORES")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '30 minutes ago' --no-pager 2>&1 | grep -E 'Composite score|composite_score|score.*threshold|ENTRY_THRESHOLD' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:4000])
        print()
        
        # 6. Check gates - what's blocking trades?
        print("6. TRADE GATES - WHAT'S BLOCKING?")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '30 minutes ago' --no-pager 2>&1 | grep -E 'gate|blocked|rejected|halted|freeze|max_positions|can_open' | tail -40",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:5000])
        print()
        
        # 7. Check market status
        print("7. MARKET STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from alpaca.trading.client import TradingClient\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "api_key = os.getenv('ALPACA_API_KEY')\n"
            "api_secret = os.getenv('ALPACA_API_SECRET')\n"
            "client = TradingClient(api_key, api_secret, paper=True)\n"
            "clock = client.get_clock()\n"
            "print(f'Market is_open: {clock.is_open}')\n"
            "print(f'Market next_open: {clock.next_open}')\n"
            "print(f'Market next_close: {clock.next_close}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 8. Check current positions
        print("8. CURRENT POSITIONS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from alpaca.trading.client import TradingClient\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "api_key = os.getenv('ALPACA_API_KEY')\n"
            "api_secret = os.getenv('ALPACA_API_SECRET')\n"
            "client = TradingClient(api_key, api_secret, paper=True)\n"
            "positions = client.get_all_positions()\n"
            "print(f'Current positions: {len(positions)}')\n"
            "for pos in positions:\n"
            "    print(f'  {pos.symbol}: {pos.qty} @ {pos.avg_entry_price}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 9. Check max positions config
        print("9. MAX POSITIONS CONFIG")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -E 'MAX_CONCURRENT_POSITIONS|max_positions' config/*.py main.py | head -10",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 10. Check freeze state
        print("10. FREEZE STATE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && ls -la state/*freeze* 2>/dev/null || echo 'No freeze files'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 11. Check recent run_once calls
        print("11. RUN_ONCE EXECUTION")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '1 hour ago' --no-pager 2>&1 | grep -E 'run_once|Starting.*cycle|Completed.*cycle' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:3000])
        print()
        
        # 12. Check for errors
        print("12. ERRORS IN MAIN.PY")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '1 hour ago' --no-pager 2>&1 | grep -E 'ERROR|Exception|Traceback|Failed|failed' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:5000])
        print()
        
        print("=" * 80)
        print("DIAGNOSIS SUMMARY")
        print("=" * 80)
        print("Checked:")
        print("1. Is main.py running?")
        print("2. Is cache populated?")
        print("3. Are clusters generated?")
        print("4. Are scores calculated?")
        print("5. What gates are blocking?")
        print("6. Is market open?")
        print("7. Current positions?")
        print("8. Max positions config?")
        print("9. Freeze state?")
        print("10. Is run_once executing?")
        print("11. Any errors?")
        print()
        
    except Exception as e:
        print(f"[ERROR] Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

