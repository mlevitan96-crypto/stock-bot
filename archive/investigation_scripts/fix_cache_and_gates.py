#!/usr/bin/env python3
"""
Fix cache path and check why gates are rejecting all symbols
"""

from droplet_client import DropletClient
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIX CACHE AND GATES")
        print("=" * 80)
        print()
        
        # 1. Find cache file
        print("1. FINDING CACHE FILE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && find . -name 'uw_flow_cache.json' -type f 2>&1 | head -5",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 2. Check registry path
        print("2. CHECKING REGISTRY PATH")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import CacheFiles\n"
            "print(f'CacheFiles.UW_FLOW_CACHE: {CacheFiles.UW_FLOW_CACHE}')\n"
            "from pathlib import Path\n"
            "cache_path = Path(CacheFiles.UW_FLOW_CACHE)\n"
            "print(f'Cache path exists: {cache_path.exists()}')\n"
            "if cache_path.exists():\n"
            "    print(f'Cache path: {cache_path.absolute()}')\n"
            "    print(f'Cache size: {cache_path.stat().st_size} bytes')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 3. Check why composite scoring is rejecting symbols
        print("3. CHECKING COMPOSITE SCORING REJECTIONS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '5 minutes ago' --no-pager 2>&1 | grep -E 'Composite signal REJECTED|Composite signal ACCEPTED|score=|threshold=|toxicity=|freshness=' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:4000])
        print()
        
        # 4. Test composite scoring directly
        print("4. TESTING COMPOSITE SCORING DIRECTLY")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "from signals.uw_enrich import UWEnricher\n"
            "from signals.uw_v2 import compute_composite_score_v3, should_enter_v2\n"
            "from main import compute_market_regime\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Cache symbols: {symbols[:5]}')\n"
            "if symbols:\n"
            "    sym = symbols[0]\n"
            "    print(f'\\nTesting {sym}...')\n"
            "    symbol_data = cache.get(sym, {})\n"
            "    print(f'Symbol data keys: {list(symbol_data.keys())[:10]}')\n"
            "    enricher = UWEnricher()\n"
            "    enriched = enricher.enrich_signal(sym, cache, 'mixed')\n"
            "    print(f'Enriched keys: {list(enriched.keys())[:10]}')\n"
            "    composite = compute_composite_score_v3(sym, enriched, 'mixed')\n"
            "    if composite:\n"
            "        score = composite.get('score', 0.0)\n"
            "        print(f'Composite score: {score:.2f}')\n"
            "        gate_result = should_enter_v2(composite, sym, mode='base')\n"
            "        print(f'Gate result: {gate_result}')\n"
            "        if not gate_result:\n"
            "            from main import get_threshold\n"
            "            threshold = get_threshold(sym, 'base')\n"
            "            print(f'Threshold: {threshold:.2f}')\n"
            "            print(f'Score {score:.2f} < Threshold {threshold:.2f}: {score < threshold}')\n"
            "            toxicity = composite.get('toxicity', 0.0)\n"
            "            freshness = composite.get('freshness', 1.0)\n"
            "            print(f'Toxicity: {toxicity:.2f} (reject if > 0.90)')\n"
            "            print(f'Freshness: {freshness:.2f} (reject if < 0.30)')\n"
            "    else:\n"
            "        print('Composite scoring returned None')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 5. Check daemon logs
        print("5. CHECKING DAEMON LOGS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '10 minutes ago' --no-pager 2>&1 | grep -E 'uw_flow_daemon|Cache file|flow_trades|polled' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:3000])
        print()
        
        # 6. Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("Key findings:")
        print("- Cache file location needs verification")
        print("- Composite scoring is running but rejecting all symbols")
        print("- Need to check: score vs threshold, toxicity, freshness")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

