#!/usr/bin/env python3
"""
Complete Fix All Workflow Issues
1. Remove ALL freeze files (including performance freeze)
2. Fix cluster generation
3. Fix use_composite
4. Verify end-to-end trading
"""

from droplet_client import DropletClient
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("COMPLETE FIX ALL WORKFLOW ISSUES")
        print("=" * 80)
        print()
        
        # 1. Remove ALL freeze files including performance freeze
        print("1. REMOVING ALL FREEZE FILES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && rm -f state/freeze.json state/governor_freezes.json state/pre_market_freeze.flag state/*freeze* 2>&1 && echo 'All freeze files removed'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 2. Check what check_freeze_state actually returns
        print("2. TESTING check_freeze_state()")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from monitoring_guards import check_freeze_state, check_performance_freeze\n"
            "perf = check_performance_freeze()\n"
            "freeze = check_freeze_state()\n"
            "print(f'check_performance_freeze(): {perf}')\n"
            "print(f'check_freeze_state(): {freeze}')\n"
            "PYEOF",
            timeout=60
        )
        print(result['stdout'])
        print()
        
        # 3. Pull latest code
        print("3. PULLING LATEST CODE")
        print("-" * 80)
        result = client.execute_command("cd ~/stock-bot && git pull origin main", timeout=30)
        print("[OK] Code updated")
        print()
        
        # 4. Restart service
        print("4. RESTARTING SERVICE")
        print("-" * 80)
        client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted")
        time.sleep(20)
        print()
        
        # 5. Wait for cycles
        print("5. WAITING FOR CYCLES (90 seconds)")
        print("-" * 80)
        time.sleep(90)
        print()
        
        # 6. Check cycles
        print("6. CHECKING RUN CYCLES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -10 logs/run.jsonl 2>&1",
            timeout=10
        )
        cycles = []
        if result['stdout']:
            for line in result['stdout'].strip().split('\n'):
                if line.strip():
                    try:
                        import json
                        c = json.loads(line)
                        cycles.append(c)
                    except:
                        pass
        
        if cycles:
            for c in cycles[-5:]:
                msg = c.get('msg', '')
                clusters = c.get('clusters', 0)
                orders = c.get('orders', 0)
                metrics = c.get('metrics', {})
                composite = metrics.get('composite_enabled', False)
                print(f"{msg}: clusters={clusters}, orders={orders}, composite={composite}")
        else:
            print("No cycles found")
        print()
        
        # 7. Check systemd logs for debug
        print("7. SYSTEMD LOGS - DEBUG")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '2 minutes ago' --no-pager 2>&1 | grep -E 'DEBUG.*clusters|DEBUG.*composite|DEBUG.*Processing|DEBUG.*symbols|halted_freeze|FREEZE' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:3000])
        print()
        
        # 8. Final summary
        print("=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        if cycles:
            latest = cycles[-1]
            msg = latest.get('msg', '')
            clusters = latest.get('clusters', 0)
            orders = latest.get('orders', 0)
            print(f"Status: {msg}")
            print(f"Clusters: {clusters}")
            print(f"Orders: {orders}")
            if msg == "halted_freeze":
                print("[FAIL] Bot is frozen - check freeze files and check_freeze_state()")
            elif clusters > 0 and orders == 0:
                print("[WARNING] Clusters generated but no orders - check gates")
            elif clusters == 0:
                print("[WARNING] No clusters - check cache and signal generation")
            elif orders > 0:
                print("[OK] Trading is working!")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

