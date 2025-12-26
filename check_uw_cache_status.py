#!/usr/bin/env python3
"""Check UW cache status on droplet."""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("Checking UW daemon and cache status...")
        print()
        
        # Check daemon process
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        if result['stdout'].strip():
            print("[OK] UW daemon is running")
            print(f"  {result['stdout'].strip()[:100]}")
        else:
            print("[FAIL] UW daemon not running")
        print()
        
        # Check cache file
        result = client.execute_command("cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1", timeout=10)
        if "No such file" not in result['stdout']:
            print("[OK] Cache file exists")
            print(f"  {result['stdout'].strip()}")
            
            # Check cache content
            result2 = client.execute_command(
                "cd ~/stock-bot && python3 << 'PYEOF'\n"
                "import json\n"
                "try:\n"
                "    with open('data/uw_flow_cache.json') as f:\n"
                "        cache = json.load(f)\n"
                "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
                "    print(f'Symbols in cache: {len(symbols)}')\n"
                "    if symbols:\n"
                "        print(f'Sample symbols: {symbols[:5]}')\n"
                "    cache_time = cache.get('_cache_timestamp', 'unknown')\n"
                "    print(f'Cache timestamp: {cache_time}')\n"
                "except Exception as e:\n"
                "    print(f'Error reading cache: {e}')\n"
                "PYEOF",
                timeout=30
            )
            if result2['stdout']:
                print(f"  {result2['stdout']}")
        else:
            print("[FAIL] Cache file does not exist")
            print("  Waiting 30 seconds for daemon to create cache...")
            time.sleep(30)
            
            # Check again
            result = client.execute_command("cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1", timeout=10)
            if "No such file" not in result['stdout']:
                print("[OK] Cache file created!")
                print(f"  {result['stdout'].strip()}")
            else:
                print("[WARNING] Cache file still not created after 30 seconds")
                print("  Checking daemon logs...")
                result_logs = client.execute_command("cd ~/stock-bot && tail -30 logs/uw_flow_daemon.log 2>&1", timeout=10)
                if result_logs['stdout']:
                    print(f"  {result_logs['stdout'][:1000]}")
        print()
        
        # Check recent daemon activity
        result = client.execute_command("cd ~/stock-bot && tail -15 logs/uw_flow_daemon.log 2>&1", timeout=10)
        if result['stdout']:
            print("Recent daemon activity:")
            print(result['stdout'][:600])
        
    except Exception as e:
        print(f"[ERROR] Check failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()

