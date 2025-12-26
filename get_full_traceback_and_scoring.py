#!/usr/bin/env python3
"""
Get full traceback errors and detailed scoring breakdown
"""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FULL TRACEBACK AND SCORING ANALYSIS")
        print("=" * 80)
        print()
        
        # 1. Get full traceback for one error
        print("1. FULL TRACEBACK FOR SPY/QQQ")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '30 minutes ago' --no-pager 2>&1 | grep -A 20 'DEBUG SPY: Traceback' | head -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:6000])
        print()
        
        # 2. Check what components are contributing to scores
        print("2. SCORING COMPONENT BREAKDOWN")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '30 minutes ago' --no-pager 2>&1 | grep -E 'compute_composite|component|dark_pool.*component|insider.*component|market_tide.*component' | tail -50",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:6000])
        print()
        
        # 3. Check actual scoring calculation for AAPL
        print("3. DETAILED SCORING FOR AAPL")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "from uw_composite_v2 import compute_composite_score_v3, get_threshold\n"
            "cache = read_uw_cache()\n"
            "symbol = 'AAPL'\n"
            "data = cache.get(symbol, {})\n"
            "print(f'Computing composite score for {symbol}...')\n"
            "print(f'Has flow_trades: {bool(data.get(\"flow_trades\"))}')\n"
            "print(f'Has dark_pool: {bool(data.get(\"dark_pool\"))}')\n"
            "print(f'Has market_tide: {bool(data.get(\"market_tide\"))}')\n"
            "print(f'Has insider: {bool(data.get(\"insider\"))}')\n"
            "print(f'Has greeks: {bool(data.get(\"greeks\"))}')\n"
            "try:\n"
            "    result = compute_composite_score_v3(symbol, data, 'mixed')\n"
            "    print(f'\\nComposite score: {result.get(\"score\", \"MISSING\")}')\n"
            "    print(f'Threshold: {get_threshold(\"bootstrap\")}')\n"
            "    print(f'\\nComponent breakdown:')\n"
            "    if 'components' in result:\n"
            "        for comp, val in result['components'].items():\n"
            "            print(f'  {comp}: {val}')\n"
            "except Exception as e:\n"
            "    print(f'ERROR computing score: {e}')\n"
            "    import traceback\n"
            "    traceback.print_exc()\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 4. Check what gates are blocking after score check
        print("4. GATES BLOCKING AFTER SCORE CHECK")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '30 minutes ago' --no-pager 2>&1 | grep -E 'BLOCKED|REJECTED|gate.*fail|can_open|max_positions|expectancy.*fail|toxicity|regime.*block' | tail -40",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:5000])
        print()
        
        # 5. Check dark_pool data structure
        print("5. DARK_POOL DATA STRUCTURE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbol = 'AAPL'\n"
            "data = cache.get(symbol, {})\n"
            "dp = data.get('dark_pool', {})\n"
            "print(f'{symbol} dark_pool:')\n"
            "print(f'  Type: {type(dp)}')\n"
            "print(f'  Value: {dp}')\n"
            "print(f'  Keys: {list(dp.keys()) if isinstance(dp, dict) else \"NOT A DICT\"}')\n"
            "if isinstance(dp, dict):\n"
            "    print(f'  total_premium: {dp.get(\"total_premium\", \"MISSING\")}')\n"
            "    print(f'  print_count: {dp.get(\"print_count\", \"MISSING\")}')\n"
            "    print(f'  sentiment: {dp.get(\"sentiment\", \"MISSING\")}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

