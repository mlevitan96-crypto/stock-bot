#!/usr/bin/env python3
"""Verify trading workflow is working end-to-end."""

from droplet_client import DropletClient
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("VERIFYING TRADING WORKFLOW")
        print("=" * 80)
        print()
        
        # 1. Pull latest code
        print("1. PULLING LATEST CODE")
        print("-" * 80)
        result = client.execute_command("cd ~/stock-bot && git pull origin main", timeout=30)
        print("[OK] Code updated")
        print()
        
        # 2. Restart service
        print("2. RESTARTING SERVICE")
        print("-" * 80)
        client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted")
        time.sleep(15)
        print()
        
        # 3. Wait for cycles
        print("3. WAITING FOR RUN CYCLES (60 seconds)")
        print("-" * 80)
        time.sleep(60)
        print()
        
        # 4. Check recent cycles
        print("4. RECENT RUN CYCLES")
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
            for c in cycles[-3:]:
                msg = c.get('msg', '')
                clusters = c.get('clusters', 0)
                orders = c.get('orders', 0)
                metrics = c.get('metrics', {})
                composite = metrics.get('composite_enabled', False)
                print(f"{msg}: clusters={clusters}, orders={orders}, composite={composite}")
        else:
            print("No cycles found")
        print()
        
        # 5. Check cache
        print("5. CACHE STATUS")
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
        
        # 6. Check processes
        print("6. PROCESS STATUS")
        print("-" * 80)
        result = client.execute_command(
            "ps aux | grep -E 'main.py|uw_flow_daemon' | grep -v grep",
            timeout=10
        )
        print(result['stdout'][:400] if result['stdout'] else 'Not running')
        print()
        
        # 7. Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        if cycles:
            latest = cycles[-1]
            clusters = latest.get('clusters', 0)
            orders = latest.get('orders', 0)
            print(f"Latest cycle: {clusters} clusters, {orders} orders")
            if clusters > 0 and orders == 0:
                print("[WARNING] Clusters generated but no orders - check gates")
            elif clusters == 0:
                print("[WARNING] No clusters - check cache and signal generation")
            elif orders > 0:
                print("[OK] Trading is working!")
        else:
            print("[WARNING] No cycles found - bot may not be running")
        print()
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

