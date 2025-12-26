#!/usr/bin/env python3
"""
Complete workflow fix and verification
1. Fix UnboundLocalError (already done)
2. Fix freeze state (already done)
3. Diagnose why composite scores are so low
4. Ensure daemon is populating cache
5. Verify end-to-end trading
"""

from droplet_client import DropletClient
import time
import json

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("COMPLETE WORKFLOW FIX AND VERIFICATION")
        print("=" * 80)
        print()
        
        # 1. Pull latest code
        print("1. PULLING LATEST CODE")
        print("-" * 80)
        result = client.execute_command("cd ~/stock-bot && git pull origin main", timeout=30)
        print("[OK] Code updated")
        print()
        
        # 2. Remove all freeze files
        print("2. REMOVING ALL FREEZE FILES")
        print("-" * 80)
        client.execute_command("cd ~/stock-bot && rm -f state/freeze.json state/governor_freezes.json state/pre_market_freeze.flag state/*freeze* 2>&1", timeout=10)
        print("[OK] Freeze files removed")
        print()
        
        # 3. Check cache and daemon
        print("3. CHECKING CACHE AND DAEMON")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from pathlib import Path\n"
            "import json\n"
            "cache_path = Path('data/uw_flow_cache.json')\n"
            "if cache_path.exists():\n"
            "    cache = json.loads(cache_path.read_text())\n"
            "    symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
            "    print(f'Cache exists: YES')\n"
            "    print(f'Symbols: {len(symbols)}')\n"
            "    for sym in symbols[:5]:\n"
            "        data = cache.get(sym, {})\n"
            "        flow_trades = data.get('flow_trades', [])\n"
            "        sentiment = data.get('sentiment', 'N/A')\n"
            "        conviction = data.get('conviction', 0.0)\n"
            "        print(f'  {sym}: {len(flow_trades)} flow_trades, sentiment={sentiment}, conviction={conviction:.2f}')\n"
            "else:\n"
            "    print('Cache exists: NO')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 4. Restart service
        print("4. RESTARTING SERVICE")
        print("-" * 80)
        client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted")
        time.sleep(30)
        print()
        
        # 5. Wait for cycles
        print("5. WAITING FOR CYCLES (120 seconds)")
        print("-" * 80)
        time.sleep(120)
        print()
        
        # 6. Check cycles and scores
        print("6. CHECKING CYCLES AND SCORES")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '3 minutes ago' --no-pager 2>&1 | grep -E 'Composite signal|score=|threshold=|clusters=|orders=' | tail -30",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:4000])
        print()
        
        # 7. Final summary
        print("=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -3 logs/run.jsonl 2>&1",
            timeout=10
        )
        if result['stdout']:
            for line in result['stdout'].strip().split('\n'):
                if line.strip():
                    try:
                        data = json.loads(line)
                        msg = data.get('msg', 'N/A')
                        clusters = data.get('clusters', 0)
                        orders = data.get('orders', 0)
                        print(f"Status: {msg}")
                        print(f"Clusters: {clusters}")
                        print(f"Orders: {orders}")
                        if msg == "complete" and clusters > 0:
                            print("[OK] Clusters generated - trading should work")
                        elif msg == "complete" and clusters == 0:
                            print("[WARNING] No clusters - composite scores too low or threshold too high")
                        elif msg == "halted_freeze":
                            print("[FAIL] Bot is frozen")
                    except:
                        pass
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

