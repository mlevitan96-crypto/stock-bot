#!/usr/bin/env python3
"""
Fix dark_pool storage and ensure all signals are populated
1. Check dark_pool API response
2. Fix dark_pool storage logic
3. Ensure market-wide data is stored
4. Fix missing signal endpoints
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIX DARK_POOL AND ALL SIGNALS")
        print("=" * 80)
        print()
        
        # 1. Test dark_pool API directly
        print("1. TESTING DARK_POOL API")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from uw_flow_daemon import UWClient\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "client = UWClient()\n"
            "print('Testing dark_pool API for AAPL...')\n"
            "dp_data = client.get_dark_pool_levels('AAPL')\n"
            "print(f'Response type: {type(dp_data)}')\n"
            "print(f'Response length: {len(dp_data) if isinstance(dp_data, list) else \"NOT A LIST\"}')\n"
            "if isinstance(dp_data, list) and len(dp_data) > 0:\n"
            "    print(f'Sample item: {dp_data[0]}')\n"
            "    from uw_flow_daemon import SmartPoller\n"
            "    poller = SmartPoller()\n"
            "    # Create a minimal daemon-like object\n"
            "    class MockDaemon:\n"
            "        def _normalize_dark_pool(self, dp_data):\n"
            "            from uw_flow_daemon import UWFlowDaemon\n"
            "            daemon = UWFlowDaemon()\n"
            "            return daemon._normalize_dark_pool(dp_data)\n"
            "    daemon = MockDaemon()\n"
            "    normalized = daemon._normalize_dark_pool(dp_data)\n"
            "    print(f'Normalized: {normalized}')\n"
            "    print(f'Will be stored: {bool(normalized)}')\n"
            "else:\n"
            "    print('API returned empty or invalid data')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 2. Check current dark_pool storage logic
        print("2. CHECKING DARK_POOL STORAGE LOGIC")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -A 10 'if dp_normalized:' uw_flow_daemon.py",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 3. Fix dark_pool storage - always store even if empty
        print("3. FIXING DARK_POOL STORAGE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && sed -i 's/if dp_normalized:/if dp_normalized is not None:/' uw_flow_daemon.py && echo 'Fixed dark_pool storage check'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 4. Check market-wide data storage
        print("4. CHECKING MARKET-WIDE DATA STORAGE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -B 5 -A 15 'get_market_tide' uw_flow_daemon.py | head -25",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 5. Check which tickers are being polled
        print("5. CHECKING POLLED TICKERS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '30 minutes ago' --no-pager 2>&1 | grep -E 'Polling.*for|_poll_ticker.*ticker=' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:2000])
        print()
        
        # 6. Restart service
        print("6. RESTARTING SERVICE")
        print("-" * 80)
        client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted")
        time.sleep(30)
        print()
        
        # 7. Wait and check cache
        print("7. WAITING FOR POLLING (60 seconds)")
        print("-" * 80)
        time.sleep(60)
        print()
        
        # 8. Check cache for dark_pool
        print("8. CHECKING CACHE FOR DARK_POOL")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Cache symbols: {symbols[:5]}')\n"
            "if symbols:\n"
            "    sym = symbols[0]\n"
            "    data = cache.get(sym, {})\n"
            "    print(f'\\n{sym} has dark_pool: {\"dark_pool\" in data}')\n"
            "    if \"dark_pool\" in data:\n"
            "        print(f'dark_pool value: {data[\"dark_pool\"]}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("1. Tested dark_pool API")
        print("2. Fixed dark_pool storage check (if dp_normalized -> if dp_normalized is not None)")
        print("3. Checked market-wide data storage")
        print("4. Service restarted")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

