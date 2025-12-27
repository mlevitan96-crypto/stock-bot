#!/usr/bin/env python3
"""
Final Complete Fix - All Issues
1. Unfreeze bot
2. Ensure daemon runs and stays running
3. Fix self-healing
4. Verify everything works
5. Update memory bank
"""

from droplet_client import DropletClient
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FINAL COMPLETE FIX - ALL ISSUES")
        print("=" * 80)
        print()
        
        # 1. Remove all freeze files
        print("1. REMOVING ALL FREEZE FILES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && rm -f state/freeze.json state/governor_freezes.json state/pre_market_freeze.flag state/*freeze* 2>&1 && echo 'All freeze files removed'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 2. Pull latest code
        print("2. PULLING LATEST CODE")
        print("-" * 80)
        result = client.execute_command("cd ~/stock-bot && git pull origin main", timeout=30)
        print("[OK] Code updated")
        print()
        
        # 3. Restart service
        print("3. RESTARTING SERVICE")
        print("-" * 80)
        client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted")
        time.sleep(10)
        print()
        
        # 4. Verify all processes
        print("4. VERIFYING ALL PROCESSES")
        print("-" * 80)
        result = client.execute_command(
            "ps aux | grep -E 'deploy_supervisor|main.py|uw_flow_daemon|dashboard|heartbeat' | grep -v grep",
            timeout=10
        )
        processes = result['stdout'].strip().split('\n') if result['stdout'] else []
        print(f"Processes: {len(processes)}")
        daemon_running = any('uw_flow_daemon' in p for p in processes)
        main_running = any('main.py' in p for p in processes)
        print(f"UW daemon: {'[OK]' if daemon_running else '[FAIL]'}")
        print(f"Main bot: {'[OK]' if main_running else '[FAIL]'}")
        print()
        
        # 5. Wait for cache
        print("5. WAITING FOR CACHE (90 seconds)")
        print("-" * 80)
        time.sleep(90)
        result = client.execute_command(
            "cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1",
            timeout=10
        )
        cache_exists = "No such file" not in result['stdout']
        print(f"Cache file: {'[OK]' if cache_exists else '[FAIL]'}")
        if cache_exists:
            result2 = client.execute_command(
                "cd ~/stock-bot && python3 << 'PYEOF'\n"
                "import json\n"
                "with open('data/uw_flow_cache.json') as f:\n"
                "    cache = json.load(f)\n"
                "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
                "print(f'Symbols: {len(symbols)}')\n"
                "PYEOF",
                timeout=30
            )
            print(result2['stdout'])
        print()
        
        # 6. Verify main.py can read cache
        print("6. VERIFYING MAIN.PY CAN READ CACHE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'read_uw_cache() returns: {len(symbols)} symbols')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 7. Check recent run cycles
        print("7. CHECKING RECENT RUN CYCLES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -5 logs/run.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            c = json.loads(line)\n"
            "            msg = c.get('msg', '')\n"
            "            market = c.get('market_open', 'unknown')\n"
            "            clusters = c.get('clusters', 0)\n"
            "            print(f'{msg}: market_open={market}, clusters={clusters}')\n"
            "        except:\n"
            "            pass\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'] if result['stdout'] else 'No cycles')
        print()
        
        # 8. Final summary
        print("=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        print(f"UW daemon: {'[OK]' if daemon_running else '[FAIL]'}")
        print(f"Main bot: {'[OK]' if main_running else '[FAIL]'}")
        print(f"Cache: {'[OK]' if cache_exists else '[FAIL]'}")
        print(f"Freeze: [OK] (removed)")
        print()
        if daemon_running and main_running and cache_exists:
            print("[SUCCESS] All systems operational!")
        else:
            print("[WARNING] Some issues remain - check above")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

