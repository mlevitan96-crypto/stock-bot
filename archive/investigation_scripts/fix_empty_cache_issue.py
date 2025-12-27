#!/usr/bin/env python3
"""
Fix Empty Cache Issue - Comprehensive diagnosis and fix
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIXING EMPTY CACHE ISSUE")
        print("=" * 80)
        print()
        
        # 1. Check cache file directly
        print("1. CHECKING CACHE FILE DIRECTLY")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from pathlib import Path\n"
            "import json\n"
            "cache_path = Path('data/uw_flow_cache.json')\n"
            "print(f'Cache path: {cache_path.absolute()}')\n"
            "print(f'Exists: {cache_path.exists()}')\n"
            "if cache_path.exists():\n"
            "    print(f'Size: {cache_path.stat().st_size} bytes')\n"
            "    try:\n"
            "        cache = json.load(open(cache_path))\n"
            "        all_keys = list(cache.keys())\n"
            "        symbols = [k for k in all_keys if not k.startswith('_')]\n"
            "        metadata_keys = [k for k in all_keys if k.startswith('_')]\n"
            "        print(f'Total keys: {len(all_keys)}')\n"
            "        print(f'Symbol keys: {len(symbols)}')\n"
            "        print(f'Metadata keys: {len(metadata_keys)}')\n"
            "        print(f'Symbols: {symbols[:20]}')\n"
            "        print(f'Metadata: {metadata_keys}')\n"
            "        if symbols:\n"
            "            sample = symbols[0]\n"
            "            data = cache.get(sample, {})\n"
            "            print(f'\\nSample symbol ({sample}) keys: {list(data.keys())[:15]}')\n"
            "    except Exception as e:\n"
            "        print(f'Error reading cache: {e}')\n"
            "        import traceback\n"
            "        traceback.print_exc()\n"
            "else:\n"
            "    print('Cache file does not exist')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 2. Check registry path
        print("2. CHECKING REGISTRY PATH")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import CacheFiles\n"
            "cache_path = CacheFiles.UW_FLOW_CACHE\n"
            "print(f'Registry path: {cache_path}')\n"
            "print(f'Absolute: {cache_path.absolute()}')\n"
            "print(f'Exists: {cache_path.exists()}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 3. Check daemon status and logs
        print("3. CHECKING DAEMON STATUS")
        print("-" * 80)
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        print("Daemon process:")
        print(result['stdout'] if result['stdout'] else 'NOT RUNNING')
        print()
        
        # 4. Check daemon logs for cache writes
        print("4. CHECKING DAEMON LOGS FOR CACHE WRITES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -200 logs/uw_flow_daemon.log 2>&1 | grep -E 'Cache update|atomic_write|_update_cache|Polling.*AAPL|LOOP ENTERED|SUCCESS' | tail -30",
            timeout=30
        )
        output = result['stdout'] if result['stdout'] else 'No cache write activity found'
        # Remove Unicode characters for Windows compatibility
        output = output.encode('ascii', 'ignore').decode('ascii')
        print(output[:2000])
        print()
        
        # 5. Restart daemon if needed
        print("5. RESTARTING DAEMON TO ENSURE CACHE POPULATION")
        print("-" * 80)
        client.execute_command("pkill -f uw_flow_daemon", timeout=10)
        time.sleep(2)
        result = client.execute_command(
            "cd ~/stock-bot && nohup venv/bin/python3 uw_flow_daemon.py > logs/uw_flow_daemon.log 2>&1 &",
            timeout=10
        )
        print("[OK] Daemon restart command executed")
        time.sleep(5)
        
        # Verify daemon is running
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        if result['stdout'].strip():
            print("[OK] Daemon is running")
        else:
            print("[FAIL] Daemon not running after restart")
        print()
        
        # 6. Wait and check cache again
        print("6. WAITING FOR CACHE TO POPULATE (90 seconds)")
        print("-" * 80)
        print("Waiting 90 seconds for daemon to poll tickers...")
        time.sleep(90)
        
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from pathlib import Path\n"
            "import json\n"
            "cache_path = Path('data/uw_flow_cache.json')\n"
            "if cache_path.exists():\n"
            "    cache = json.load(open(cache_path))\n"
            "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "    print(f'Cache symbols after wait: {len(symbols)}')\n"
            "    if symbols:\n"
            "        print(f'Sample: {symbols[:10]}')\n"
            "        if 'AAPL' in symbols:\n"
            "            aapl_data = cache['AAPL']\n"
            "            print(f'AAPL keys: {list(aapl_data.keys())[:15]}')\n"
            "else:\n"
            "    print('Cache file still does not exist')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 7. Check if main.py can now read it
        print("7. VERIFYING MAIN.PY CAN READ CACHE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'read_uw_cache() returns: {len(symbols)} symbols')\n"
            "if symbols:\n"
            "    print(f'Sample: {symbols[:10]}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("If cache has symbols, trades should start executing.")
        print("If cache is still empty, check daemon logs for errors.")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

