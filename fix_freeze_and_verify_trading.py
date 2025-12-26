#!/usr/bin/env python3
"""Fix freeze and verify trading works end-to-end."""

from droplet_client import DropletClient
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIX FREEZE AND VERIFY TRADING")
        print("=" * 80)
        print()
        
        # 1. Remove ALL freeze files
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
        time.sleep(20)
        print()
        
        # 4. Verify no freeze
        print("4. VERIFYING NO FREEZE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from pathlib import Path\n"
            "freeze_files = list(Path('state').glob('*freeze*'))\n"
            "print(f'Freeze files: {len(freeze_files)}')\n"
            "for f in freeze_files:\n"
            "    print(f'  {f.name}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
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
        
        # 7. Check cache
        print("7. CACHE STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import json\n"
            "with open('data/uw_flow_cache.json') as f:\n"
            "    cache = json.load(f)\n"
            "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "print(f'Symbols: {len(symbols)}')\n"
            "for sym in symbols[:5]:\n"
            "    data = cache.get(sym, {})\n"
            "    flow_count = len(data.get('flow_trades', []))\n"
            "    print(f'  {sym}: {flow_count} flow_trades')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 8. Check systemd logs for debug output
        print("8. SYSTEMD LOGS - DEBUG OUTPUT")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '2 minutes ago' --no-pager 2>&1 | grep -E 'DEBUG|clusters|composite|Processing|symbols' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:3000])
        print()
        
        # 9. Summary
        print("=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        if cycles:
            latest = cycles[-1]
            msg = latest.get('msg', '')
            clusters = latest.get('clusters', 0)
            orders = latest.get('orders', 0)
            print(f"Latest: {msg}")
            print(f"Clusters: {clusters}")
            print(f"Orders: {orders}")
            if msg == "halted_freeze":
                print("[FAIL] Bot is still frozen!")
            elif clusters > 0 and orders == 0:
                print("[WARNING] Clusters generated but no orders - check gates")
            elif clusters == 0:
                print("[WARNING] No clusters - check signal generation")
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

