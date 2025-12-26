#!/usr/bin/env python3
"""
Complete End-to-End Workflow Trace
Check EVERY step from UW API → Cache → Clusters → Signals → Scores → Orders
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("COMPLETE WORKFLOW TRACE - FINDING WHERE IT BREAKS")
        print("=" * 80)
        print()
        
        # STEP 1: UW Daemon Status
        print("STEP 1: UW DAEMON STATUS")
        print("-" * 80)
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        daemon_running = bool(result['stdout'].strip())
        print(f"Daemon running: {daemon_running}")
        if daemon_running:
            print(f"  {result['stdout'].strip()[:120]}")
        print()
        
        # STEP 2: Cache File Status
        print("STEP 2: CACHE FILE STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1",
            timeout=10
        )
        cache_exists = "No such file" not in result['stdout']
        print(f"Cache exists: {cache_exists}")
        if cache_exists:
            print(result['stdout'])
            # Check cache content
            result2 = client.execute_command(
                "cd ~/stock-bot && python3 << 'PYEOF'\n"
                "import json\n"
                "with open('data/uw_flow_cache.json') as f:\n"
                "    cache = json.load(f)\n"
                "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
                "print(f'Symbols in cache: {len(symbols)}')\n"
                "if symbols:\n"
                "    print(f'Sample symbols: {symbols[:10]}')\n"
                "    # Check if symbols have data\n"
                "    for sym in symbols[:3]:\n"
                "        data = cache.get(sym, {})\n"
                "        keys = list(data.keys()) if isinstance(data, dict) else []\n"
                "        print(f'  {sym}: {len(keys)} keys - {keys[:5]}')\n"
                "PYEOF",
                timeout=30
            )
            print(result2['stdout'])
        print()
        
        # STEP 3: Main.py Can Read Cache
        print("STEP 3: MAIN.PY CAN READ CACHE")
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
            "    print(f'Sample: {symbols[:5]}')\n"
            "    # Check data structure\n"
            "    sample = cache.get(symbols[0], {})\n"
            "    print(f'Sample data keys: {list(sample.keys())[:10] if isinstance(sample, dict) else \"not dict\"}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # STEP 4: Main.py Running and Generating Clusters
        print("STEP 4: MAIN.PY RUNNING AND GENERATING CLUSTERS")
        print("-" * 80)
        result = client.execute_command("ps aux | grep 'python.*main.py' | grep -v grep", timeout=10)
        main_running = bool(result['stdout'].strip())
        print(f"Main.py running: {main_running}")
        if main_running:
            print(f"  {result['stdout'].strip()[:120]}")
        print()
        
        # STEP 5: Recent Run Cycles
        print("STEP 5: RECENT RUN CYCLES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -20 logs/run.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "cycles = []\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            c = json.loads(line)\n"
            "            cycles.append(c)\n"
            "        except:\n"
            "            pass\n"
            "for c in cycles[-5:]:\n"
            "    msg = c.get('msg', '')\n"
            "    market = c.get('market_open', 'unknown')\n"
            "    clusters = c.get('clusters', 0)\n"
            "    orders = c.get('orders', 0)\n"
            "    alerts = c.get('alerts', [])\n"
            "    print(f'{msg}: market={market}, clusters={clusters}, orders={orders}, alerts={alerts}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'] if result['stdout'] else 'No cycles found')
        print()
        
        # STEP 6: Check Freeze Status
        print("STEP 6: FREEZE STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from pathlib import Path\n"
            "freeze_files = list(Path('state').glob('*freeze*'))\n"
            "print(f'Freeze files: {len(freeze_files)}')\n"
            "for f in freeze_files:\n"
            "    print(f'  {f.name}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # STEP 7: Market Status
        print("STEP 7: MARKET STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "from alpaca.trading.client import TradingClient\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "try:\n"
            "    client = TradingClient(api_key=os.getenv('ALPACA_KEY'), secret_key=os.getenv('ALPACA_SECRET'), paper=True)\n"
            "    clock = client.get_clock()\n"
            "    print(f'Market open: {clock.is_open}')\n"
            "    print(f'Next open: {clock.next_open}')\n"
            "    print(f'Next close: {clock.next_close}')\n"
            "except Exception as e:\n"
            "    print(f'Error: {e}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # STEP 8: Check Signal Generation
        print("STEP 8: SIGNAL GENERATION CHECK")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Cache symbols: {len(symbols)}')\n"
            "if symbols:\n"
            "    # Try to generate a cluster for one symbol\n"
            "    from main import UWClient\n"
            "    uw = UWClient()\n"
            "    test_symbol = symbols[0]\n"
            "    print(f'Testing cluster generation for {test_symbol}...')\n"
            "    try:\n"
            "        cluster = uw.get_cluster_for_symbol(test_symbol)\n"
            "        if cluster:\n"
            "            print(f'Cluster generated: {len(cluster)} keys')\n"
            "            print(f'Cluster keys: {list(cluster.keys())[:10]}')\n"
            "        else:\n"
            "            print('Cluster is None or empty')\n"
            "    except Exception as e:\n"
            "        print(f'Error generating cluster: {e}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # STEP 9: Check Gate Status
        print("STEP 9: GATE STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import Config\n"
            "print(f'MAX_CONCURRENT_POSITIONS: {Config.MAX_CONCURRENT_POSITIONS}')\n"
            "print(f'MIN_EXEC_SCORE: {Config.MIN_EXEC_SCORE}')\n"
            "try:\n"
            "    from v3_2_features import entry_ev_floor\n"
            "    print(f'entry_ev_floor: {entry_ev_floor}')\n"
            "except:\n"
            "    print('entry_ev_floor: not found')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # STEP 10: Check Recent Orders
        print("STEP 10: RECENT ORDERS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "from alpaca.trading.client import TradingClient\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "from datetime import datetime, timedelta\n"
            "load_dotenv()\n"
            "try:\n"
            "    client = TradingClient(api_key=os.getenv('ALPACA_KEY'), secret_key=os.getenv('ALPACA_SECRET'), paper=True)\n"
            "    orders = client.list_orders(status='all', limit=10)\n"
            "    print(f'Recent orders: {len(orders)}')\n"
            "    for o in orders[:5]:\n"
            "        print(f'  {o.symbol} {o.side} {o.qty} @ {o.created_at}')\n"
            "except Exception as e:\n"
            "    print(f'Error: {e}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # STEP 11: Check Current Positions
        print("STEP 11: CURRENT POSITIONS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "from alpaca.trading.client import TradingClient\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "try:\n"
            "    client = TradingClient(api_key=os.getenv('ALPACA_KEY'), secret_key=os.getenv('ALPACA_SECRET'), paper=True)\n"
            "    positions = client.list_positions()\n"
            "    print(f'Open positions: {len(positions)}')\n"
            "    for p in positions:\n"
            "        print(f'  {p.symbol} {p.qty} @ {p.avg_entry_price}')\n"
            "except Exception as e:\n"
            "    print(f'Error: {e}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # STEP 12: Check Main.py Logs for Errors
        print("STEP 12: MAIN.PY LOGS FOR ERRORS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -50 logs/run.jsonl 2>&1 | grep -E 'error|Error|ERROR|exception|Exception|traceback|Traceback|failed|Failed|blocked|Blocked' | tail -10",
            timeout=10
        )
        print(result['stdout'][:2000] if result['stdout'] else 'No errors found')
        print()
        
        # SUMMARY
        print("=" * 80)
        print("WORKFLOW TRACE SUMMARY")
        print("=" * 80)
        print(f"1. UW Daemon: {'[OK]' if daemon_running else '[FAIL]'}")
        print(f"2. Cache File: {'[OK]' if cache_exists else '[FAIL]'}")
        print(f"3. Main.py Running: {'[OK]' if main_running else '[FAIL]'}")
        print()
        print("Check the output above to find where the workflow breaks.")
        print()
        
    except Exception as e:
        print(f"[ERROR] Trace failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

