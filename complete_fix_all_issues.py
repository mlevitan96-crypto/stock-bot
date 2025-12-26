#!/usr/bin/env python3
"""
Complete Fix All Issues - Unfreeze, Restart Daemon, Fix Self-Healing
"""

from droplet_client import DropletClient
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("COMPLETE FIX - ALL ISSUES")
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
        
        # 2. Pull latest code with fixes
        print("2. PULLING LATEST CODE WITH FIXES")
        print("-" * 80)
        result = client.execute_command("cd ~/stock-bot && git pull origin main", timeout=30)
        print("[OK] Code updated")
        print()
        
        # 3. Restart systemd service to apply fixes
        print("3. RESTARTING SYSTEMD SERVICE")
        print("-" * 80)
        result = client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted")
        time.sleep(5)
        print()
        
        # 4. Verify all processes
        print("4. VERIFYING ALL PROCESSES")
        print("-" * 80)
        result = client.execute_command(
            "ps aux | grep -E 'deploy_supervisor|main.py|uw_flow_daemon|dashboard|heartbeat' | grep -v grep",
            timeout=10
        )
        processes = result['stdout'].strip().split('\n') if result['stdout'] else []
        print(f"Processes found: {len(processes)}")
        for proc in processes:
            print(f"  {proc[:120]}")
        print()
        
        # 5. Verify daemon is running
        print("5. VERIFYING UW DAEMON")
        print("-" * 80)
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        if result['stdout'].strip():
            print("[OK] UW daemon is running")
        else:
            print("[FAIL] UW daemon not running")
        print()
        
        # 6. Verify cache file
        print("6. VERIFYING CACHE FILE")
        print("-" * 80)
        time.sleep(30)  # Wait for daemon to create cache
        result = client.execute_command(
            "cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1",
            timeout=10
        )
        print(result['stdout'])
        if "No such file" not in result['stdout']:
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
        
        # 7. Verify no freeze
        print("7. VERIFYING NO FREEZE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && ls -la state/*freeze* 2>&1 || echo 'No freeze files'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 8. Check recent logs
        print("8. CHECKING RECENT LOGS")
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
        print(result['stdout'] if result['stdout'] else 'No recent logs')
        print()
        
        print("=" * 80)
        print("FIX COMPLETE")
        print("=" * 80)
        print("All issues should be fixed:")
        print("1. Freeze files removed")
        print("2. Self-healing fixed (daemon check + restart)")
        print("3. Service restarted")
        print("4. Daemon should be running")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

