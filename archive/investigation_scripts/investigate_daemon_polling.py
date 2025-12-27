#!/usr/bin/env python3
"""
Investigate why daemon isn't populating most signals
1. Check daemon process status
2. Check daemon logs for errors
3. Check which endpoints are being polled
4. Check API responses
5. Check cache population
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("DAEMON POLLING INVESTIGATION")
        print("=" * 80)
        print()
        
        # 1. Check daemon process
        print("1. DAEMON PROCESS STATUS")
        print("-" * 80)
        result = client.execute_command(
            "pgrep -af 'uw_flow_daemon' && echo '---' && ps aux | grep uw_flow_daemon | grep -v grep",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 2. Check daemon logs for errors
        print("2. DAEMON ERROR LOGS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '1 hour ago' --no-pager 2>&1 | grep -E 'uw-daemon|ERROR|Exception|Traceback|Failed|failed' | tail -50",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:5000])
        print()
        
        # 3. Check which endpoints are being polled
        print("3. ENDPOINT POLLING LOGS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '1 hour ago' --no-pager 2>&1 | grep -E 'Polling|should_poll|endpoint|dark_pool|congress|insider|greeks|iv_rank|oi_change|etf_flow|market_tide|calendar|institutional|shorts|ftd' | tail -100",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:6000])
        print()
        
        # 4. Check poller state
        print("4. POLLER STATE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from pathlib import Path\n"
            "import json\n"
            "poller_state = Path('state/uw_poller_state.json')\n"
            "if poller_state.exists():\n"
            "    state = json.loads(poller_state.read_text())\n"
            "    last_call = state.get('last_call', {})\n"
            "    print('Last call timestamps:')\n"
            "    import time\n"
            "    now = time.time()\n"
            "    for endpoint, timestamp in sorted(last_call.items()):\n"
            "        age = now - timestamp if timestamp else 999999\n"
            "        age_min = age / 60.0\n"
            "        print(f'  {endpoint}: {age_min:.1f} minutes ago')\n"
            "else:\n"
            "    print('Poller state file does not exist')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 5. Check cache for signal data
        print("5. CACHE SIGNAL DATA CHECK")
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
            "    print(f'\\n{sym} cache keys: {list(data.keys())}')\n"
            "    print(f'\\nSignal presence:')\n"
            "    signals = ['dark_pool', 'insider', 'congress', 'institutional', 'market_tide', 'calendar', 'shorts', 'ftd', 'greeks', 'iv_rank', 'oi_change', 'etf_flow']\n"
            "    for sig in signals:\n"
            "        present = sig in data and bool(data.get(sig))\n"
            "        print(f'  {sig}: {\"PRESENT\" if present else \"MISSING\"}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 6. Check daemon polling intervals
        print("6. DAEMON POLLING INTERVALS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -A 5 'intervals = {' uw_flow_daemon.py | head -20",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 7. Check if daemon is actually calling endpoints
        print("7. DAEMON API CALLS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '1 hour ago' --no-pager 2>&1 | grep -E 'get_dark_pool|get_congress|get_insider|get_greek|get_iv_rank|get_oi_change|get_etf_flow|get_market_tide|API request|_get.*api' | tail -50",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:5000])
        print()
        
        # 8. Check daemon ticker polling
        print("8. DAEMON TICKER POLLING")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '1 hour ago' --no-pager 2>&1 | grep -E '_poll_ticker|Polling.*for|ticker.*poll' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:3000])
        print()
        
        print("=" * 80)
        print("DIAGNOSIS")
        print("=" * 80)
        print("Checking:")
        print("1. Is daemon running?")
        print("2. Are endpoints being polled?")
        print("3. Are API calls succeeding?")
        print("4. Is data being written to cache?")
        print("5. Are polling intervals too long?")
        print()
        
    except Exception as e:
        print(f"[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

