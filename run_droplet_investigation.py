#!/usr/bin/env python3
"""Run comprehensive investigation on droplet via SSH."""

from droplet_client import DropletClient
import json

def main():
    print("=" * 80)
    print("RUNNING COMPREHENSIVE INVESTIGATION ON DROPLET")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Pull latest code
        print("Step 1: Pulling latest code from Git...")
        result = client.execute_command("cd ~/stock-bot && git pull origin main", timeout=60)
        if result['success']:
            print("[OK] Code pulled successfully")
        else:
            print(f"[WARNING] Git pull had issues: {result['stderr'][:200]}")
        print()
        
        # Step 2: Run investigation
        print("Step 2: Running comprehensive investigation...")
        result = client.execute_command(
            "cd ~/stock-bot && python3 comprehensive_no_positions_investigation.py",
            timeout=180
        )
        
        print("\n" + "=" * 80)
        print("INVESTIGATION OUTPUT")
        print("=" * 80)
        print(result['stdout'])
        
        if result['stderr']:
            print("\n" + "=" * 80)
            print("ERRORS")
            print("=" * 80)
            print(result['stderr'])
        
        # Step 2b: Run additional diagnostics
        print("\n" + "=" * 80)
        print("Step 2b: Running additional diagnostics...")
        result2 = client.execute_command(
            "cd ~/stock-bot && python3 fix_no_positions_issues.py",
            timeout=120
        )
        
        print("\n" + "=" * 80)
        print("ADDITIONAL DIAGNOSTICS OUTPUT")
        print("=" * 80)
        print(result2['stdout'])
        
        if result2['stderr']:
            print("\n" + "=" * 80)
            print("ERRORS")
            print("=" * 80)
            print(result2['stderr'])
        
        print("\n" + "=" * 80)
        print("INVESTIGATION OUTPUT")
        print("=" * 80)
        print(result['stdout'])
        
        if result['stderr']:
            print("\n" + "=" * 80)
            print("ERRORS")
            print("=" * 80)
            print(result['stderr'])
        
        # Step 3: Get investigation results
        print("\n" + "=" * 80)
        print("Step 3: Retrieving investigation results...")
        result = client.execute_command(
            "cd ~/stock-bot && cat investigate_no_positions.json",
            timeout=30
        )
        
        if result['success'] and result['stdout']:
            try:
                data = json.loads(result['stdout'])
                print("\n" + "=" * 80)
                print("INVESTIGATION RESULTS SUMMARY")
                print("=" * 80)
                print(f"Timestamp: {data.get('timestamp')}")
                print(f"Processes found: {len(data.get('processes', []))}")
                positions = data.get('positions', {})
                open_pos = len([p for p in positions.values() if p.get('status') == 'open']) if positions else 0
                print(f"Open positions: {open_pos}")
                print(f"Recent signals: {len(data.get('signals', []))}")
                print(f"Blocked trades (last 50): {len(data.get('blocked_trades', []))}")
                print(f"Errors in logs: {len(data.get('log_errors', []))}")
            except:
                print("Could not parse JSON results")
        
        # Step 4: Check if results were pushed to Git
        print("\n" + "=" * 80)
        print("Step 4: Checking if results need to be pushed to Git...")
        result = client.execute_command(
            "cd ~/stock-bot && git status --short | grep investigate_no_positions",
            timeout=30
        )
        if result['stdout'].strip():
            print("[INFO] Results file has changes, committing...")
            commit_result = client.execute_command(
                "cd ~/stock-bot && git add investigate_no_positions.json && git commit -m 'Investigation results - no positions diagnosis' && git push origin main",
                timeout=60
            )
            if commit_result['success']:
                print("[OK] Results pushed to Git")
            else:
                print(f"[WARNING] Failed to push: {commit_result['stderr'][:200]}")
        else:
            print("[INFO] No changes to commit")
        
    except Exception as e:
        print(f"[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
    
    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()

