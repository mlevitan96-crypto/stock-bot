#!/usr/bin/env python3
"""
Complete Root Cause Analysis - Find ALL issues blocking trades
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("COMPLETE ROOT CAUSE ANALYSIS - TRADE BLOCKING ISSUES")
        print("=" * 80)
        print()
        
        # 1. Check if bot is running
        print("1. BOT STATUS")
        print("-" * 80)
        result = client.execute_command(
            "systemctl is-active trading-bot.service && echo 'ACTIVE' || echo 'INACTIVE'",
            timeout=10
        )
        print(result['stdout'])
        result = client.execute_command(
            "pgrep -af 'main.py' | grep -v grep | wc -l",
            timeout=10
        )
        print(f"main.py processes: {result['stdout'].strip()}")
        print()
        
        # 2. Check recent execution cycles
        print("2. RECENT EXECUTION CYCLES")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '10 minutes ago' --no-pager 2>&1 | grep -E 'RUN_ONCE|decide_and_execute|clusters processed|orders returned|Composite score' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:4000])
        print()
        
        # 3. Check for build_client_order_id errors (should be fixed)
        print("3. build_client_order_id ERRORS (should be NONE)")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '10 minutes ago' --no-pager 2>&1 | grep -E 'build_client_order_id|ValueError.*int|invalid literal.*int' | tail -10",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        if output.strip():
            print("[FAIL] STILL HAS ERRORS:")
            print(output[:3000])
        else:
            print("[OK] No build_client_order_id errors (fix working)")
        print()
        
        # 4. Check actual scores vs threshold
        print("4. ACTUAL SCORES VS THRESHOLD")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '10 minutes ago' --no-pager 2>&1 | grep -E 'Composite score|score=.*threshold|REJECTED.*score' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:4000])
        print()
        
        # 5. Check what gates are blocking
        print("5. GATE BLOCKING ANALYSIS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '10 minutes ago' --no-pager 2>&1 | grep -E 'BLOCKED|REJECTED|gate.*fail|can_open|max_positions|expectancy.*fail|toxicity|regime.*block|already_positioned' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:5000])
        print()
        
        # 6. Check decide_and_execute flow
        print("6. decide_and_execute FLOW")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '10 minutes ago' --no-pager 2>&1 | grep -E 'decide_and_execute|Processing.*clusters|Building client_order_id|About to call submit_entry|Order submitted|Position opened' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:5000])
        print()
        
        # 7. Check cache data quality
        print("7. CACHE DATA QUALITY")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "from uw_composite_v2 import compute_composite_score_v3, get_threshold\n"
            "from uw_enrichment_v2 import enrich_signal\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')][:5]\n"
            "print(f'Testing {len(symbols)} symbols:')\n"
            "for sym in symbols:\n"
            "    data = cache.get(sym, {})\n"
            "    enriched = enrich_signal(sym, cache, 'mixed')\n"
            "    result = compute_composite_score_v3(sym, enriched, 'mixed')\n"
            "    score = result.get('score', 0)\n"
            "    threshold = get_threshold('bootstrap')\n"
            "    print(f'\\n{sym}:')\n"
            "    print(f'  Score: {score:.3f} (threshold: {threshold})')\n"
            "    print(f'  Passes: {score >= threshold}')\n"
            "    print(f'  Has dark_pool: {bool(enriched.get(\"dark_pool\"))}')\n"
            "    print(f'  Has market_tide: {bool(enriched.get(\"market_tide\"))}')\n"
            "    print(f'  Has insider: {bool(enriched.get(\"insider\"))}')\n"
            "    print(f'  Has greeks: {bool(enriched.get(\"greeks\"))}')\n"
            "    comps = result.get('components', {})\n"
            "    non_zero = {k: v for k, v in comps.items() if v != 0.0}\n"
            "    print(f'  Non-zero components: {len(non_zero)}/{len(comps)}')\n"
            "    if non_zero:\n"
            "        print(f'  Top components: {dict(list(non_zero.items())[:5])}')\n"
            "PYEOF",
            timeout=120
        )
        print(result['stdout'])
        print()
        
        # 8. Check market status
        print("8. MARKET STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from alpaca.trading.client import TradingClient\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "api_key = os.getenv('ALPACA_API_KEY')\n"
            "api_secret = os.getenv('ALPACA_API_SECRET')\n"
            "client = TradingClient(api_key, api_secret, paper=True)\n"
            "clock = client.get_clock()\n"
            "print(f'Market is_open: {clock.is_open}')\n"
            "print(f'Next open: {clock.next_open}')\n"
            "print(f'Next close: {clock.next_close}')\n"
            "positions = client.get_all_positions()\n"
            "print(f'Current positions: {len(positions)}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 9. Check for any exceptions/errors
        print("9. ALL ERRORS AND EXCEPTIONS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '10 minutes ago' --no-pager 2>&1 | grep -E 'ERROR|Exception|Traceback|Failed|failed|Error' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:6000])
        print()
        
        # 10. Check threshold configuration
        print("10. THRESHOLD CONFIGURATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -E 'ENTRY_THRESHOLD|get_threshold|bootstrap.*threshold' uw_composite_v2.py | head -10",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 11. Check max positions
        print("11. MAX POSITIONS CHECK")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from alpaca.trading.client import TradingClient\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "from config.registry import Config\n"
            "load_dotenv()\n"
            "api_key = os.getenv('ALPACA_API_KEY')\n"
            "api_secret = os.getenv('ALPACA_API_SECRET')\n"
            "client = TradingClient(api_key, api_secret, paper=True)\n"
            "positions = client.get_all_positions()\n"
            "print(f'Current positions: {len(positions)}')\n"
            "print(f'MAX_CONCURRENT_POSITIONS: {Config.MAX_CONCURRENT_POSITIONS}')\n"
            "print(f'Can open new: {len(positions) < Config.MAX_CONCURRENT_POSITIONS}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 12. Check freeze state
        print("12. FREEZE STATE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && ls -la state/*freeze* 2>/dev/null && echo '---FREEZE FILES EXIST---' || echo 'No freeze files'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        print("=" * 80)
        print("ROOT CAUSE SUMMARY")
        print("=" * 80)
        print("Checked:")
        print("1. Bot running status")
        print("2. Execution cycles")
        print("3. build_client_order_id errors (should be fixed)")
        print("4. Actual scores vs threshold")
        print("5. Gate blocking analysis")
        print("6. decide_and_execute flow")
        print("7. Cache data quality and scoring")
        print("8. Market status")
        print("9. All errors/exceptions")
        print("10. Threshold configuration")
        print("11. Max positions")
        print("12. Freeze state")
        print()
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

