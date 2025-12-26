#!/usr/bin/env python3
"""
Deep investigation of scoring issues
1. Why is dark_pool empty?
2. Why are adaptive weights so low?
3. What's the actual score calculation?
4. Test with TSLA which has good data
"""

from droplet_client import DropletClient
import json

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("DEEP SCORING INVESTIGATION")
        print("=" * 80)
        print()
        
        # 1. Test TSLA scoring in detail (it has good data)
        print("1. DETAILED TSLA SCORING TEST")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "from signals.uw_enrich import UWEnricher\n"
            "from signals.uw_v2 import compute_composite_score_v3\n"
            "from uw_composite_v2 import get_threshold, WEIGHTS_V3, get_weight\n"
            "import traceback\n"
            "cache = read_uw_cache()\n"
            "sym = 'TSLA'\n"
            "print(f'Testing {sym} with full data...')\n"
            "print()\n"
            "try:\n"
            "    # Enrichment\n"
            "    enricher = UWEnricher()\n"
            "    enriched = enricher.enrich_signal(sym, cache, 'mixed')\n"
            "    print('ENRICHED DATA:')\n"
            "    print(f'  sentiment: {enriched.get(\"sentiment\")}')\n"
            "    print(f'  conviction: {enriched.get(\"conviction\")}')\n"
            "    print(f'  dark_pool: {enriched.get(\"dark_pool\")}')\n"
            "    print(f'  insider: {enriched.get(\"insider\")}')\n"
            "    print(f'  iv_term_skew: {enriched.get(\"iv_term_skew\")}')\n"
            "    print(f'  smile_slope: {enriched.get(\"smile_slope\")}')\n"
            "    print(f'  toxicity: {enriched.get(\"toxicity\")}')\n"
            "    print(f'  freshness: {enriched.get(\"freshness\")}')\n"
            "    print()\n"
            "    # Composite scoring\n"
            "    composite = compute_composite_score_v3(sym, enriched, 'mixed')\n"
            "    if composite:\n"
            "        score = composite.get('score', 0.0)\n"
            "        components = composite.get('components', {})\n"
            "        print(f'COMPOSITE SCORE: {score:.2f}')\n"
            "        print()\n"
            "        print('COMPONENT BREAKDOWN:')\n"
            "        total_contribution = 0.0\n"
            "        for comp_name, comp_value in sorted(components.items()):\n"
            "            weight = get_weight(comp_name)\n"
            "            if isinstance(comp_value, (int, float)):\n"
            "                contribution = comp_value * weight\n"
            "                total_contribution += contribution\n"
            "                print(f'  {comp_name}: value={comp_value:.3f}, weight={weight:.3f}, contribution={contribution:.3f}')\n"
            "            else:\n"
            "                print(f'  {comp_name}: value={comp_value}, weight={weight:.3f} (non-numeric)')\n"
            "        print()\n"
            "        print(f'TOTAL CONTRIBUTION: {total_contribution:.2f}')\n"
            "        print(f'FINAL SCORE: {score:.2f}')\n"
            "        print(f'DIFFERENCE: {score - total_contribution:.2f}')\n"
            "        print()\n"
            "        threshold = get_threshold(sym, 'base')\n"
            "        print(f'THRESHOLD: {threshold:.2f}')\n"
            "        print(f'PASS: {score >= threshold}')\n"
            "    else:\n"
            "        print('ERROR: Composite scoring returned None')\n"
            "        print(traceback.format_exc())\n"
            "except Exception as e:\n"
            "    print(f'ERROR: {e}')\n"
            "    print(traceback.format_exc())\n"
            "PYEOF",
            timeout=90
        )
        print(result['stdout'])
        print()
        
        # 2. Check why dark_pool is empty
        print("2. WHY IS DARK_POOL EMPTY?")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "sym = 'TSLA'\n"
            "data = cache.get(sym, {})\n"
            "print(f'TSLA cache keys: {list(data.keys())}')\n"
            "print(f'dark_pool key exists: {\"dark_pool\" in data}')\n"
            "print(f'dark_pool value: {data.get(\"dark_pool\", \"MISSING\")}')\n"
            "print()\n"
            "print('Checking if daemon populates dark_pool...')\n"
            "print('Looking for dark_pool in flow_trades...')\n"
            "flow_trades = data.get('flow_trades', [])\n"
            "if flow_trades:\n"
            "    print(f'flow_trades count: {len(flow_trades)}')\n"
            "    sample = flow_trades[0] if flow_trades else {}\n"
            "    print(f'Sample trade keys: {list(sample.keys()) if isinstance(sample, dict) else \"NOT A DICT\"}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 3. Check adaptive optimizer state
        print("3. ADAPTIVE OPTIMIZER STATE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from pathlib import Path\n"
            "import json\n"
            "optimizer_state = Path('state/adaptive_signal_optimizer_state.json')\n"
            "if optimizer_state.exists():\n"
            "    state = json.loads(optimizer_state.read_text())\n"
            "    print('ADAPTIVE OPTIMIZER STATE:')\n"
            "    weights = state.get('weights', {})\n"
            "    print(f'Number of learned weights: {len(weights)}')\n"
            "    for key, val in sorted(weights.items())[:10]:\n"
            "        print(f'  {key}: {val}')\n"
            "    print()\n"
            "    print('Recent outcomes:')\n"
            "    outcomes = state.get('recent_outcomes', [])\n"
            "    print(f'  Total outcomes: {len(outcomes)}')\n"
            "    if outcomes:\n"
            "        wins = sum(1 for o in outcomes if o.get('pnl', 0) > 0)\n"
            "        print(f'  Wins: {wins}, Losses: {len(outcomes) - wins}')\n"
            "else:\n"
            "    print('Optimizer state file does not exist')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 4. Check scoring algorithm source
        print("4. SCORING ALGORITHM SOURCE CODE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && grep -A 50 'def compute_composite_score_v3' signals/uw_v2.py | head -60",
            timeout=10
        )
        print(result['stdout'])
        print()
        
    except Exception as e:
        print(f"[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

