#!/usr/bin/env python3
"""Final verification that trades are ready to execute."""

from droplet_client import DropletClient
import json

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FINAL VERIFICATION: TRADES READY")
        print("=" * 80)
        print()
        
        # 1. Check cache
        print("1. CACHE STATUS")
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
            "    print(f'Symbols: {symbols[:20]}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 2. Check market
        print("2. MARKET STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import is_market_open_now\n"
            "market_open = is_market_open_now()\n"
            "print(f'Market open: {market_open}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 3. Check if clusters would be generated
        print("3. CLUSTER GENERATION TEST")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache, Config\n"
            "import uw_composite_v2 as uw_v2\n"
            "import uw_enrichment_v2 as uw_enrich\n"
            "uw_cache = read_uw_cache()\n"
            "symbols = [k for k in uw_cache.keys() if not k.startswith('_')]\n"
            "print(f'Testing cluster generation for {len(symbols)} symbols...')\n"
            "clusters = []\n"
            "for symbol in symbols[:5]:\n"
            "    try:\n"
            "        enriched = uw_enrich.enrich_symbol(symbol, uw_cache.get(symbol, {}))\n"
            "        composite = uw_v2.compute_composite_score_v3(symbol, enriched, 'mixed')\n"
            "        score = composite.get('score', 0)\n"
            "        if score > 0:\n"
            "            clusters.append({'symbol': symbol, 'score': score})\n"
            "            print(f'  {symbol}: score={score:.2f}')\n"
            "    except Exception as e:\n"
            "        print(f'  {symbol}: error={e}')\n"
            "print(f'\\nClusters generated: {len(clusters)}')\n"
            "PYEOF",
            timeout=120
        )
        print(result['stdout'])
        print()
        
        # 4. Check recent run cycles
        print("4. RECENT RUN CYCLES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -5 logs/run.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            c = json.loads(line)\n"
            "            market = c.get('market_open', 'unknown')\n"
            "            clusters = c.get('clusters', 0)\n"
            "            orders = c.get('orders', 0)\n"
            "            print(f'market_open={market}, clusters={clusters}, orders={orders}')\n"
            "        except:\n"
            "            pass\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'] if result['stdout'] else 'No cycles found')
        print()
        
        # 5. Check main bot status
        print("5. MAIN BOT STATUS")
        print("-" * 80)
        result = client.execute_command("ps aux | grep 'main.py' | grep -v grep", timeout=10)
        print("Main bot:" if result['stdout'] else "Main bot: NOT RUNNING")
        print(result['stdout'][:200] if result['stdout'] else '')
        print()
        
        # 6. Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("If cache has symbols, market is open, and clusters are generated,")
        print("trades should execute in the next run cycle.")
        print()
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

