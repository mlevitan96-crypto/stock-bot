#!/usr/bin/env python3
"""
Comprehensive Diagnosis and Fix - Find and Fix ALL Issues
No assumptions - check everything and fix what's broken.
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("COMPREHENSIVE DIAGNOSIS - FINDING ALL ISSUES")
        print("=" * 80)
        print()
        
        # 1. Check systemd service
        print("1. SYSTEMD SERVICE STATUS")
        print("-" * 80)
        result = client.execute_command("systemctl status trading-bot.service --no-pager | head -20", timeout=10)
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output)
        print()
        
        # 2. Check all processes
        print("2. ALL PROCESSES CHECK")
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
        
        # 3. Check UW daemon specifically
        print("3. UW DAEMON DETAILED CHECK")
        print("-" * 80)
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        if result['stdout'].strip():
            print("[OK] UW daemon process found")
            print(f"  {result['stdout'].strip()[:120]}")
        else:
            print("[FAIL] UW daemon NOT running")
        print()
        
        # 4. Check cache file
        print("4. CACHE FILE CHECK")
        print("-" * 80)
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
                "print(f'Symbols in cache: {len(symbols)}')\n"
                "if symbols:\n"
                "    print(f'Sample: {symbols[:10]}')\n"
                "PYEOF",
                timeout=30
            )
            print(result2['stdout'])
        print()
        
        # 5. Check main.py can read cache
        print("5. MAIN.PY CACHE READ CHECK")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from main import read_uw_cache\n"
            "cache = read_uw_cache()\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'read_uw_cache() returns: {len(symbols)} symbols')\n"
            "if symbols:\n"
            "    print(f'Sample: {symbols[:10]}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 6. Check recent run cycles
        print("6. RECENT RUN CYCLES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -10 logs/run.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            c = json.loads(line)\n"
            "            market = c.get('market_open', 'unknown')\n"
            "            clusters = c.get('clusters', 0)\n"
            "            orders = c.get('orders', 0)\n"
            "            print(f'market_open={market}, clusters={clusters}, orders={orders}')\n"
            "        except:\n"
            "            pass\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'] if result['stdout'] else 'No cycles found')
        print()
        
        # 7. Check self-healing status
        print("7. SELF-HEALING STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && ps aux | grep heartbeat | grep -v grep",
            timeout=10
        )
        if result['stdout'].strip():
            print("[OK] Heartbeat keeper running")
            print(f"  {result['stdout'].strip()[:120]}")
        else:
            print("[FAIL] Heartbeat keeper NOT running")
        print()
        
        # 8. Check dashboard health endpoint
        print("8. DASHBOARD HEALTH CHECK")
        print("-" * 80)
        result = client.execute_command(
            "curl -s http://localhost:5000/api/sre/health 2>&1 | python3 -m json.tool 2>&1 | head -30",
            timeout=10
        )
        print(result['stdout'][:1000] if result['stdout'] else 'Dashboard not responding')
        print()
        
        # 9. Check daemon logs for errors
        print("9. UW DAEMON LOGS (LAST 30 LINES)")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -30 logs/uw_flow_daemon.log 2>&1 | tail -20",
            timeout=10
        )
        print(result['stdout'][:1500] if result['stdout'] else 'No daemon logs')
        print()
        
        # 10. Check main.py logs for errors
        print("10. MAIN.PY RECENT LOGS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -20 logs/run.jsonl 2>&1 | tail -10",
            timeout=10
        )
        print(result['stdout'][:1000] if result['stdout'] else 'No main.py logs')
        print()
        
        # 11. Summary and fixes needed
        print("=" * 80)
        print("DIAGNOSIS SUMMARY")
        print("=" * 80)
        
        # Determine what's broken
        issues = []
        if not result['stdout'] or 'uw_flow_daemon' not in str(result['stdout']):
            issues.append("UW daemon not running")
        if "No such file" in result['stdout']:
            issues.append("Cache file missing")
        
        if issues:
            print("ISSUES FOUND:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("All checks passed - investigating further...")
        print()
        
    except Exception as e:
        print(f"[ERROR] Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

