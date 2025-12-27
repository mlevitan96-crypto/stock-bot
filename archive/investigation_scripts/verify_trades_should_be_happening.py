#!/usr/bin/env python3
"""
Comprehensive Verification: Trades Should Be Happening
Checks all systems to confirm trades can execute and identifies any blockers.
"""

from droplet_client import DropletClient
import json
import time
from datetime import datetime, timezone

def main():
    print("=" * 80)
    print("COMPREHENSIVE TRADE READINESS VERIFICATION")
    print("=" * 80)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    client = DropletClient()
    
    try:
        # 1. Check UW Cache Status
        print("1. CHECKING UW CACHE STATUS")
        print("-" * 80)
        result = client.execute_command("cd ~/stock-bot && ls -lh data/uw_flow_cache.json 2>&1", timeout=10)
        if "No such file" not in result['stdout']:
            print("[OK] Cache file exists")
            # Check cache content
            result2 = client.execute_command(
                "cd ~/stock-bot && python3 << 'PYEOF'\n"
                "import json, time\n"
                "with open('data/uw_flow_cache.json') as f:\n"
                "    cache = json.load(f)\n"
                "symbols = [k for k in cache.keys() if not k.startswith('_')]\n"
                "print(f'  Symbols in cache: {len(symbols)}')\n"
                "if symbols:\n"
                "    print(f'  Sample: {symbols[:10]}')\n"
                "    # Check if cache has data\n"
                "    sample_symbol = symbols[0] if symbols else None\n"
                "    if sample_symbol:\n"
                "        data = cache.get(sample_symbol, {})\n"
                "        has_flow = bool(data.get('flow_trades') or data.get('sentiment'))\n"
                "        print(f'  Sample symbol has data: {has_flow}')\n"
                "PYEOF",
                timeout=30
            )
            print(result2['stdout'])
        else:
            print("[FAIL] Cache file does not exist")
        print()
        
        # 2. Check Recent Signals
        print("2. CHECKING RECENT SIGNAL GENERATION")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -50 logs/signals.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "signals = []\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            sig = json.loads(line)\n"
            "            cluster = sig.get('cluster', {})\n"
            "            ticker = cluster.get('ticker', 'unknown')\n"
            "            score = cluster.get('composite_score', 0)\n"
            "            ts = sig.get('ts', 'unknown')\n"
            "            signals.append({'ticker': ticker, 'score': score, 'ts': ts})\n"
            "        except:\n"
            "            pass\n"
            "print(f'Recent signals (last 50): {len(signals)}')\n"
            "if signals:\n"
            "    recent = signals[-10:]\n"
            "    print(f'Last 10 signals:')\n"
            "    for s in recent:\n"
            "        print(f'  {s[\"ticker\"]}: score={s[\"score\"]:.2f} at {s[\"ts\"]}')\n"
            "    # Check if any have good scores\n"
            "    good_signals = [s for s in signals if s['score'] > 2.5]\n"
            "    print(f'Signals with score > 2.5: {len(good_signals)}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 3. Check Current Positions
        print("3. CHECKING CURRENT POSITIONS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import os\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()\n"
            "import alpaca_trade_api as tradeapi\n"
            "api = tradeapi.REST(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_API_SECRET'), os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'), api_version='v2')\n"
            "positions = api.list_positions()\n"
            "print(f'Alpaca positions: {len(positions)}')\n"
            "print(f'Max allowed: 16')\n"
            "print(f'Can open new: {len(positions) < 16}')\n"
            "for p in positions[:5]:\n"
            "    print(f'  {p.symbol}: {p.qty} shares')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 4. Check Blocked Trades
        print("4. CHECKING RECENT BLOCKED TRADES")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -100 state/blocked_trades.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "blocks = []\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            blocks.append(json.loads(line))\n"
            "        except:\n"
            "            pass\n"
            "print(f'Blocked trades (last 100): {len(blocks)}')\n"
            "if blocks:\n"
            "    reasons = {}\n"
            "    for b in blocks:\n"
            "        reason = b.get('reason', 'unknown')\n"
            "        reasons[reason] = reasons.get(reason, 0) + 1\n"
            "    print('Block reasons:')\n"
            "    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):\n"
            "        print(f'  {reason}: {count}')\n"
            "    # Check recent blocks\n"
            "    recent = blocks[-10:]\n"
            "    print(f'\\nLast 10 blocked trades:')\n"
            "    for b in recent:\n"
            "        symbol = b.get('symbol', 'unknown')\n"
            "        score = b.get('score', 0)\n"
            "        reason = b.get('reason', 'unknown')\n"
            "        print(f'  {symbol}: score={score:.2f}, reason={reason}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 5. Check Market Status
        print("5. CHECKING MARKET STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "from datetime import datetime\n"
            "import pytz\n"
            "now = datetime.now(pytz.timezone('America/New_York'))\n"
            "print(f'Current NY time: {now.strftime(\"%Y-%m-%d %H:%M:%S %Z\")}')\n"
            "print(f'Is market hours (9:30-16:00): {9.5 <= now.hour + now.minute/60 < 16}')\n"
            "print(f'Is weekday: {now.weekday() < 5}')\n"
            "market_open = (9.5 <= now.hour + now.minute/60 < 16) and (now.weekday() < 5)\n"
            "print(f'Market open: {market_open}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 6. Check Main Bot Status
        print("6. CHECKING MAIN BOT STATUS")
        print("-" * 80)
        result = client.execute_command("ps aux | grep 'main.py' | grep -v grep", timeout=10)
        if result['stdout'].strip():
            print("[OK] main.py is running")
            print(f"  {result['stdout'].strip()[:100]}")
        else:
            print("[FAIL] main.py not running")
        print()
        
        # 7. Check Recent Bot Activity
        print("7. CHECKING RECENT BOT ACTIVITY")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && tail -30 logs/run.jsonl 2>&1 | python3 << 'PYEOF'\n"
            "import sys, json\n"
            "events = []\n"
            "for line in sys.stdin:\n"
            "    if line.strip():\n"
            "        try:\n"
            "            events.append(json.loads(line))\n"
            "        except:\n"
            "            pass\n"
            "print(f'Recent events (last 30): {len(events)}')\n"
            "if events:\n"
            "    recent = events[-10:]\n"
            "    for e in recent:\n"
            "        event = e.get('event', 'unknown')\n"
            "        symbol = e.get('symbol', '')\n"
            "        print(f'  {event} {symbol}')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 8. Check Gate Status
        print("8. CHECKING GATE STATUS")
        print("-" * 80)
        result = client.execute_command(
            "cd ~/stock-bot && python3 << 'PYEOF'\n"
            "import json\n"
            "from pathlib import Path\n"
            "# Check if freeze is active\n"
            "freeze_file = Path('state/freeze.json')\n"
            "if freeze_file.exists():\n"
            "    freeze_data = json.load(open(freeze_file))\n"
            "    print(f'Freeze active: {freeze_data.get(\"frozen\", False)}')\n"
            "    if freeze_data.get('frozen'):\n"
            "        print(f'  Reason: {freeze_data.get(\"reason\", \"unknown\")}')\n"
            "else:\n"
            "    print('Freeze: Not active')\n"
            "# Check bootstrap status\n"
            "bootstrap_file = Path('state/bootstrap_status.json')\n"
            "if bootstrap_file.exists():\n"
            "    bootstrap = json.load(open(bootstrap_file))\n"
            "    trades = bootstrap.get('trades_completed', 0)\n"
            "    print(f'Bootstrap trades: {trades}/30')\n"
            "else:\n"
            "    print('Bootstrap: Not in bootstrap mode')\n"
            "PYEOF",
            timeout=30
        )
        print(result['stdout'])
        print()
        
        # 9. Summary and Recommendations
        print("=" * 80)
        print("TRADE READINESS SUMMARY")
        print("=" * 80)
        
        # Collect all statuses
        cache_ok = "No such file" not in client.execute_command("cd ~/stock-bot && ls data/uw_flow_cache.json 2>&1", timeout=10)['stdout']
        main_running = bool(client.execute_command("ps aux | grep 'main.py' | grep -v grep", timeout=10)['stdout'].strip())
        
        print(f"UW Cache: {'[OK]' if cache_ok else '[FAIL]'}")
        print(f"Main Bot: {'[OK]' if main_running else '[FAIL]'}")
        print()
        print("RECOMMENDATIONS:")
        print("- Check recent signals to see if any meet entry criteria")
        print("- Review blocked trades to identify most common blockers")
        print("- Verify market is open and bot is processing signals")
        print("- Check if bootstrap mode is preventing trades")
        print()
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

