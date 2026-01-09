#!/usr/bin/env python3
"""
Comprehensive Stagnation Diagnostic
Checks: Bot status, UW daemon, cache, signals, signal history, trade blocking
"""

import sys
from pathlib import Path

try:
    from droplet_client import DropletClient
except ImportError:
    print("ERROR: droplet_client not available")
    sys.exit(1)

def run_diagnostic():
    """Run comprehensive diagnostic on droplet."""
    print("=" * 80)
    print("COMPREHENSIVE STAGNATION DIAGNOSTIC")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Step 1: Check if bot is running
        print("Step 1: Checking if trading bot is running...")
        stdout, stderr, exit_code = client._execute(
            "ps aux | grep 'python.*main.py' | grep -v grep",
            timeout=10
        )
        if stdout.strip():
            print(f"[OK] Bot process is running")
            print(f"  {stdout.strip()[:150]}")
        else:
            print("[FAIL] Bot process NOT running!")
        print()
        
        # Step 2: Check if UW daemon is running
        print("Step 2: Checking if UW daemon is running...")
        stdout, stderr, exit_code = client._execute(
            "ps aux | grep -E 'uw_flow_daemon|uw_integration_full' | grep -v grep",
            timeout=10
        )
        if stdout.strip():
            print(f"[OK] UW daemon is running")
            print(f"  {stdout.strip()[:150]}")
        else:
            print("[FAIL] UW daemon NOT running!")
        print()
        
        # Step 3: Check UW cache status
        print("Step 3: Checking UW cache status...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && python3 -c \""
            "import json\n"
            "from pathlib import Path\n"
            "cache_file = Path('data/uw_flow_cache.json')\n"
            "if cache_file.exists():\n"
            "    cache = json.load(open(cache_file))\n"
            "    print(f'Cache exists: {len(cache)} symbols')\n"
            "    symbols_with_trades = [t for t, v in cache.items() if isinstance(v, dict) and v.get('flow_trades') and len(v.get('flow_trades', [])) > 0]\n"
            "    print(f'Symbols with flow_trades: {len(symbols_with_trades)}')\n"
            "    symbols_with_sentiment = [t for t, v in cache.items() if isinstance(v, dict) and (v.get('sentiment') or v.get('conviction'))]\n"
            "    print(f'Symbols with sentiment/conviction: {len(symbols_with_sentiment)}')\n"
            "    if symbols_with_sentiment:\n"
            "        sample = list(symbols_with_sentiment)[:3]\n"
            "        for s in sample:\n"
            "            v = cache[s]\n"
            "            print(f'  {s}: sentiment={v.get(\"sentiment\", \"N/A\")}, conviction={v.get(\"conviction\", 0.0):.2f}')\n"
            "else:\n"
            "    print('Cache file does not exist!')\n"
            "\"",
            timeout=30
        )
        if stdout:
            print(stdout)
        if stderr:
            print(f"[WARNING] {stderr[:200]}")
        print()
        
        # Step 4: Check signal history
        print("Step 4: Checking signal history...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && python3 -c \""
            "from pathlib import Path\n"
            "import json\n"
            "history_file = Path('state/signal_history.jsonl')\n"
            "if history_file.exists():\n"
            "    signals = []\n"
            "    with open(history_file, 'r') as f:\n"
            "        for line in f:\n"
            "            if line.strip():\n"
            "                try:\n"
            "                    signals.append(json.loads(line))\n"
            "                except:\n"
            "                    pass\n"
            "    print(f'Total signals in history: {len(signals)}')\n"
            "    if signals:\n"
            "        recent = signals[-10:]\n"
            "        print(f'Last 10 signals:')\n"
            "        for s in recent:\n"
            "            print(f'  {s.get(\"symbol\", \"N/A\")}: {s.get(\"decision\", \"N/A\")} (score={s.get(\"final_score\", 0.0):.2f})')\n"
            "    else:\n"
            "        print('No signals in history file')\n"
            "else:\n"
            "    print('Signal history file does not exist!')\n"
            "\"",
            timeout=30
        )
        if stdout:
            print(stdout)
        if stderr:
            print(f"[WARNING] {stderr[:200]}")
        print()
        
        # Step 5: Check recent bot logs for signal processing
        print("Step 5: Checking recent bot logs for signal processing...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && tail -100 logs/trading-bot-pc.log 2>/dev/null | grep -E 'Processing cluster|DEBUG.*Processing|clustering|composite scoring|signal' | tail -20",
            timeout=10
        )
        if stdout.strip():
            print("Recent signal processing activity:")
            print(stdout)
        else:
            print("[WARNING] No signal processing activity found in logs")
        print()
        
        # Step 6: Check for blocking gates
        print("Step 6: Checking for blocking gates in recent logs...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && tail -200 logs/trading-bot-pc.log 2>/dev/null | grep -E 'BLOCKED|Blocked|score_below|momentum|concentration|expectancy' | tail -15",
            timeout=10
        )
        if stdout.strip():
            print("Recent blocking events:")
            print(stdout)
        else:
            print("[INFO] No blocking events found in recent logs")
        print()
        
        # Step 7: Check UW daemon logs
        print("Step 7: Checking UW daemon logs...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && tail -50 logs/uw-daemon-pc.log 2>/dev/null | tail -20",
            timeout=10
        )
        if stdout.strip():
            print("Recent daemon activity:")
            print(stdout)
        else:
            print("[WARNING] No daemon log found or empty")
        print()
        
        # Step 8: Check systemd service status
        print("Step 8: Checking systemd service status...")
        stdout, stderr, exit_code = client._execute(
            "systemctl status trading-bot.service --no-pager -l | head -30",
            timeout=15
        )
        if stdout:
            # Handle encoding
            try:
                safe_output = stdout.encode('ascii', errors='replace').decode('ascii', errors='replace')
                print(safe_output)
            except:
                print(stdout[:500])
        print()
        
        # Step 9: Check if market is open
        print("Step 9: Checking market status...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && python3 -c \""
            "from datetime import datetime, timezone\n"
            "import pytz\n"
            "now = datetime.now(pytz.timezone('America/New_York'))\n"
            "hour = now.hour\n"
            "minute = now.minute\n"
            "is_weekday = now.weekday() < 5\n"
            "is_market_hours = (hour == 9 and minute >= 30) or (9 < hour < 16) or (hour == 16 and minute == 0)\n"
            "market_open = is_weekday and is_market_hours\n"
            "print(f'Current time (ET): {now.strftime(\"%Y-%m-%d %H:%M:%S %Z\")}')\n"
            "print(f'Is weekday: {is_weekday}')\n"
            "print(f'Is market hours: {is_market_hours}')\n"
            "print(f'Market should be open: {market_open}')\n"
            "\"",
            timeout=15
        )
        if stdout:
            print(stdout)
        print()
        
        # Step 10: Check last order timestamp
        print("Step 10: Checking last order timestamp...")
        stdout, stderr, exit_code = client._execute_with_cd(
            "cd ~/stock-bot && tail -1 data/live_orders.jsonl 2>/dev/null | python3 -c \""
            "import sys, json\n"
            "try:\n"
            "    line = sys.stdin.read()\n"
            "    if line.strip():\n"
            "        data = json.loads(line)\n"
            "        ts = data.get('_ts') or data.get('timestamp')\n"
            "        if ts:\n"
            "            from datetime import datetime\n"
            "            dt = datetime.fromtimestamp(ts)\n"
            "            print(f'Last order: {dt.strftime(\"%Y-%m-%d %H:%M:%S\")}')\n"
            "        else:\n"
            "            print('Last order: timestamp not found')\n"
            "    else:\n"
            "        print('No orders in log file')\n"
            "except Exception as e:\n"
            "    print(f'Error: {e}')\n"
            "\"",
            timeout=15
        )
        if stdout:
            print(stdout)
        print()
        
        print("=" * 80)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. If bot not running: Check systemd logs for errors")
        print("2. If daemon not running: Restart supervisor")
        print("3. If cache empty: Check daemon logs for API errors")
        print("4. If signals not being logged: Check if log_signal_to_history is being called")
        print("5. If all running but no trades: Check blocking gates in logs")
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    success = run_diagnostic()
    sys.exit(0 if success else 1)
