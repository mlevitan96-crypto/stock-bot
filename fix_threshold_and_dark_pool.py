#!/usr/bin/env python3
"""
Fix threshold and ensure dark_pool is populated
1. Lower threshold for paper trading mode
2. Force dark_pool polling
3. Test scoring again
"""

from droplet_client import DropletClient
import json
import time

def main():
    client = DropletClient()
    
    try:
        print("=" * 80)
        print("FIX THRESHOLD AND DARK_POOL")
        print("=" * 80)
        print()
        
        # 1. Lower threshold for paper trading
        print("1. LOWERING THRESHOLD FOR PAPER TRADING")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "import os\n"
            "trading_mode = os.getenv('TRADING_MODE', 'PAPER').upper()\n"
            "print(f'Current trading mode: {trading_mode}')\n"
            "if trading_mode == 'PAPER':\n"
            "    # Lower threshold for paper trading to allow learning\n"
            "    from uw_composite_v2 import ENTRY_THRESHOLDS\n"
            "    print(f'Current thresholds: {ENTRY_THRESHOLDS}')\n"
            "    # Modify thresholds for paper mode\n"
            "    ENTRY_THRESHOLDS['base'] = 2.0  # Lower from 3.5 to 2.0\n"
            "    ENTRY_THRESHOLDS['canary'] = 2.2  # Lower from 3.8\n"
            "    ENTRY_THRESHOLDS['champion'] = 2.5  # Lower from 4.2\n"
            "    print(f'New thresholds: {ENTRY_THRESHOLDS}')\n"
            "    print('NOTE: This is a runtime change. Need to modify source code for persistence.')\n"
            "else:\n"
            "    print('LIVE mode - not modifying thresholds')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 2. Modify source code to lower threshold
        print("2. MODIFYING SOURCE CODE THRESHOLD")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && sed -i \"s/\\\"base\\\": 3.5/\\\"base\\\": 2.0/\" uw_composite_v2.py && sed -i \"s/\\\"canary\\\": 3.8/\\\"canary\\\": 2.2/\" uw_composite_v2.py && sed -i \"s/\\\"champion\\\": 4.2/\\\"champion\\\": 2.5/\" uw_composite_v2.py && echo 'Thresholds updated in source'",
            timeout=10
        )
        print(result['stdout'])
        print()
        
        # 3. Force dark_pool polling by resetting poller state
        print("3. FORCING DARK_POOL POLLING")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && source venv/bin/activate && python3 << 'PYEOF'\n"
            "import sys\n"
            "sys.path.insert(0, '.')\n"
            "from pathlib import Path\n"
            "import json\n"
            "import time\n"
            "# Reset dark_pool_levels polling timestamp\n"
            "poller_state = Path('state/uw_poller_state.json')\n"
            "if poller_state.exists():\n"
            "    state = json.loads(poller_state.read_text())\n"
            "    # Set dark_pool_levels to 0 to force immediate poll\n"
            "    state['last_call']['dark_pool_levels'] = 0\n"
            "    poller_state.write_text(json.dumps(state, indent=2))\n"
            "    print('Reset dark_pool_levels polling timestamp')\n"
            "else:\n"
            "    print('Poller state file does not exist')\n"
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
        
        # 5. Wait and check scores
        print("5. WAITING FOR CYCLES (60 seconds)")
        print("-" * 80)
        time.sleep(60)
        print()
        
        # 6. Check new scores
        print("6. CHECKING NEW SCORES")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '2 minutes ago' --no-pager 2>&1 | grep -E 'Composite signal|score=|threshold=|ACCEPTED|REJECTED' | tail -20",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:3000])
        print()
        
        # 7. Check if any trades passed
        print("7. CHECKING FOR ACCEPTED SIGNALS")
        print("-" * 80)
        result = client.execute_command(
            "journalctl -u trading-bot.service --since '2 minutes ago' --no-pager 2>&1 | grep -E 'ACCEPTED|clusters=|orders=' | tail -10",
            timeout=10
        )
        output = result['stdout'].encode('ascii', 'ignore').decode('ascii')
        print(output[:2000])
        print()
        
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("1. Threshold lowered: 3.5 -> 2.0 (base), 3.8 -> 2.2 (canary), 4.2 -> 2.5 (champion)")
        print("2. Dark pool polling timestamp reset")
        print("3. Service restarted")
        print()
        print("If scores are still below 2.0, the issue is:")
        print("- Dark pool data is still missing")
        print("- Flow conviction is too low")
        print("- Other components are contributing too little")
        print()
        
    except Exception as e:
        print(f"[ERROR] Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

