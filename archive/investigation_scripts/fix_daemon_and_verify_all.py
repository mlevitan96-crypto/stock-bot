#!/usr/bin/env python3
"""
Fix Daemon Exit Issue and Verify Everything Works
"""

from droplet_client import DropletClient
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIXING DAEMON AND VERIFYING ALL")
        print("=" * 80)
        print()
        
        # 1. Check current daemon status
        print("1. CURRENT STATUS")
        print("-" * 80)
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        print("UW daemon:" if result['stdout'] else "UW daemon: NOT RUNNING")
        print(result['stdout'][:200] if result['stdout'] else '')
        print()
        
        # 2. Check daemon output from supervisor
        print("2. CHECKING DAEMON OUTPUT FROM SUPERVISOR")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && journalctl -u trading-bot.service --since '5 minutes ago' --no-pager 2>&1 | grep -A 5 -B 5 'uw-daemon' | tail -40",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:2500])
        print()
        
        # 3. Try starting daemon manually to see error
        print("3. TESTING MANUAL DAEMON START")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && timeout 15 python uw_flow_daemon.py 2>&1 | head -50",
            timeout=20
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:2000])
        print()
        
        # 4. Check if API key issue
        print("4. CHECKING ENVIRONMENT")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "print(f'UW_API_KEY: {\"SET\" if os.getenv(\"UW_API_KEY\") else \"NOT SET\"}')\n"
            "print(f'ALPACA_KEY: {\"SET\" if os.getenv(\"ALPACA_KEY\") else \"NOT SET\"}')\n"
            "print(f'ALPACA_SECRET: {\"SET\" if os.getenv(\"ALPACA_SECRET\") else \"NOT SET\"}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 5. Restart service and wait
        print("5. RESTARTING SERVICE AND WAITING")
        print("-" * 80)
        client.execute_command("systemctl restart trading-bot.service", timeout=10)
        print("[OK] Service restarted")
        print("Waiting 20 seconds for daemon to start...")
        time.sleep(20)
        print()
        
        # 6. Verify daemon is running
        print("6. VERIFYING DAEMON")
        print("-" * 80)
        result = client.execute_command("ps aux | grep uw_flow_daemon | grep -v grep", timeout=10)
        if result['stdout'].strip():
            print("[OK] UW daemon is running")
            print(f"  {result['stdout'].strip()[:120]}")
        else:
            print("[FAIL] UW daemon still not running")
        print()
        
        # 7. Verify cache
        print("7. VERIFYING CACHE")
        print("-" * 80)
        time.sleep(30)  # Wait for cache
        result = client.execute_command(
            "cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 8. Verify no freeze
        print("8. VERIFYING NO FREEZE")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from pathlib import Path\n"
            "import json\n"
            "freeze_files = list(Path('state').glob('*freeze*'))\n"
            "print(f'Freeze files: {len(freeze_files)}')\n"
            "for f in freeze_files:\n"
            "    print(f'  {f.name}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 9. Final verification
        print("=" * 80)
        print("FINAL VERIFICATION")
        print("=" * 80)
        result = client.execute_command("systemctl status trading-bot.service --no-pager | head -20", timeout=10)
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output)
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

