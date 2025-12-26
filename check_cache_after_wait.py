#!/usr/bin/env python3
"""Check cache after waiting for daemon to poll."""

from droplet_client import DropletClient
import time
import json

def main():
    client = DropletClient()
    
    print("Waiting 2 minutes for daemon to poll tickers...")
    time.sleep(120)
    
    # Check cache
    result = client.execute_command(
        "cd ~/stock-bot && python3 << 'PYEOF'\n"
        "import json\n"
        "try:\n"
        "    with open('data/uw_flow_cache.json') as f:\n"
        "        cache = json.load(f)\n"
        "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
        "    print(f'Symbols in cache: {len(symbols)}')\n"
        "    if symbols:\n"
        "        print(f'Sample: {symbols[:10]}')\n"
        "        sample = symbols[0]\n"
        "        data = cache.get(sample, {})\n"
        "        print(f'Sample data keys: {list(data.keys())[:10]}')\n"
        "    else:\n"
        "        print(f'All cache keys: {list(cache.keys())[:20]}')\n"
        "except Exception as e:\n"
        "    print(f'Error: {e}')\n"
        "PYEOF",
        timeout=30
    )
    print("\nCache status:")
    print(result['stdout'])
    
    # Check daemon logs
    result2 = client.execute_command(
        "cd ~/stock-bot && tail -100 logs/uw_flow_daemon.log 2>&1 | grep -E 'Polling|ticker|AAPL|MSFT|error|Error' | tail -20",
        timeout=10
    )
    print("\nRecent daemon activity:")
    print(result2['stdout'][:1000] if result2['stdout'] else 'No activity found')
    
    client.close()

if __name__ == "__main__":
    main()

