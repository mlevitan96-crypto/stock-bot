#!/usr/bin/env python3
"""
Fix UW Daemon and Verify Cache Population
Ensures UW daemon is running and cache is being populated.
"""

from droplet_client import DropletClient
import json
import time

def main():
    print("=" * 80)
    print("FIXING UW DAEMON AND VERIFYING CACHE")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Kill any existing daemon processes
        print("Step 1: Stopping any existing UW daemon processes...")
        result = client.execute_command("pkill -f uw_flow_daemon", timeout=10)
        time.sleep(2)
        print("[OK] Existing processes stopped")
        print()
        
        # Step 2: Verify virtual environment and dependencies
        print("Step 2: Verifying virtual environment...")
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 -c 'import dotenv; print(\"OK\")'",
            timeout=30
        )
        if result['success']:
            print("[OK] Virtual environment and dependencies OK")
        else:
            print(f"[WARNING] Dependency check: {result['stderr']}")
        print()
        
        # Step 3: Start UW daemon in virtual environment
        print("Step 3: Starting UW daemon in virtual environment...")
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && nohup python3 uw_flow_daemon.py > logs/uw_flow_daemon.log 2>&1 &",
            timeout=10
        )
        time.sleep(5)  # Give it time to start
        print("[OK] Daemon start command executed")
        print()
        
        # Step 4: Verify daemon is running
        print("Step 4: Verifying daemon is running...")
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        if result['stdout'].strip():
            print("[OK] UW daemon is running")
            print(f"  {result['stdout'].strip()}")
        else:
            print("[WARNING] UW daemon not found in process list")
            # Check logs for errors
            result_logs = client.execute_command("cd ~/stock-bot && tail -30 logs/uw_flow_daemon.log 2>&1", timeout=10)
            if result_logs['stdout']:
                print("  Recent logs:")
                print(f"  {result_logs['stdout'][:500]}")
        print()
        
        # Step 5: Wait for cache file to be created
        print("Step 5: Waiting for cache file to be created...")
        cache_created = False
        for i in range(12):  # Wait up to 60 seconds
            result = client.execute_command("cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1", timeout=10)
            if "No such file" not in result['stdout']:
                cache_created = True
                print(f"[OK] Cache file exists after {i*5} seconds")
                print(f"  {result['stdout'].strip()}")
                break
            time.sleep(5)
        
        if not cache_created:
            print("[WARNING] Cache file not created after 60 seconds")
            print("  Checking daemon logs for errors...")
            result_logs = client.execute_command("cd ~/stock-bot && tail -50 logs/uw_flow_daemon.log 2>&1", timeout=10)
            if result_logs['stdout']:
                print(f"  {result_logs['stdout'][:1000]}")
        print()
        
        # Step 6: Check cache content
        if cache_created:
            print("Step 6: Checking cache content...")
            result = client.execute_command(
                "cd ~/stock-bot && python3 -c \""
                "import json; "
                "with open('data/uw_flow_cache.json') as f: "
                "  cache = json.load(f); "
                "  symbols = [k for k in cache.keys() if not k.startswith('_')]; "
                "  print(f'Symbols in cache: {len(symbols)}'); "
                "  if symbols: print(f'Sample: {symbols[:5]}')\"",
                timeout=30
            )
            if result['stdout']:
                print(f"  {result['stdout']}")
        print()
        
        # Step 7: Final status
        print("=" * 80)
        print("FINAL STATUS")
        print("=" * 80)
        
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        daemon_running = bool(result['stdout'].strip())
        
        result = client.execute_command("cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1", timeout=10)
        cache_exists = "No such file" not in result['stdout']
        
        print(f"UW Daemon Running: {'[OK]' if daemon_running else '[FAIL]'}")
        print(f"Cache File Exists: {'[OK]' if cache_exists else '[FAIL]'}")
        
        if daemon_running and cache_exists:
            print("\n[SUCCESS] UW daemon is running and cache is being populated!")
        else:
            print("\n[WARNING] Issues detected - check logs above")
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

