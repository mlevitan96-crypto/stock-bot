#!/usr/bin/env python3
"""
Direct investigation on droplet - simplified version
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from droplet_client import DropletClient
except ImportError as e:
    print(f"ERROR: Could not import droplet_client: {e}")
    sys.exit(1)

def main():
    print("=" * 80)
    print("RUNNING SCORE INVESTIGATION ON DROPLET")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Pull latest code
        print("Step 1: Pulling latest code...")
        result = client.execute_command(
            "cd ~/stock-bot && git fetch origin main && git reset --hard origin/main",
            timeout=120
        )
        if result.get('success'):
            print("[OK] Code pulled")
        else:
            print(f"[WARNING] {result.get('stderr', 'Unknown error')[:200]}")
        print()
        
        # Step 2: Run investigation
        print("Step 2: Running score investigation...")
        result = client.execute_command(
            "cd ~/stock-bot && python3 investigate_low_scores.py",
            timeout=300
        )
        
        print("\n" + "=" * 80)
        print("INVESTIGATION OUTPUT")
        print("=" * 80)
        print(result.get('stdout', ''))
        
        if result.get('stderr'):
            print("\n" + "=" * 80)
            print("ERRORS")
            print("=" * 80)
            print(result.get('stderr'))
        
        # Step 3: Get recent scores
        print("\n" + "=" * 80)
        print("Step 3: Recent composite scores from logs...")
        print("=" * 80)
        
        result2 = client.execute_command(
            "cd ~/stock-bot && tail -500 logs/trading.log | grep -i 'composite_score\\|score=' | tail -30",
            timeout=30
        )
        print(result2.get('stdout', 'No scores found'))
        
        # Step 4: Check cache data
        print("\n" + "=" * 80)
        print("Step 4: Sample cache data...")
        print("=" * 80)
        
        result3 = client.execute_command(
            """cd ~/stock-bot && python3 -c "
import json
from pathlib import Path
cache = json.load(open('data/uw_flow_cache.json'))
syms = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'SPY', 'QQQ']
for s in syms:
    if s in cache:
        d = cache[s]
        print(f'{s}: sent={d.get(\"sentiment\", \"MISS\")}, conv={d.get(\"conviction\", 0):.3f}, fresh={d.get(\"freshness\", 1.0):.3f}, has_dp={bool(d.get(\"dark_pool\"))}, has_ins={bool(d.get(\"insider\"))}, has_iv={bool(d.get(\"iv_term_skew\"))}')
" """,
            timeout=30
        )
        print(result3.get('stdout', 'No data'))
        
    except Exception as e:
        print(f"\n[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()
