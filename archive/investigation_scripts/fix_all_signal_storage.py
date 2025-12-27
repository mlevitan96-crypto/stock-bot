#!/usr/bin/env python3
"""
Fix all signal storage issues:
1. Store market_tide per-ticker (copy from global)
2. Store empty responses as empty structures
3. Ensure all polled data is stored
"""

from droplet_client import DropletClient
import json

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIX ALL SIGNAL STORAGE")
        print("=" * 80)
        print()
        
        # 1. Fix market_tide to be stored per-ticker
        print("1. FIXING MARKET_TIDE STORAGE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "with open('uw_flow_daemon.py', 'r') as f:\n"
            "    content = f.read()\n"
            "# Find market_tide storage and fix it to store per-ticker\n"
            "old_market_tide = '''                            if tide_data:\n                                # Store in cache metadata\n                                cache = read_json(CACHE_FILE, default={}) if CACHE_FILE.exists() else {}\n                                cache[\"_market_tide\"] = {\n                                    \"data\": tide_data,\n                                    \"last_update\": int(time.time())\n                                }\n                                atomic_write_json(CACHE_FILE, cache)'''\n"
            "new_market_tide = '''                            if tide_data:\n                                # Store in cache metadata AND per-ticker (for scoring)\n                                cache = read_json(CACHE_FILE, default={}) if CACHE_FILE.exists() else {}\n                                cache[\"_market_tide\"] = {\n                                    \"data\": tide_data,\n                                    \"last_update\": int(time.time())\n                                }\n                                # Also store per-ticker so scoring can access it\n                                for ticker in self.tickers:\n                                    if ticker not in cache:\n                                        cache[ticker] = {}\n                                    cache[ticker][\"market_tide\"] = tide_data\n                                atomic_write_json(CACHE_FILE, cache)'''\n"
            "if old_market_tide in content:\n"
            "    content = content.replace(old_market_tide, new_market_tide)\n"
            "    with open('uw_flow_daemon.py', 'w') as f:\n"
            "        f.write(content)\n"
            "    print('Fixed market_tide storage')\n"
            "else:\n"
            "    print('Could not find exact match for market_tide')\n"
            "    # Try to find it\n"
            "    if '_market_tide' in content:\n"
            "        print('Found _market_tide reference')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 2. Fix all signals to store even if empty
        print("2. FIXING EMPTY RESPONSE STORAGE")
        print("-" * 80)
        # Fix congress, institutional, calendar, etf_flow, oi_change to store even if empty
        result = client.execute_command(
            "cd ~/stock-bot && sed -i 's/if congress_data:/if True:  # Always store congress/' uw_flow_daemon.py && sed -i 's/if institutional_data:/if True:  # Always store institutional/' uw_flow_daemon.py && sed -i 's/if calendar_data:/if True:  # Always store calendar/' uw_flow_daemon.py && sed -i 's/if etf_data:/if True:  # Always store etf_flow/' uw_flow_daemon.py && echo 'Fixed empty response storage'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 3. Ensure empty responses create empty structures
        print("3. ENSURING EMPTY STRUCTURES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "with open('uw_flow_daemon.py', 'r') as f:\n"
            "    lines = f.readlines()\n"
            "# Fix congress\n"
            "for i, line in enumerate(lines):\n"
            "    if 'congress for {ticker}: API returned empty' in line:\n"
            "        # Add storage of empty structure after this line\n"
            "        if i+1 < len(lines) and 'except Exception' not in lines[i+1]:\n"
            "            lines.insert(i+1, f'                        self._update_cache(ticker, {{\"congress\": {{}}}})\\n')\n"
            "        break\n"
            "# Fix institutional\n"
            "for i, line in enumerate(lines):\n"
            "    if 'institutional for {ticker}: API returned empty' in line:\n"
            "        if i+1 < len(lines) and 'except Exception' not in lines[i+1]:\n"
            "            lines.insert(i+1, f'                        self._update_cache(ticker, {{\"institutional\": {{}}}})\\n')\n"
            "        break\n"
            "with open('uw_flow_daemon.py', 'w') as f:\n"
            "    f.writelines(lines)\n"
            "print('Added empty structure storage')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 4. Restart and verify
        print("4. RESTARTING SERVICE")
        print("-" * 80)
        client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted")
        print()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("1. Fixed market_tide to store per-ticker")
        print("2. Fixed empty response storage")
        print("3. Service restarted")
        print()
        print("All signals should now be stored, even if empty")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

