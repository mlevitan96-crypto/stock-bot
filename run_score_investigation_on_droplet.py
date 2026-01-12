#!/usr/bin/env python3
"""
Run score investigation on droplet and analyze results.
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available")
    sys.exit(1)

def main():
    print("=" * 80)
    print("RUNNING SCORE INVESTIGATION ON DROPLET")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Pull latest code
        print("Step 1: Pulling latest code from Git...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && git fetch origin main && git reset --hard origin/main",
            timeout=120
        )
        if exit_code == 0:
            print("[OK] Code pulled successfully")
        else:
            print(f"[WARNING] Git pull had issues: {stderr[:200] if stderr else 'Unknown error'}")
        print()
        
        # Step 2: Run investigation
        print("Step 2: Running score investigation...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && source venv/bin/activate 2>/dev/null; python3 investigate_low_scores.py 2>&1",
            timeout=300
        )
        
        print("\n" + "=" * 80)
        print("INVESTIGATION OUTPUT")
        print("=" * 80)
        
        # Handle encoding for Windows terminal
        try:
            stdout_safe = stdout.encode('ascii', errors='replace').decode('ascii', errors='replace')
            print(stdout_safe)
        except:
            print(stdout)
        
        if stderr:
            print("\n" + "=" * 80)
            print("ERRORS")
            print("=" * 80)
            try:
                stderr_safe = stderr.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                print(stderr_safe)
            except:
                print(stderr)
        
        # Step 3: Get recent composite scores from logs
        print("\n" + "=" * 80)
        print("Step 3: Checking recent composite scores in logs...")
        print("=" * 80)
        
        stdout2, stderr2, exit_code2 = client._execute_with_cd(
            "cd ~/stock-bot && tail -200 logs/trading.log 2>/dev/null | grep -i 'composite_score\\|score=' | tail -20",
            timeout=30
        )
        
        if stdout2:
            print(stdout2)
        else:
            print("No recent scores found in logs")
        
        # Step 4: Check actual cache data
        print("\n" + "=" * 80)
        print("Step 4: Checking cache data for sample symbols...")
        print("=" * 80)
        
        stdout3, stderr3, exit_code3 = client._execute_with_cd(
            "cd ~/stock-bot && python3 -c \"import json; cache = json.load(open('data/uw_flow_cache.json')); syms = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'SPY']; [print(f'{s}: sentiment={cache.get(s, {}).get(\\\"sentiment\\\", \\\"MISSING\\\")}, conviction={cache.get(s, {}).get(\\\"conviction\\\", 0):.3f}, freshness={cache.get(s, {}).get(\\\"freshness\\\", 1.0):.3f}') for s in syms if s in cache]\" 2>&1",
            timeout=30
        )
        
        if stdout3:
            print(stdout3)
        
        # Step 5: Check if main.py is using composite scoring
        print("\n" + "=" * 80)
        print("Step 5: Checking if composite scoring is enabled...")
        print("=" * 80)
        
        stdout4, stderr4, exit_code4 = client._execute_with_cd(
            "cd ~/stock-bot && grep -n 'composite.*enabled\\|use_composite' main.py | head -5",
            timeout=30
        )
        
        if stdout4:
            print(stdout4)
        
        print("\n" + "=" * 80)
        print("INVESTIGATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()
