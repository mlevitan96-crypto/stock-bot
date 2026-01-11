#!/usr/bin/env python3
"""
Check why no signals are being generated - inspect composite scores and gate results
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available")
    sys.exit(1)

def check_signal_generation():
    """Check why signals aren't being generated."""
    print("=" * 80)
    print("CHECKING WHY NO SIGNALS ARE BEING GENERATED")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Check composite scores for sample symbols
        print("Step 1: Checking composite scores for sample symbols...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import json\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import CacheFiles, read_json\n"
            "import uw_composite_v2 as uw_v2\n"
            "\n"
            "cache = read_json(CacheFiles.UW_FLOW_CACHE, default={})\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')][:5]\n"
            "print(f'Checking {len(symbols)} symbols...')\n"
            "for symbol in symbols:\n"
            "    enriched = cache.get(symbol, {})\n"
            "    if enriched:\n"
            "        composite = uw_v2.compute_composite_score_v3(symbol, enriched, 'mixed')\n"
            "        if composite:\n"
            "            score = composite.get('score', 0.0)\n"
            "            threshold = 2.7  # Base threshold\n"
            "            toxicity = composite.get('toxicity', 0.0)\n"
            "            freshness = composite.get('freshness', 1.0)\n"
            "            whale_boost = composite.get('whale_conviction_boost', 0.0)\n"
            "            print(f'{symbol}: score={score:.2f}, threshold={threshold:.2f}, toxicity={toxicity:.2f}, freshness={freshness:.2f}, whale_boost={whale_boost:.2f}')\n"
            "            print(f'  Would pass gate: score >= threshold={score >= threshold}, toxicity <= 0.90={toxicity <= 0.90}, freshness >= 0.30={freshness >= 0.30}')\n"
            "        else:\n"
            "            print(f'{symbol}: composite scoring returned None')\n"
            "PYEOF",
            timeout=30
        )
        if stdout:
            print(stdout)
        print()
        
        # Check should_enter_v2 results
        print("Step 2: Checking should_enter_v2 gate results...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import json\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from config.registry import CacheFiles, read_json\n"
            "import uw_composite_v2 as uw_v2\n"
            "\n"
            "cache = read_json(CacheFiles.UW_FLOW_CACHE, default={})\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')][:5]\n"
            "print(f'Testing should_enter_v2 for {len(symbols)} symbols...')\n"
            "for symbol in symbols:\n"
            "    enriched = cache.get(symbol, {})\n"
            "    if enriched:\n"
            "        composite = uw_v2.compute_composite_score_v3(symbol, enriched, 'mixed')\n"
            "        if composite:\n"
            "            # Test should_enter_v2 (without api parameter)\n"
            "            try:\n"
            "                gate_result = uw_v2.should_enter_v2(composite, symbol, mode='base', api=None)\n"
            "                score = composite.get('score', 0.0)\n"
            "                print(f'{symbol}: score={score:.2f}, should_enter_v2={gate_result}')\n"
            "            except Exception as e:\n"
            "                print(f'{symbol}: should_enter_v2 error: {e}')\n"
            "PYEOF",
            timeout=30
        )
        if stdout:
            print(stdout)
        print()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("If all scores are below threshold or all should_enter_v2=False,")
        print("then signals are being generated but rejected by gates.")
        print("This is why clusters=0 and no signals appear in Signal Review tab.")
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Check failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = check_signal_generation()
    sys.exit(0 if success else 1)
