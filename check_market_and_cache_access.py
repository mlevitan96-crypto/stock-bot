#!/usr/bin/env python3
"""Check market status and cache access from main.py context."""

from droplet_client import DropletClient

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("CHECKING MARKET STATUS AND CACHE ACCESS")
        print("=" * 80)
        print()
        
        # Check market status using Alpaca
        print("1. MARKET STATUS (Alpaca API)")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "import alpaca_trade_api as tradeapi\n"
            "api = tradeapi.REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_API_SECRET'), os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'), api_version='v2')\n"
            "try:\n"
            "    clock = api.get_clock()\n"
            "    print(f'Alpaca clock.is_open: {clock.is_open}')\n"
            "    print(f'Next open: {clock.next_open}')\n"
            "    print(f'Next close: {clock.next_close}')\n"
            "except Exception as e:\n"
            "    print(f'Error: {e}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # Check if main.py can read cache
        print("2. CACHE ACCESS FROM MAIN.PY")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import CacheFiles\n"
            "from pathlib import Path\n"
            "import json\n"
            "cache_path = Path('data/uw_flow_cache.json')\n"
            "print(f'Cache file path: {cache_path}')\n"
            "print(f'Cache exists: {cache_path.exists()}')\n"
            "if cache_path.exists():\n"
            "    try:\n"
            "        cache = json.load(open(cache_path))\n"
            "        symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "        print(f'Symbols in cache: {len(symbols)}')\n"
            "        if symbols:\n"
            "            print(f'Sample: {symbols[:10]}')\n"
            "    except Exception as e:\n"
            "        print(f'Error reading cache: {e}')\n"
            "# Check read_uw_cache function\n"
            "try:\n"
            "    from main import read_uw_cache\n"
            "    uw_cache = read_uw_cache()\n"
            "    print(f'read_uw_cache() returned: {len(uw_cache)} symbols')\n"
            "except Exception as e:\n"
            "    print(f'Error calling read_uw_cache: {e}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # Check TICKERS config
        print("3. TICKERS CONFIGURATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import Config\n"
            "tickers = Config.TICKERS\n"
            "print(f'Total tickers: {len(tickers)}')\n"
            "print(f'First 20: {tickers[:20]}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # Check if clusters would be generated
        print("4. CLUSTER GENERATION TEST")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache, Config\n"
            "import uw_composite_v2 as uw_v2\n"
            "import uw_enrichment_v2 as uw_enrich\n"
            "# Read cache\n"
            "uw_cache = read_uw_cache()\n"
            "print(f'Cache symbols: {len(uw_cache)}')\n"
            "# Try to generate clusters for first few tickers\n"
            "test_tickers = Config.TICKERS[:5]\n"
            "print(f'Testing cluster generation for: {test_tickers}')\n"
            "clusters = []\n"
            "for ticker in test_tickers:\n"
            "    if ticker in uw_cache:\n"
            "        try:\n"
            "            enriched = uw_enrich.enrich_symbol(ticker, uw_cache.get(ticker, {}))\n"
            "            composite = uw_v2.compute_composite_score_v3(ticker, enriched, 'mixed')\n"
            "            score = composite.get('score', 0)\n"
            "            if score > 0:\n"
            "                clusters.append({'ticker': ticker, 'score': score})\n"
            "                print(f'  {ticker}: score={score:.2f}')\n"
            "        except Exception as e:\n"
            "            print(f'  {ticker}: error={e}')\n"
            "print(f'\\nClusters generated: {len(clusters)}')\n"
            "PYEOF",
            timeout=120
        )
        print(result['stdout'])
        print()
        
    except Exception as e:
        print(f"[ERROR] Check failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

