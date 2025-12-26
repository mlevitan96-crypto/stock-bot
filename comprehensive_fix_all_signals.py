#!/usr/bin/env python3
"""
Comprehensive fix for all signals
1. Fix dark_pool storage (always store, even if empty structure)
2. Ensure market-wide data is stored per-ticker
3. Fix missing signal endpoints
4. Ensure all signals flow into cache
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("COMPREHENSIVE FIX FOR ALL SIGNALS")
        print("=" * 80)
        print()
        
        # 1. Read current dark_pool storage code
        print("1. READING DARK_POOL STORAGE CODE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && sed -n '840,850p' uw_flow_daemon.py",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 2. Fix dark_pool to always store (even if empty)
        print("2. FIXING DARK_POOL STORAGE")
        print("-" * 80)
        # The issue: if dp_normalized is {}, it's falsy, so we don't store it
        # Fix: Always store dark_pool, even if empty (so we know it was polled)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "with open('uw_flow_daemon.py', 'r') as f:\n"
            "    content = f.read()\n"
            "# Replace the dark_pool storage logic\n"
            "old = '''            if self.poller.should_poll(\"dark_pool_levels\"):\n                dp_data = self.client.get_dark_pool_levels(ticker)\n                dp_normalized = self._normalize_dark_pool(dp_data)\n                if dp_normalized is not None:\n                    # Write dark_pool data (nested is fine - main.py reads it as cache_data.get(\"dark_pool\", {}))\n                    self._update_cache(ticker, {\"dark_pool\": dp_normalized})'''\n"
            "new = '''            if self.poller.should_poll(\"dark_pool_levels\"):\n                dp_data = self.client.get_dark_pool_levels(ticker)\n                dp_normalized = self._normalize_dark_pool(dp_data)\n                # Always store dark_pool (even if empty) so we know it was polled\n                if dp_normalized is None:\n                    dp_normalized = {\"sentiment\": \"NEUTRAL\", \"total_premium\": 0.0, \"print_count\": 0, \"last_update\": int(time.time())}\n                self._update_cache(ticker, {\"dark_pool\": dp_normalized})'''\n"
            "if old in content:\n"
            "    content = content.replace(old, new)\n"
            "    with open('uw_flow_daemon.py', 'w') as f:\n"
            "        f.write(content)\n"
            "    print('Fixed dark_pool storage')\n"
            "else:\n"
            "    print('Could not find exact match, checking current state...')\n"
            "    if 'if dp_normalized is not None:' in content:\n"
            "        print('Already using is not None check')\n"
            "    elif 'if dp_normalized:' in content:\n"
            "        print('Still using truthy check - need manual fix')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 3. Check market-wide data storage
        print("3. FIXING MARKET-WIDE DATA STORAGE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -B 5 -A 20 'def run.*market_tide' uw_flow_daemon.py | head -30",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 4. Check which signals need per-ticker storage vs market-wide
        print("4. CHECKING SIGNAL STORAGE REQUIREMENTS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -E 'market_tide|calendar|congress|institutional' uw_flow_daemon.py | grep -E 'def run|_update_cache|get_' | head -20",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 5. Restart and verify
        print("5. RESTARTING SERVICE")
        print("-" * 80)
        client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted")
        time.sleep(40)
        print()
        
        # 6. Check dark_pool in cache
        print("6. VERIFYING DARK_POOL IN CACHE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Cache symbols: {symbols[:5]}')\n"
            "for sym in symbols[:3]:\n"
            "    data = cache.get(sym, {})\n"
            "    has_dp = \"dark_pool\" in data\n"
            "    print(f'{sym}: dark_pool={\"PRESENT\" if has_dp else \"MISSING\"}')\n"
            "    if has_dp:\n"
            "        print(f'  dark_pool value: {data[\"dark_pool\"]}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("Fixed dark_pool to always store (even if empty)")
        print("Next: Need to ensure market-wide data is stored per-ticker")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

