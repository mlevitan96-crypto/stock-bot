#!/usr/bin/env python3
"""
Comprehensive investigation of scoring system
1. Check cache data completeness
2. Test composite scoring with actual data
3. Check all scoring components
4. Identify what's broken
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("COMPREHENSIVE SCORING SYSTEM INVESTIGATION")
        print("=" * 80)
        print()
        
        # 1. Check cache data structure and completeness
        print("1. CACHE DATA STRUCTURE ANALYSIS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from pathlib import Path\n"
            "import json\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Total symbols in cache: {len(symbols)}')\n"
            "print(f'Symbols: {symbols[:10]}')\n"
            "print()\n"
            "if symbols:\n"
            "    sym = symbols[0]\n"
            "    print(f'Analyzing {sym}:')\n"
            "    data = cache.get(sym, {})\n"
            "    print(f'  Keys: {list(data.keys())}')\n"
            "    print(f'  sentiment: {data.get(\"sentiment\", \"MISSING\")}')\n"
            "    print(f'  conviction: {data.get(\"conviction\", \"MISSING\")}')\n"
            "    print(f'  flow_trades count: {len(data.get(\"flow_trades\", []))}')\n"
            "    dark_pool = data.get('dark_pool', {})\n"
            "    print(f'  dark_pool: {dark_pool}')\n"
            "    insider = data.get('insider', {})\n"
            "    print(f'  insider: {insider}')\n"
            "    print(f'  iv_term_skew: {data.get(\"iv_term_skew\", \"MISSING\")}')\n"
            "    print(f'  smile_slope: {data.get(\"smile_slope\", \"MISSING\")}')\n"
            "    print(f'  _last_update: {data.get(\"_last_update\", \"MISSING\")}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 2. Test composite scoring step by step
        print("2. COMPOSITE SCORING STEP-BY-STEP")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache, compute_market_regime\n"
            "from signals.uw_enrich import UWEnricher\n"
            "from signals.uw_v2 import compute_composite_score_v3\n"
            "from uw_composite_v2 import get_threshold, WEIGHTS_V3\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "if symbols:\n"
            "    sym = symbols[0]\n"
            "    print(f'Testing {sym}:')\n"
            "    print()\n"
            "    # Step 1: Enrichment\n"
            "    enricher = UWEnricher()\n"
            "    enriched = enricher.enrich_signal(sym, cache, 'mixed')\n"
            "    print('ENRICHMENT OUTPUT:')\n"
            "    for key in ['sentiment', 'conviction', 'dark_pool', 'insider', 'iv_term_skew', 'smile_slope', 'toxicity', 'freshness']:\n"
            "        val = enriched.get(key, 'MISSING')\n"
            "        if isinstance(val, dict):\n"
            "            print(f'  {key}: {list(val.keys()) if val else \"EMPTY\"}')\n"
            "        else:\n"
            "            print(f'  {key}: {val}')\n"
            "    print()\n"
            "    # Step 2: Composite scoring\n"
            "    composite = compute_composite_score_v3(sym, enriched, 'mixed')\n"
            "    if composite:\n"
            "        print('COMPOSITE SCORE OUTPUT:')\n"
            "        score = composite.get('score', 0.0)\n"
            "        print(f'  Final score: {score:.2f}')\n"
            "        components = composite.get('components', {})\n"
            "        print(f'  Components: {components}')\n"
            "        print()\n"
            "        # Step 3: Check weights\n"
            "        print('WEIGHTS USED:')\n"
            "        for comp_name, comp_value in components.items():\n"
            "            weight = WEIGHTS_V3.get(comp_name, 0.0)\n"
            "            contribution = comp_value * weight if isinstance(comp_value, (int, float)) else 0.0\n"
            "            print(f'  {comp_name}: value={comp_value}, weight={weight}, contribution={contribution:.2f}')\n"
            "        print()\n"
            "        # Step 4: Threshold check\n"
            "        threshold = get_threshold(sym, 'base')\n"
            "        print(f'THRESHOLD CHECK:')\n"
            "        print(f'  Score: {score:.2f}')\n"
            "        print(f'  Threshold: {threshold:.2f}')\n"
            "        print(f'  Pass: {score >= threshold}')\n"
            "    else:\n"
            "        print('ERROR: Composite scoring returned None')\n"
            "PYEOF",
            timeout=90
        )
        print(result['stdout'])
        print()
        
        # 3. Check if weights are being applied correctly
        print("3. WEIGHT APPLICATION VERIFICATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from uw_composite_v2 import WEIGHTS_V3, get_weight, get_all_current_weights\n"
            "print('BASE WEIGHTS (WEIGHTS_V3):')\n"
            "for key, val in sorted(WEIGHTS_V3.items()):\n"
            "    print(f'  {key}: {val}')\n"
            "print()\n"
            "print('CURRENT WEIGHTS (with adaptive):')\n"
            "current = get_all_current_weights()\n"
            "for key, val in sorted(current.items()):\n"
            "    print(f'  {key}: {val}')\n"
            "print()\n"
            "print('SAMPLE WEIGHT CHECKS:')\n"
            "for comp in ['options_flow', 'dark_pool', 'insider', 'iv_term_skew']:\n"
            "    w = get_weight(comp)\n"
            "    print(f'  {comp}: {w}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 4. Check scoring algorithm implementation
        print("4. SCORING ALGORITHM VERIFICATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from signals.uw_v2 import compute_composite_score_v3\n"
            "import inspect\n"
            "source = inspect.getsource(compute_composite_score_v3)\n"
            "lines = source.split('\\n')\n"
            "print('SCORING ALGORITHM KEY PARTS:')\n"
            "for i, line in enumerate(lines):\n"
            "    if 'score' in line.lower() and ('=' in line or '+' in line or '*' in line):\n"
            "        print(f'  Line {i}: {line.strip()}')\n"
            "        if i < len(lines) - 1:\n"
            "            print(f'    Next: {lines[i+1].strip()}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 5. Check recent logs for scoring details
        print("5. RECENT SCORING LOGS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '10 minutes ago' --no-pager 2>&1 | grep -E 'Composite|score|threshold|components|weights' | tail -40",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:5000])
        print()
        
        # 6. Summary and diagnosis
        print("=" * 80)
        print("DIAGNOSIS SUMMARY")
        print("=" * 80)
        print("Checking for common issues:")
        print("1. Missing cache data (sentiment, conviction, dark_pool, insider)")
        print("2. Zero or negative component values")
        print("3. Weights not being applied")
        print("4. Scoring algorithm bugs")
        print("5. Threshold too high for current data quality")
        print()
        
    except Exception as e:
        print(f"[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

