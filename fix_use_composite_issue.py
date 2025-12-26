#!/usr/bin/env python3
"""Fix use_composite issue - ensure it's True when cache has data."""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIXING USE_COMPOSITE ISSUE")
        print("=" * 80)
        print()
        
        # 1. Check what read_uw_cache actually returns
        print("1. TESTING read_uw_cache()")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "print(f'Cache returned: len={len(cache)}')\n"
            "print(f'Keys: {list(cache.keys())[:10]}')\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Symbols: {len(symbols)}')\n"
            "print(f'use_composite would be: {len(cache) > 0}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 2. Check cache file directly
        print("2. CACHE FILE DIRECT")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import json\n"
            "from pathlib import Path\n"
            "cache_file = Path('data/uw_flow_cache.json')\n"
            "if cache_file.exists():\n"
            "    cache = json.loads(cache_file.read_text())\n"
            "    print(f'Direct read: len={len(cache)}')\n"
            "    print(f'Keys: {list(cache.keys())[:10]}')\n"
            "else:\n"
            "    print('Cache file does not exist')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 3. Check if there's a timing issue (cache being cleared)
        print("3. CHECKING FOR CACHE CLEARING")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -r 'uw_flow_cache.*clear\\|uw_flow_cache.*delete\\|uw_flow_cache.*remove\\|uw_flow_cache.*=.*\\{\\}' main.py uw_flow_daemon.py 2>&1 | head -10",
            timeout=10
        )
        print(result['stdout'][:1000] if result['stdout'] else 'No cache clearing found')
        print()
        
        # 4. Check recent main.py logs for cache read
        print("4. RECENT MAIN.PY LOGS - CACHE READ")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && journalctl -u trading-bot.service --since '5 minutes ago' --no-pager 2>&1 | grep -E 'cache|read_uw_cache|use_composite|composite_enabled' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:2000])
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

