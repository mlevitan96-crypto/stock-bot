#!/usr/bin/env python3
"""
Fix Cluster Generation - Ensure clusters are generated even with minimal cache data
"""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIXING CLUSTER GENERATION")
        print("=" * 80)
        print()
        
        # 1. Check cache structure
        print("1. CACHE STRUCTURE CHECK")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import json\n"
            "with open('data/uw_flow_cache.json') as f:\n"
            "    cache = json.load(f)\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Symbols: {len(symbols)}')\n"
            "for sym in symbols[:3]:\n"
            "    data = cache.get(sym, {})\n"
            "    print(f'\\n{sym}:')\n"
            "    print(f'  Keys: {list(data.keys())}')\n"
            "    print(f'  Has flow_trades: {\"flow_trades\" in data}')\n"
            "    if 'flow_trades' in data:\n"
            "        print(f'  flow_trades count: {len(data[\"flow_trades\"]) if isinstance(data[\"flow_trades\"], list) else \"not list\"}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 2. Check why daemon isn't populating flow_trades
        print("2. DAEMON FLOW_TRADES POPULATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -100 logs/uw_flow_daemon.log 2>&1 | grep -E 'flow_trades|option_flow|Retrieved|Stored' | tail -20",
            timeout=10
        )
        print(result['stdout'][:2000] if result['stdout'] else 'No flow_trades activity')
        print()
        
        # 3. Check Config.TICKERS
        print("3. CONFIG TICKERS CHECK")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import Config\n"
            "print(f'TICKERS: {Config.TICKERS[:10]}')\n"
            "print(f'Total tickers: {len(Config.TICKERS)}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 4. Check if composite mode should be enabled
        print("4. COMPOSITE MODE CHECK")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "use_composite = len(cache) > 0\n"
            "print(f'Cache symbols: {len(symbols)}')\n"
            "print(f'use_composite should be: {use_composite}')\n"
            "print(f'Cache keys: {list(cache.keys())[:10]}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 5. Check recent run logs for composite_enabled
        print("5. RECENT RUN LOGS - COMPOSITE STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -10 logs/run.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            c = json.loads(line)\n"
            "            metrics = c.get('metrics', {})\n"
            "            composite = metrics.get('composite_enabled', 'unknown')\n"
            "            clusters = c.get('clusters', 0)\n"
            "            print(f'composite_enabled={composite}, clusters={clusters}')\n"
            "        except:\n"
            "            pass\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'] if result['stdout'] else 'No logs')
        print()
        
        print("=" * 80)
        print("DIAGNOSIS COMPLETE")
        print("=" * 80)
        print("Check output above to identify why clusters are 0")
        print()
        
    except Exception as e:
        print(f"[ERROR] Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

