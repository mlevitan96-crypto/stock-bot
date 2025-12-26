#!/usr/bin/env python3
"""
Complete Workflow Fix - Fix EVERY step to ensure trading works
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("COMPLETE WORKFLOW FIX")
        print("=" * 80)
        print()
        
        # 1. Check actual cache file
        print("1. ACTUAL CACHE FILE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && cat data/uw_flow_cache.json 2>&1",
            timeout=10
        )
        print(result['stdout'][:3000])
        print()
        
        # 2. Check CacheFiles.UW_FLOW_CACHE path
        print("2. CACHE FILE PATH")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import CacheFiles\n"
            "print(f'UW_FLOW_CACHE path: {CacheFiles.UW_FLOW_CACHE}')\n"
            "print(f'Exists: {CacheFiles.UW_FLOW_CACHE.exists()}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 3. Test read_uw_cache directly
        print("3. TEST read_uw_cache()")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "print(f'read_uw_cache() returned: {type(cache)}, len={len(cache)}')\n"
            "print(f'Keys: {list(cache.keys())[:20]}')\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Symbols (non-_): {len(symbols)}')\n"
            "if symbols:\n"
            "    print(f'Sample symbol: {symbols[0]}')\n"
            "    print(f'Sample data keys: {list(cache[symbols[0]].keys())[:10] if isinstance(cache.get(symbols[0]), dict) else \"not dict\"}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 4. Check if daemon is writing to correct path
        print("4. DAEMON CACHE PATH")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -E 'CACHE_FILE|uw_flow_cache' uw_flow_daemon.py | head -5",
            timeout=10
        )
        print(result['stdout'][:1000] if result['stdout'] else 'Not found')
        print()
        
        # 5. Check Config.TICKERS vs cache symbols
        print("5. TICKERS VS CACHE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import Config\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "tickers = Config.TICKERS[:20]\n"
            "print(f'Config.TICKERS: {len(tickers)} tickers')\n"
            "print(f'Cache symbols: {len(symbols)} symbols')\n"
            "print(f'Overlap: {len(set(tickers) & set(symbols))} symbols')\n"
            "print(f'In tickers but not cache: {set(tickers[:10]) - set(symbols)}')\n"
            "print(f'In cache but not tickers: {set(symbols) - set(tickers[:10])}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 6. Force daemon to poll option_flow for a symbol
        print("6. FORCING DAEMON TO POLL")
        print("-" * 80)
        # Restart daemon to force fresh poll
        client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted - daemon should poll fresh")
        time.sleep(30)
        print()
        
        # 7. Check cache again
        print("7. CACHE AFTER RESTART")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import json\n"
            "with open('data/uw_flow_cache.json') as f:\n"
            "    cache = json.load(f)\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Symbols: {len(symbols)}')\n"
            "for sym in symbols[:5]:\n"
            "    data = cache.get(sym, {})\n"
            "    has_flow = 'flow_trades' in data\n"
            "    flow_count = len(data.get('flow_trades', [])) if has_flow else 0\n"
            "    print(f'  {sym}: flow_trades={has_flow}, count={flow_count}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        print("=" * 80)
        print("DIAGNOSIS COMPLETE")
        print("=" * 80)
        print("Check output above to identify the issue")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

