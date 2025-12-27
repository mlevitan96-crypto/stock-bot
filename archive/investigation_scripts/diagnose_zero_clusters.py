#!/usr/bin/env python3
"""
Diagnose why clusters = 0
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("DIAGNOSE ZERO CLUSTERS")
        print("=" * 80)
        print()
        
        # 1. Check cache
        print("1. CHECKING CACHE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from pathlib import Path\n"
            "import json\n"
            "cache_path = Path('data/uw_flow_cache.json')\n"
            "if cache_path.exists():\n"
            "    cache = json.loads(cache_path.read_text())\n"
            "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "    print(f'Cache exists: YES')\n"
            "    print(f'Cache size: {cache_path.stat().st_size} bytes')\n"
            "    print(f'Symbols: {len(symbols)}')\n"
            "    print(f'Symbol list: {symbols[:10]}')\n"
            "    for sym in symbols[:3]:\n"
            "        data = cache.get(sym, {})\n"
            "        flow_trades = data.get('flow_trades', [])\n"
            "        print(f'  {sym}: {len(flow_trades)} flow_trades')\n"
            "else:\n"
            "    print('Cache exists: NO')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 2. Check daemon
        print("2. CHECKING DAEMON")
        print("-" * 80)
        result = client.execute_command(
            "pgrep -f 'uw_flow_daemon.py' && echo 'Daemon running' || echo 'Daemon NOT running'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 3. Check recent main.py logs for cluster generation
        print("3. CHECKING CLUSTER GENERATION LOGS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '5 minutes ago' --no-pager 2>&1 | grep -E 'DEBUG.*clusters|DEBUG.*flow_trades|DEBUG.*composite|DEBUG.*symbols|cluster_signals' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:4000])
        print()
        
        # 4. Check run.jsonl for detailed metrics
        print("4. CHECKING RUN METRICS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -3 logs/run.jsonl 2>&1",
            timeout=10
        )
        if result['stdout']:
            for line in result['stdout'].strip().split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        metrics = data.get('metrics', {})
                        print(f"Msg: {data.get('msg', 'N/A')}")
                        print(f"Clusters: {data.get('clusters', 0)}")
                        print(f"Orders: {data.get('orders', 0)}")
                        print(f"Composite enabled: {metrics.get('composite_enabled', False)}")
                        print(f"Cache symbols: {metrics.get('cache_symbols', 0)}")
                        print(f"Flow trades: {metrics.get('flow_trades_count', 0)}")
                        print()
                    except:
                        print(line)
        print()
        
        # 5. Test cluster_signals directly
        print("5. TESTING cluster_signals() DIRECTLY")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import cluster_signals, read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "print(f'Cache symbols: {len([k for k in cache.keys() if not k.startswith(\"_\")])}')\n"
            "# Get flow_trades from cache\n"
            "all_trades = []\n"
            "for sym, data in cache.items():\n"
            "    if sym.startswith('_'):\n"
            "        continue\n"
            "    flow_trades = data.get('flow_trades', [])\n"
            "    for trade in flow_trades:\n"
            "        trade['ticker'] = sym  # Ensure ticker is set\n"
            "        all_trades.append(trade)\n"
            "print(f'Total flow_trades: {len(all_trades)}')\n"
            "clusters = cluster_signals(all_trades)\n"
            "print(f'Clusters generated: {len(clusters)}')\n"
            "if clusters:\n"
            "    for c in clusters[:3]:\n"
            "        print(f'  {c.get(\"ticker\", \"N/A\")}: {c.get(\"direction\", \"N/A\")}, count={c.get(\"count\", 0)}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 6. Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("If clusters = 0, possible causes:")
        print("1. Cache has no flow_trades")
        print("2. cluster_signals() is filtering out all trades")
        print("3. Composite scoring is not generating clusters")
        print("4. Daemon is not populating cache")
        print()
        
    except Exception as e:
        print(f"[ERROR] Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

