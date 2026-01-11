#!/usr/bin/env python3
"""Verify signals and orders - run on droplet"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

def main():
    print("="*80)
    print("SIGNAL GENERATION & ORDER EXECUTION STATUS")
    print("="*80)
    print()
    
    # 1. Check recent signals
    print("1. Recent Signals:")
    signal_log = Path("logs/signals.jsonl")
    if signal_log.exists():
        with open(signal_log, 'r') as f:
            lines = f.readlines()
            recent = [json.loads(l) for l in lines[-10:] if l.strip()]
            if recent:
                for sig in recent[-5:]:
                    cluster = sig.get('cluster', {})
                    ts = sig.get('ts', '')[:19] if sig.get('ts') else 'N/A'
                    symbol = cluster.get('ticker', 'N/A')
                    direction = cluster.get('direction', 'N/A')
                    count = cluster.get('count', 0)
                    print(f"   {ts} | {symbol:6} | {direction:8} | count: {count}")
            else:
                print("   No signals found")
    else:
        print("   Signal log not found")
    print()
    
    # 2. Check system log for run_once activity
    print("2. Bot Activity (run_once):")
    system_log = Path("logs/system.jsonl")
    if system_log.exists():
        with open(system_log, 'r') as f:
            lines = f.readlines()
            run_once = [json.loads(l) for l in lines if 'run_once' in l.get('msg', '').lower()]
            if run_once:
                for log in run_once[-5:]:
                    ts = log.get('ts', '')[:19] if log.get('ts') else 'N/A'
                    msg = log.get('msg', '')[:50]
                    print(f"   {ts} | {msg}")
            else:
                print("   No run_once activity")
    print()
    
    # 3. Check recent orders
    print("3. Recent Order Submissions:")
    order_log = Path("logs/order.jsonl")
    if order_log.exists():
        with open(order_log, 'r') as f:
            lines = f.readlines()
            orders = [json.loads(l) for l in lines[-20:] if l.strip()]
            if orders:
                for o in orders[-10:]:
                    ts = o.get('ts', '')[:19] if o.get('ts') else 'N/A'
                    symbol = o.get('symbol', 'N/A')
                    action = o.get('action', 'N/A')[:25]
                    status = o.get('entry_status', o.get('status', 'N/A'))
                    print(f"   {ts} | {symbol:6} | {action:25} | {status}")
            else:
                print("   No orders found")
    else:
        print("   Order log not found")
    print()
    
    # 4. Check API failures AFTER fix deployment (18:40 was before fix)
    print("4. API Failures After Fix (deployed ~18:55):")
    failure_log = Path("logs/critical_api_failure.log")
    if failure_log.exists():
        with open(failure_log, 'r') as f:
            lines = f.readlines()
            if lines:
                # Find failures after 18:55 (fix deployment time)
                fix_time = datetime(2026, 1, 5, 18, 55, 0, tzinfo=timezone.utc)
                recent_failures = []
                for line in lines:
                    if ' | ' in line:
                        parts = line.split(' | ', 2)
                        if len(parts) >= 2:
                            try:
                                ts_str = parts[0]
                                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                                if ts >= fix_time:
                                    recent_failures.append(line.strip())
                            except:
                                pass
                
                if recent_failures:
                    print(f"   WARNING: {len(recent_failures)} failures after fix:")
                    for line in recent_failures[-5:]:
                        parts = line.split(' | ', 2)
                        print(f"   {parts[0][:19]} | {parts[1]}")
                else:
                    print("   OK: No failures after fix deployment")
            else:
                print("   No failures logged")
    else:
        print("   Failure log not found")
    print()
    
    # 5. Check Alpaca positions
    print("5. Current Alpaca Positions:")
    try:
        from alpaca_trade_api import REST
        from dotenv import load_dotenv
        load_dotenv()
        api = REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), 
                  os.getenv('ALPACA_BASE_URL'), api_version='v2')
        positions = api.list_positions()
        print(f"   {len(positions)} positions")
        for p in positions:
            print(f"   {p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # 6. Check service status
    print("6. Service Status:")
    import subprocess
    try:
        result = subprocess.run(['systemctl', 'is-active', 'trading-bot.service'], 
                              capture_output=True, text=True, timeout=5)
        status = result.stdout.strip()
        print(f"   Service: {status}")
    except:
        print("   Could not check service status")
    print()
    
    print("="*80)

if __name__ == "__main__":
    main()
