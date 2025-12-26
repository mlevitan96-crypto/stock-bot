#!/usr/bin/env python3
"""
Comprehensive Investigation: Why No Trades Despite Healthy Signals
Checks all aspects of the trading pipeline when signals exist but trades don't execute.
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("INVESTIGATING: WHY NO TRADES DESPITE HEALTHY SIGNALS")
        print("=" * 80)
        print()
        
        # 1. Check cache content
        print("1. CACHE CONTENT CHECK")
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
            "    # Check AAPL specifically\n"
            "    if 'AAPL' in cache:\n"
            "        aapl_data = cache['AAPL']\n"
            "        print(f'\\nAAPL data keys: {list(aapl_data.keys())[:15]}')\n"
            "        has_flow = bool(aapl_data.get('flow_trades'))\n"
            "        has_sentiment = bool(aapl_data.get('sentiment'))\n"
            "        has_conviction = bool(aapl_data.get('conviction'))\n"
            "        print(f'AAPL has flow_trades: {has_flow}')\n"
            "        print(f'AAPL has sentiment: {has_sentiment}')\n"
            "        print(f'AAPL has conviction: {has_conviction}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 2. Check if clusters are being generated
        print("2. CLUSTER GENERATION CHECK")
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
            "# Try to generate clusters for AAPL\n"
            "if 'AAPL' in uw_cache:\n"
            "    print('\\nTesting cluster generation for AAPL...')\n"
            "    try:\n"
            "        enriched = uw_enrich.enrich_symbol('AAPL', uw_cache.get('AAPL', {}))\n"
            "        print(f'Enriched keys: {list(enriched.keys())[:15]}')\n"
            "        composite = uw_v2.compute_composite_score_v3('AAPL', enriched, 'mixed')\n"
            "        score = composite.get('score', 0)\n"
            "        print(f'Composite score: {score:.2f}')\n"
            "        if score > 0:\n"
            "            print('✅ Cluster would be generated')\n"
            "        else:\n"
            "            print('❌ Score too low for cluster')\n"
            "    except Exception as e:\n"
            "        print(f'Error generating cluster: {e}')\n"
            "        import traceback\n"
            "        traceback.print_exc()\n"
            "else:\n"
            "    print('AAPL not in cache')\n"
            "PYEOF",
            timeout=120
        )
        print(result['stdout'])
        print()
        
        # 3. Check recent run cycles
        print("3. RECENT RUN CYCLES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -20 logs/run.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "cycles = []\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            cycles.append(json.loads(line))\n"
            "        except:\n"
            "            pass\n"
            "print(f'Recent cycles: {len(cycles)}')\n"
            "for c in cycles[-5:]:\n"
            "    market = c.get('market_open', 'unknown')\n"
            "    clusters = c.get('clusters', 0)\n"
            "    orders = c.get('orders', 0)\n"
            "    ts = c.get('ts', c.get('_ts', 'unknown'))\n"
            "    print(f'  {ts}: market_open={market}, clusters={clusters}, orders={orders}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 4. Check market status
        print("4. MARKET STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import is_market_open_now\n"
            "market_open = is_market_open_now()\n"
            "print(f'Market open (is_market_open_now): {market_open}')\n"
            "# Also check Alpaca directly\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "import alpaca_trade_api as tradeapi\n"
            "api = tradeapi.REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_API_SECRET'), os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'), api_version='v2')\n"
            "clock = api.get_clock()\n"
            "print(f'Alpaca clock.is_open: {clock.is_open}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 5. Check if decide_and_execute is being called
        print("5. DECIDE_AND_EXECUTE CALLS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -E 'decide_and_execute|clusters.*processed|About to call decide' logs/run.jsonl 2>&1 | tail -10",
            timeout=30
        )
        print(result['stdout'] if result['stdout'] else 'No decide_and_execute calls found')
        print()
        
        # 6. Check blocked trades
        print("6. RECENT BLOCKED TRADES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -50 state/blocked_trades.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "blocks = []\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            blocks.append(json.loads(line))\n"
            "        except:\n"
            "            pass\n"
            "print(f'Blocked trades (last 50): {len(blocks)}')\n"
            "if blocks:\n"
            "    recent = blocks[-10:]\n"
            "    for b in recent:\n"
            "        symbol = b.get('symbol', 'unknown')\n"
            "        score = b.get('score', 0)\n"
            "        reason = b.get('reason', 'unknown')\n"
            "        print(f'  {symbol}: score={score:.2f}, reason={reason}')\n"
            "else:\n"
            "    print('No blocked trades found')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 7. Check entry gates
        print("7. ENTRY GATE STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import trading_is_armed, Config\n"
            "from pathlib import Path\n"
            "import json\n"
            "# Check armed status\n"
            "armed = trading_is_armed()\n"
            "print(f'Trading armed: {armed}')\n"
            "# Check freeze\n"
            "freeze_file = Path('state/freeze.json')\n"
            "if freeze_file.exists():\n"
            "    freeze = json.load(open(freeze_file))\n"
            "    print(f'Freeze active: {freeze.get(\"frozen\", False)}')\n"
            "else:\n"
            "    print('Freeze: Not active')\n"
            "# Check entry gate threshold\n"
            "print(f'Entry gate threshold: {Config.UW_ENTRY_GATE}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 8. Check positions
        print("8. CURRENT POSITIONS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "import alpaca_trade_api as tradeapi\n"
            "api = tradeapi.REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_API_SECRET'), os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'), api_version='v2')\n"
            "positions = api.list_positions()\n"
            "print(f'Current positions: {len(positions)}')\n"
            "print(f'Max allowed: 16')\n"
            "print(f'Can open new: {len(positions) < 16}')\n"
            "for p in positions[:5]:\n"
            "    print(f'  {p.symbol}: {p.qty} shares')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 9. Summary
        print("=" * 80)
        print("DIAGNOSIS SUMMARY")
        print("=" * 80)
        print("Check each section above to identify why trades aren't executing:")
        print("1. Cache must have symbols with data")
        print("2. Clusters must be generated from cache")
        print("3. Market must be detected as open")
        print("4. decide_and_execute must be called")
        print("5. Signals must pass entry gates")
        print("6. No freeze or bootstrap blocking")
        print()
        
    except Exception as e:
        print(f"[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

