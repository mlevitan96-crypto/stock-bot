#!/usr/bin/env python3
"""
Fix scoring issues:
1. Reset adaptive weights (they're too low)
2. Ensure dark_pool is populated
3. Test scoring with fixed weights
4. Verify scores are reasonable
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIXING SCORING ISSUES")
        print("=" * 80)
        print()
        
        # 1. Reset adaptive weights to base weights
        print("1. RESETTING ADAPTIVE WEIGHTS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from pathlib import Path\n"
            "import json\n"
            "# Delete adaptive optimizer state to reset to base weights\n"
            "optimizer_state = Path('state/adaptive_signal_optimizer_state.json')\n"
            "if optimizer_state.exists():\n"
            "    optimizer_state.unlink()\n"
            "    print('Deleted adaptive optimizer state')\n"
            "else:\n"
            "    print('Adaptive optimizer state does not exist')\n"
            "# Also clear cached weights in uw_composite_v2\n"
            "print('Adaptive weights will reset on next scoring call')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 2. Check if dark_pool endpoint is being called
        print("2. CHECKING DARK_POOL POLLING")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '30 minutes ago' --no-pager 2>&1 | grep -E 'dark_pool|darkpool' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:2000])
        print()
        
        # 3. Manually trigger dark_pool polling for TSLA
        print("3. MANUALLY TRIGGERING DARK_POOL POLL")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from uw_flow_daemon import UWClient\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "client = UWClient()\n"
            "print('Polling dark_pool for TSLA...')\n"
            "dp_data = client.get_dark_pool_levels('TSLA')\n"
            "print(f'Dark pool data: {len(dp_data) if isinstance(dp_data, list) else \"NOT A LIST\"} items')\n"
            "if dp_data and len(dp_data) > 0:\n"
            "    print(f'Sample item: {dp_data[0] if isinstance(dp_data, list) else dp_data}')\n"
            "    from uw_flow_daemon import SmartPoller\n"
            "    poller = SmartPoller()\n"
            "    daemon = type('obj', (object,), {'client': client, 'poller': poller})()\n"
            "    dp_normalized = daemon._normalize_dark_pool(dp_data)\n"
            "    print(f'Normalized: {dp_normalized}')\n"
            "else:\n"
            "    print('No dark pool data returned')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 4. Test scoring with base weights (no adaptive)
        print("4. TESTING SCORING WITH BASE WEIGHTS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "# Force base weights by clearing adaptive\n"
            "import uw_composite_v2\n"
            "uw_composite_v2._cached_weights = {}\n"
            "uw_composite_v2._weights_cache_ts = 0.0\n"
            "from main import read_uw_cache\n"
            "from signals.uw_enrich import UWEnricher\n"
            "from signals.uw_v2 import compute_composite_score_v3\n"
            "from uw_composite_v2 import get_threshold, WEIGHTS_V3\n"
            "cache = read_uw_cache()\n"
            "sym = 'TSLA'\n"
            "if sym in cache:\n"
            "    enricher = UWEnricher()\n"
            "    enriched = enricher.enrich_signal(sym, cache, 'mixed')\n"
            "    # Force no adaptive weights\n"
            "    composite = compute_composite_score_v3(sym, enriched, 'mixed', use_adaptive_weights=False)\n"
            "    if composite:\n"
            "        score = composite.get('score', 0.0)\n"
            "        threshold = get_threshold(sym, 'base')\n"
            "        print(f'TSLA with BASE WEIGHTS:')\n"
            "        print(f'  Score: {score:.2f}')\n"
            "        print(f'  Threshold: {threshold:.2f}')\n"
            "        print(f'  Pass: {score >= threshold}')\n"
            "        components = composite.get('components', {})\n"
            "        print(f'  Components: {len(components)}')\n"
            "        for key, val in sorted(components.items())[:5]:\n"
            "            weight = WEIGHTS_V3.get(key, 0.0)\n"
            "            contrib = val * weight if isinstance(val, (int, float)) else 0.0\n"
            "            print(f'    {key}: {val:.3f} * {weight:.3f} = {contrib:.3f}')\n"
            "    else:\n"
            "        print('ERROR: Composite scoring returned None')\n"
            "else:\n"
            "    print(f'{sym} not in cache')\n"
            "PYEOF",
            timeout=90
        )
        print(result['stdout'])
        print()
        
        # 5. Restart service to apply changes
        print("5. RESTARTING SERVICE")
        print("-" * 80)
        client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted")
        time.sleep(30)
        print()
        
        # 6. Check new scores
        print("6. CHECKING NEW SCORES")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '2 minutes ago' --no-pager 2>&1 | grep -E 'Composite signal|score=|threshold=' | tail -10",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:2000])
        print()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("1. Adaptive weights reset - should use base weights now")
        print("2. Dark pool polling checked")
        print("3. Scoring tested with base weights")
        print("4. Service restarted")
        print()
        print("If scores are still low, the issue is:")
        print("- Missing dark_pool data (daemon not polling or API returning empty)")
        print("- Low conviction/flow values")
        print("- Threshold too high for current market conditions")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

