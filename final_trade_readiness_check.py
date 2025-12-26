#!/usr/bin/env python3
"""
Final Trade Readiness Check - Comprehensive verification
"""

from droplet_client import DropletClient
import json

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FINAL TRADE READINESS CHECK")
        print("=" * 80)
        print()
        
        # 1. Check cache file path
        print("1. CACHE FILE PATH CHECK")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import CacheFiles\n"
            "from pathlib import Path\n"
            "cache_path = CacheFiles.UW_FLOW_CACHE\n"
            "print(f'Registry cache path: {cache_path}')\n"
            "print(f'Path exists: {cache_path.exists()}')\n"
            "print(f'Absolute path: {cache_path.absolute()}')\n"
            "# Also check data/uw_flow_cache.json directly\n"
            "direct_path = Path('data/uw_flow_cache.json')\n"
            "print(f'Direct path exists: {direct_path.exists()}')\n"
            "if direct_path.exists():\n"
            "    import json\n"
            "    cache = json.load(open(direct_path))\n"
            "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "    print(f'Symbols in direct path: {len(symbols)}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 2. Check market status
        print("2. MARKET STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "import alpaca_trade_api as tradeapi\n"
            "api = tradeapi.REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_API_SECRET'), os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'), api_version='v2')\n"
            "clock = api.get_clock()\n"
            "print(f'Market is_open: {clock.is_open}')\n"
            "print(f'Next open: {clock.next_open}')\n"
            "print(f'Next close: {clock.next_close}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 3. Check if main.py can read cache
        print("3. MAIN.PY CACHE ACCESS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "print(f'read_uw_cache() returned: {len(cache)} symbols')\n"
            "if cache:\n"
            "    print(f'Sample keys: {list(cache.keys())[:5]}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 4. Check recent run cycles
        print("4. RECENT RUN CYCLES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -5 logs/run.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            e = json.loads(line)\n"
            "            print(f\"{e.get('ts', 'unknown')}: market_open={e.get('market_open', 'unknown')}, clusters={e.get('clusters', 0)}, orders={e.get('orders', 0)}\")\n"
            "        except:\n"
            "            pass\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 5. Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("Key checks:")
        print("1. Cache file path must match registry")
        print("2. Market must be open (Alpaca clock)")
        print("3. read_uw_cache() must return symbols")
        print("4. Recent cycles should show market_open=true and clusters > 0")
        print()
        
    except Exception as e:
        print(f"[ERROR] Check failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

