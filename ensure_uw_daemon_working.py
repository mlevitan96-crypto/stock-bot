#!/usr/bin/env python3
"""
Ensure UW Daemon is Working and Creating Cache
Monitors daemon and ensures cache is created.
"""

from droplet_client import DropletClient
import time
import json

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("ENSURING UW DAEMON IS WORKING")
        print("=" * 80)
        print()
        
        # 1. Kill any existing daemons
        print("Step 1: Stopping any existing daemons...")
        client.execute_command("pkill -f uw_flow_daemon", timeout=10)
        time.sleep(2)
        print("[OK] Stopped")
        print()
        
        # 2. Ensure data directory exists
        print("Step 2: Ensuring data directory exists...")
        result = client.execute_command("cd ~/stock-bot && mkdir -p data && ls -ld data", timeout=10)
        print("[OK] Data directory ready")
        print()
        
        # 3. Start daemon with venv
        print("Step 3: Starting UW daemon...")
        result = client.execute_command(
            "cd ~/stock-bot && nohup venv/bin/python3 uw_flow_daemon.py > logs/uw_flow_daemon.log 2>&1 &",
            timeout=10
        )
        time.sleep(5)
        print("[OK] Daemon start command executed")
        print()
        
        # 4. Verify daemon is running
        print("Step 4: Verifying daemon is running...")
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        if result['stdout'].strip():
            print("[OK] Daemon is running")
            print(f"  {result['stdout'].strip()[:100]}")
        else:
            print("[FAIL] Daemon not running")
            # Check logs
            result_logs = client.execute_command("cd ~/stock-bot && tail -50 logs/uw_flow_daemon.log 2>&1", timeout=10)
            print("  Logs:")
            print(f"  {result_logs['stdout'][:1000]}")
        print()
        
        # 5. Wait for cache to be created (up to 2 minutes)
        print("Step 5: Waiting for cache file to be created...")
        cache_created = False
        for i in range(24):  # 2 minutes
            result = client.execute_command("cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1", timeout=10)
            if "No such file" not in result['stdout']:
                cache_created = True
                print(f"[OK] Cache file created after {i*5} seconds")
                print(f"  {result['stdout'].strip()}")
                break
            if i % 6 == 0:  # Every 30 seconds
                print(f"  Still waiting... ({i*5}s)")
            time.sleep(5)
        
        if not cache_created:
            print("[WARNING] Cache file not created after 2 minutes")
            print("  Checking daemon logs for errors...")
            result_logs = client.execute_command("cd ~/stock-bot && tail -100 logs/uw_flow_daemon.log 2>&1", timeout=10)
            print(f"  {result_logs['stdout'][:1500]}")
        print()
        
        # 6. If cache exists, check content
        if cache_created:
            print("Step 6: Checking cache content...")
            result = client.execute_command(
                "cd ~/stock-bot && python3 << 'PYEOF'\n"
                "import json\n"
                "with open('data/uw_flow_cache.json') as f:\n"
                "    cache = json.load(f)\n"
                "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
                "print(f'Symbols in cache: {len(symbols)}')\n"
                "if symbols:\n"
                "    print(f'Sample: {symbols[:10]}')\n"
                "    # Check if symbols have data\n"
                "    sample = symbols[0]\n"
                "    data = cache.get(sample, {})\n"
                "    has_sentiment = bool(data.get('sentiment'))\n"
                "    has_conviction = bool(data.get('conviction'))\n"
                "    print(f'Sample symbol ({sample}): sentiment={has_sentiment}, conviction={has_conviction}')\n"
                "PYEOF",
                timeout=30
            )
            print(result['stdout'])
        print()
        
        # 7. Final status
        print("=" * 80)
        print("FINAL STATUS")
        print("=" * 80)
        
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        daemon_running = bool(result['stdout'].strip())
        
        result = client.execute_command("cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1", timeout=10)
        cache_exists = "No such file" not in result['stdout']
        
        print(f"UW Daemon: {'[OK]' if daemon_running else '[FAIL]'}")
        print(f"Cache File: {'[OK]' if cache_exists else '[FAIL]'}")
        
        if daemon_running and cache_exists:
            print("\n[SUCCESS] UW daemon is working and cache is being populated!")
            print("Bot should be able to generate signals and open positions.")
        else:
            print("\n[WARNING] Issues detected - review logs above")
        
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

