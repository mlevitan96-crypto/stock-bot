#!/usr/bin/env python3
"""
Check actual API responses from daemon logs
"""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("CHECKING ACTUAL API RESPONSES FROM LOGS")
        print("=" * 80)
        print()
        
        # 1. Check dark_pool API responses
        print("1. DARK_POOL API RESPONSES")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '2 hours ago' --no-pager 2>&1 | grep -E 'darkpool|dark_pool|Polling dark_pool' | grep -E 'API call|data_type|data_keys|Updated dark_pool|dark_pool.*returned' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:5000])
        print()
        
        # 2. Check what dark_pool data looks like when stored
        print("2. DARK_POOL STORAGE EVENTS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '2 hours ago' --no-pager 2>&1 | grep -E 'dark_pool|darkpool' | grep -E 'Updated|normalized|_update_cache' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:3000])
        print()
        
        # 3. Check recent successful API calls
        print("3. RECENT SUCCESSFUL API CALLS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '2 hours ago' --no-pager 2>&1 | grep 'API call success' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:4000])
        print()
        
        # 4. Check for empty responses
        print("4. EMPTY API RESPONSES")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '2 hours ago' --no-pager 2>&1 | grep -E 'API returned empty|has_data.*false|data_type.*list.*list_len.*0' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:4000])
        print()
        
        # 5. Check actual cache content for dark_pool
        print("5. ACTUAL CACHE CONTENT - DARK_POOL")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import json\n"
            "from pathlib import Path\n"
            "cache_path = Path('data/uw_flow_cache.json')\n"
            "if cache_path.exists():\n"
            "    cache = json.loads(cache_path.read_text())\n"
            "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "    if symbols:\n"
            "        sym = symbols[0]\n"
            "        data = cache.get(sym, {})\n"
            "        dp = data.get('dark_pool', {})\n"
            "        print(f'{sym} dark_pool:')\n"
            "        print(f'  Type: {type(dp)}')\n"
            "        print(f'  Value: {dp}')\n"
            "        print(f'  Keys: {list(dp.keys()) if isinstance(dp, dict) else \"NOT A DICT\"}')\n"
            "        if isinstance(dp, dict):\n"
            "            print(f'  total_premium: {dp.get(\"total_premium\", \"MISSING\")}')\n"
            "            print(f'  print_count: {dp.get(\"print_count\", \"MISSING\")}')\n"
            "            print(f'  sentiment: {dp.get(\"sentiment\", \"MISSING\")}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
    except Exception as e:
        print(f"[ERROR] Check failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

