#!/usr/bin/env python3
"""
Investigate REAL signal data flow - not just storage
1. Check if APIs are returning real data
2. Check if data is being processed correctly
3. Check if data is being stored correctly
4. Find root causes of missing signals
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("INVESTIGATE REAL SIGNAL DATA FLOW")
        print("=" * 80)
        print()
        
        # 1. Test dark_pool API directly - get REAL data
        print("1. TESTING DARK_POOL API FOR REAL DATA")
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
            "print(f'API response type: {type(dp_data)}')\n"
            "print(f'API response length: {len(dp_data) if isinstance(dp_data, list) else \"NOT A LIST\"}')\n"
            "if isinstance(dp_data, list):\n"
            "    print(f'First item: {dp_data[0] if dp_data else \"EMPTY LIST\"}')\n"
            "    if dp_data:\n"
            "        print(f'Sample keys: {list(dp_data[0].keys()) if isinstance(dp_data[0], dict) else \"NOT A DICT\"}')\n"
            "        # Check if it has premium data\n"
            "        sample = dp_data[0]\n"
            "        premium = sample.get('premium', sample.get('total_premium', 'MISSING'))\n"
            "        print(f'Sample premium: {premium}')\n"
            "else:\n"
            "    print(f'Response: {dp_data}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 2. Test normalization - does it work with real data?
        print("2. TESTING DARK_POOL NORMALIZATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from uw_flow_daemon import UWFlowDaemon\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "daemon = UWFlowDaemon()\n"
            "# Test with sample data\n"
            "sample_data = [{'premium': 5000000}, {'premium': -2000000}]\n"
            "normalized = daemon._normalize_dark_pool(sample_data)\n"
            "print(f'Normalized with sample data: {normalized}')\n"
            "# Test with empty\n"
            "empty_normalized = daemon._normalize_dark_pool([])\n"
            "print(f'Normalized with empty: {empty_normalized}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 3. Check recent daemon logs for API responses
        print("3. CHECKING RECENT API RESPONSES")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '30 minutes ago' --no-pager 2>&1 | grep -E 'dark_pool|API returned|API call success|data_type|data_keys' | tail -40",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:6000])
        print()
        
        # 4. Check what data is actually in cache
        print("4. CHECKING ACTUAL CACHE DATA")
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
            "    print(f'\\n{sym} data:')\n"
            "    # Check dark_pool\n"
            "    dp = data.get('dark_pool', {})\n"
            "    print(f'  dark_pool: {dp}')\n"
            "    print(f'  dark_pool has data: {bool(dp and dp.get(\"total_premium\", 0) != 0)}')\n"
            "    # Check other signals\n"
            "    for sig in ['congress', 'institutional', 'market_tide', 'etf_flow', 'oi_change', 'iv_rank']:\n"
            "        sig_data = data.get(sig, {})\n"
            "        has_real_data = bool(sig_data and (isinstance(sig_data, dict) and len(sig_data) > 0))\n"
            "        print(f'  {sig}: has_data={has_real_data}, keys={list(sig_data.keys())[:5] if isinstance(sig_data, dict) else \"NOT A DICT\"}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 5. Check API endpoint URLs - are they correct?
        print("5. CHECKING API ENDPOINT URLS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -E 'def get_(dark_pool|congress|institutional|market_tide)' uw_flow_daemon.py | head -10",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 6. Check if there are API errors or rate limiting
        print("6. CHECKING FOR API ERRORS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '1 hour ago' --no-pager 2>&1 | grep -E '404|403|401|rate limit|quota|API.*error|HTTP error' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:4000])
        print()
        
        # 7. Check if endpoints exist in UW API
        print("7. TESTING ENDPOINT EXISTENCE")
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
            "test_ticker = 'AAPL'\n"
            "endpoints = [\n"
            "    ('dark_pool', f'/api/darkpool/{test_ticker}'),\n"
            "    ('congress', f'/api/congress/{test_ticker}'),\n"
            "    ('institutional', f'/api/institutional/{test_ticker}'),\n"
            "    ('market_tide', '/api/market/market-tide'),\n"
            "    ('etf_flow', f'/api/etfs/{test_ticker}/in-outflow'),\n"
            "    ('oi_change', f'/api/stock/{test_ticker}/oi-change'),\n"
            "    ('iv_rank', f'/api/stock/{test_ticker}/iv-rank'),\n"
            "]\n"
            "print('Testing endpoint existence:')\n"
            "for name, endpoint in endpoints:\n"
            "    try:\n"
            "        raw = client._get(endpoint)\n"
            "        status = 'OK'\n"
            "        has_data = bool(raw.get('data'))\n"
            "        data_type = type(raw.get('data', {})).__name__\n"
            "        print(f'  {name} ({endpoint}): {status}, has_data={has_data}, data_type={data_type}')\n"
            "    except Exception as e:\n"
            "        error_msg = str(e)\n"
            "        if '404' in error_msg:\n"
            "            print(f'  {name} ({endpoint}): 404 NOT FOUND')\n"
            "        elif '403' in error_msg:\n"
            "            print(f'  {name} ({endpoint}): 403 FORBIDDEN')\n"
            "        else:\n"
            "            print(f'  {name} ({endpoint}): ERROR - {error_msg[:100]}')\n"
            "PYEOF",
            timeout=90
        )
        print(result['stdout'])
        print()
        
        print("=" * 80)
        print("DIAGNOSIS")
        print("=" * 80)
        print("Checking:")
        print("1. Are APIs returning real data?")
        print("2. Is normalization working correctly?")
        print("3. Are endpoints correct?")
        print("4. Are there API errors?")
        print("5. Is data being stored correctly?")
        print()
        
    except Exception as e:
        print(f"[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

