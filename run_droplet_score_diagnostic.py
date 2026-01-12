#!/usr/bin/env python3
"""
Run comprehensive score diagnostic on droplet and analyze results.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from droplet_client import DropletClient
except ImportError as e:
    print(f"ERROR: Could not import droplet_client: {e}")
    sys.exit(1)

def main():
    print("=" * 80)
    print("RUNNING COMPREHENSIVE SCORE DIAGNOSTIC ON DROPLET")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Pull latest code
        print("Step 1: Pulling latest code...")
        result = client.execute_command(
            "git fetch origin main && git reset --hard origin/main",
            timeout=120
        )
        if result.get('success'):
            print("[OK] Code pulled")
        else:
            print(f"[WARNING] {result.get('stderr', 'Unknown error')[:200]}")
        print()
        
        # Step 2: Run comprehensive diagnostic
        print("Step 2: Running comprehensive score diagnostic...")
        result = client.execute_command(
            "python3 comprehensive_score_diagnostic.py",
            timeout=600
        )
        
        print("\n" + "=" * 80)
        print("DIAGNOSTIC OUTPUT")
        print("=" * 80)
        stdout = result.get('stdout', '')
        stderr = result.get('stderr', '')
        
        # Print output
        try:
            # Try to handle encoding
            print(stdout.encode('ascii', errors='replace').decode('ascii', errors='replace'))
        except:
            print(stdout)
        
        if stderr:
            print("\n" + "=" * 80)
            print("ERRORS")
            print("=" * 80)
            try:
                print(stderr.encode('ascii', errors='replace').decode('ascii', errors='replace'))
            except:
                print(stderr)
        
        # Step 3: Get sample cache data for analysis
        print("\n" + "=" * 80)
        print("Step 3: Getting sample cache data...")
        print("=" * 80)
        
        result2 = client.execute_command(
            """python3 -c "
import json
cache = json.load(open('data/uw_flow_cache.json'))
syms = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'SPY', 'QQQ', 'META', 'GOOGL']
print('Symbol Data:')
for s in syms:
    if s in cache:
        d = cache[s]
        print(f'{s}:')
        print(f'  sentiment: {d.get(\"sentiment\", \"MISSING\")}')
        print(f'  conviction: {d.get(\"conviction\", 0):.3f}')
        print(f'  freshness: {d.get(\"freshness\", 1.0):.3f}')
        print(f'  dark_pool: {bool(d.get(\"dark_pool\"))}')
        print(f'  insider: {bool(d.get(\"insider\"))}')
        print(f'  iv_term_skew: {d.get(\"iv_term_skew\", \"MISSING\")}')
        print(f'  smile_slope: {d.get(\"smile_slope\", \"MISSING\")}')
        print()
" """,
            timeout=30
        )
        print(result2.get('stdout', 'No data'))
        
        # Step 4: Check recent log entries for scores
        print("\n" + "=" * 80)
        print("Step 4: Recent score entries from logs...")
        print("=" * 80)
        
        result3 = client.execute_command(
            "tail -1000 logs/trading.log | grep -E 'composite_score|score=' | tail -20",
            timeout=30
        )
        print(result3.get('stdout', 'No scores found'))
        
    except Exception as e:
        print(f"\n[ERROR] Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
