#!/usr/bin/env python3
"""
Comprehensive Diagnosis: Why No Trades Are Happening
Checks all conditions and identifies blockers.
"""

from droplet_client import DropletClient
import json
import time

def main():
    print("=" * 80)
    print("COMPREHENSIVE DIAGNOSIS: WHY NO TRADES")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # 1. Check Cache and Data Availability
        print("1. DATA AVAILABILITY")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import json\n"
            "from pathlib import Path\n"
            "cache_file = Path('data/uw_flow_cache.json')\n"
            "if cache_file.exists():\n"
            "    cache = json.load(open(cache_file))\n"
            "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "    print(f'Cache exists: YES')\n"
            "    print(f'Symbols in cache: {len(symbols)}')\n"
            "    if symbols:\n"
            "        sample = symbols[0]\n"
            "        data = cache.get(sample, {})\n"
            "        has_sentiment = bool(data.get('sentiment'))\n"
            "        has_conviction = bool(data.get('conviction'))\n"
            "        has_flow = bool(data.get('flow_trades'))\n"
            "        print(f'Sample symbol ({sample}): sentiment={has_sentiment}, conviction={has_conviction}, flow_trades={has_flow}')\n"
            "else:\n"
            "    print('Cache exists: NO')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 2. Check if clusters are being generated
        print("2. CLUSTER GENERATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import ConfigFiles\n"
            "import json\n"
            "from pathlib import Path\n"
            "# Check if composite scoring would generate clusters\n"
            "cache_file = Path('data/uw_flow_cache.json')\n"
            "if cache_file.exists():\n"
            "    cache = json.load(open(cache_file))\n"
            "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "    print(f'Symbols available for composite scoring: {len(symbols)}')\n"
            "    # Check TICKERS config\n"
            "    try:\n"
            "        from main import Config\n"
            "        tickers = Config.TICKERS\n"
            "        print(f'Configured tickers: {len(tickers)}')\n"
            "        print(f'Sample tickers: {tickers[:10] if len(tickers) > 10 else tickers}')\n"
            "        # Check overlap\n"
            "        overlap = [s for s in symbols if s in tickers]\n"
            "        print(f'Symbols in both cache and tickers: {len(overlap)}')\n"
            "    except Exception as e:\n"
            "        print(f'Could not check tickers: {e}')\n"
            "else:\n"
            "    print('Cache not available for cluster generation')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 3. Check run_once conditions
        print("3. RUN_ONCE CONDITIONS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from pathlib import Path\n"
            "import json\n"
            "# Check freeze\n"
            "freeze_file = Path('state/freeze.json')\n"
            "if freeze_file.exists():\n"
            "    freeze = json.load(open(freeze_file))\n"
            "    print(f'Freeze active: {freeze.get(\"frozen\", False)}')\n"
            "else:\n"
            "    print('Freeze active: NO')\n"
            "# Check armed status\n"
            "try:\n"
            "    from main import trading_is_armed\n"
            "    armed = trading_is_armed()\n"
            "    print(f'Trading armed: {armed}')\n"
            "except Exception as e:\n"
            "    print(f'Could not check armed status: {e}')\n"
            "# Check market open\n"
            "try:\n"
            "    from main import is_market_open\n"
            "    market_open = is_market_open()\n"
            "    print(f'Market open: {market_open}')\n"
            "except Exception as e:\n"
            "    print(f'Could not check market status: {e}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 4. Check recent main.py output
        print("4. RECENT MAIN.PY OUTPUT")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -50 logs/run.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "events = []\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            events.append(json.loads(line))\n"
            "        except:\n"
            "            pass\n"
            "print(f'Recent events: {len(events)}')\n"
            "if events:\n"
            "    # Look for key events\n"
            "    for e in events[-20:]:\n"
            "        event = e.get('event', '')\n"
            "        if 'cluster' in event.lower() or 'decide' in event.lower() or 'signal' in event.lower() or 'order' in event.lower():\n"
            "            print(f\"  {event}: {e.get('symbol', '')} {e.get('cluster_count', '')} {e.get('orders', '')}\")\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'] if result['stdout'] else 'No relevant events found')
        print()
        
        # 5. Check if composite scoring is running
        print("5. COMPOSITE SCORING STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -E 'composite|cluster|decide_and_execute' logs/run.jsonl 2>&1 | tail -20",
            timeout=30
        )
        print(result['stdout'] if result['stdout'] else 'No composite scoring activity found')
        print()
        
        # 6. Check TICKERS configuration
        print("6. TICKERS CONFIGURATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "try:\n"
            "    from main import Config\n"
            "    tickers = Config.TICKERS\n"
            "    print(f'Total tickers configured: {len(tickers)}')\n"
            "    print(f'First 20: {tickers[:20]}')\n"
            "except Exception as e:\n"
            "    print(f'Error: {e}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 7. Summary and Recommendations
        print("=" * 80)
        print("DIAGNOSIS SUMMARY")
        print("=" * 80)
        print("Check the above sections to identify blockers:")
        print("1. Data availability - cache must exist with symbols")
        print("2. Cluster generation - composite scoring must create clusters")
        print("3. Run conditions - freeze, armed, market open must all be OK")
        print("4. Recent activity - check if decide_and_execute is being called")
        print("5. Composite scoring - must be running to generate signals")
        print("6. Tickers config - must have symbols configured")
        print()
        
    except Exception as e:
        print(f"[ERROR] Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

