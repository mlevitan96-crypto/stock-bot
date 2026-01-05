#!/usr/bin/env python3
"""Comprehensive trade workflow analysis - run on droplet"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

def analyze_workflow():
    print("="*80)
    print("COMPREHENSIVE TRADE WORKFLOW ANALYSIS")
    print("="*80)
    print()
    
    # 1. Check signals generated
    print("STEP 1: Signal Generation")
    print("-" * 80)
    signal_log = Path("logs/signals.jsonl")
    if signal_log.exists():
        with open(signal_log, 'r') as f:
            lines = f.readlines()
            if lines:
                recent = [json.loads(l) for l in lines[-10:] if l.strip()]
                print(f"   Signals in log: {len(recent)} recent")
                if recent:
                    latest = recent[-1]
                    cluster = latest.get('cluster', {})
                    ts = latest.get('ts', '')[:19] if latest.get('ts') else 'N/A'
                    symbol = cluster.get('ticker', 'N/A')
                    direction = cluster.get('direction', 'N/A')
                    count = cluster.get('count', 0)
                    print(f"   Latest signal: {ts} | {symbol} | {direction} | count: {count}")
                print("   STATUS: Signals generating")
            else:
                print("   STATUS: No signals found")
    else:
        print("   STATUS: Signal log missing")
    print()
    
    # 2. Check system log for decide_and_execute calls
    print("STEP 2: Decision & Execution (decide_and_execute calls)")
    print("-" * 80)
    system_log = Path("logs/system.jsonl")
    decide_events = []
    if system_log.exists():
        with open(system_log, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg = data.get('msg', '').lower()
                    if 'decide' in msg or 'execute' in msg or 'cluster' in msg:
                        decide_events.append(data)
                except:
                    pass
        if decide_events:
            print(f"   Decision events found: {len(decide_events)}")
            for event in decide_events[-5:]:
                ts = event.get('ts', '')[:19] if event.get('ts') else 'N/A'
                msg = event.get('msg', '')[:60]
                print(f"   {ts} | {msg}")
        else:
            print("   STATUS: No decide/execute events found")
    print()
    
    # 3. Check trading.jsonl for gate blocks
    print("STEP 3: Trading Gates & Blocks")
    print("-" * 80)
    trading_log = Path("logs/trading.jsonl")
    blocked = []
    allowed = []
    if trading_log.exists():
        with open(trading_log, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg = data.get('msg', '').lower()
                    if 'blocked' in msg or 'gate' in msg:
                        blocked.append(data)
                    if 'should_trade' in msg or 'allowed' in msg:
                        allowed.append(data)
                except:
                    pass
        print(f"   Blocked trades: {len(blocked)}")
        if blocked:
            for b in blocked[-5:]:
                ts = b.get('ts', '')[:19] if b.get('ts') else 'N/A'
                symbol = b.get('symbol', 'N/A')
                reason = b.get('reason', b.get('msg', ''))[:50]
                print(f"   {ts} | {symbol} | BLOCKED: {reason}")
        print(f"   Allowed trades: {len(allowed)}")
        if allowed:
            for a in allowed[-5:]:
                ts = a.get('ts', '')[:19] if a.get('ts') else 'N/A'
                symbol = a.get('symbol', 'N/A')
                print(f"   {ts} | {symbol} | ALLOWED")
    else:
        print("   STATUS: Trading log missing")
    print()
    
    # 4. Check order submissions
    print("STEP 4: Order Submissions")
    print("-" * 80)
    order_log = Path("logs/order.jsonl")
    orders = []
    if order_log.exists():
        with open(order_log, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('symbol'):
                        orders.append(data)
                except:
                    pass
        print(f"   Total orders: {len(orders)}")
        if orders:
            recent = orders[-10:]
            print(f"   Recent orders (last 10):")
            for o in recent:
                ts = o.get('ts', '')[:19] if o.get('ts') else 'N/A'
                symbol = o.get('symbol', 'N/A')
                action = o.get('action', o.get('msg', ''))[:30]
                status = o.get('entry_status', o.get('status', 'N/A'))
                print(f"   {ts} | {symbol} | {action} | {status}")
        else:
            print("   STATUS: No orders found")
    else:
        print("   STATUS: Order log missing")
    print()
    
    # 5. Check API failures
    print("STEP 5: API Failures")
    print("-" * 80)
    failure_log = Path("logs/critical_api_failure.log")
    if failure_log.exists():
        with open(failure_log, 'r') as f:
            lines = f.readlines()
            if lines:
                recent_failures = lines[-10:]
                print(f"   Total failures: {len(lines)}")
                print(f"   Recent failures (last 10):")
                for line in recent_failures:
                    if ' | ' in line:
                        parts = line.split(' | ', 2)
                        if len(parts) >= 2:
                            ts = parts[0][:19]
                            event = parts[1]
                            print(f"   {ts} | {event}")
            else:
                print("   STATUS: No failures logged")
    else:
        print("   STATUS: Failure log missing")
    print()
    
    # 6. Check Alpaca positions
    print("STEP 6: Alpaca Positions (Final State)")
    print("-" * 80)
    try:
        from alpaca_trade_api import REST
        from dotenv import load_dotenv
        load_dotenv()
        api = REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), 
                  os.getenv('ALPACA_BASE_URL'), api_version='v2')
        positions = api.list_positions()
        print(f"   Current positions: {len(positions)}")
        if positions:
            for p in positions:
                print(f"   {p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f}")
        else:
            print("   STATUS: No positions in Alpaca")
    except Exception as e:
        print(f"   ERROR: {e}")
    print()
    
    # 7. Check run_once activity
    print("STEP 7: Bot Loop Activity (run_once)")
    print("-" * 80)
    run_once_count = 0
    last_run_once = None
    if system_log.exists():
        with open(system_log, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg = data.get('msg', '').lower()
                    if 'run_once' in msg:
                        run_once_count += 1
                        last_run_once = data
                except:
                    pass
        print(f"   Total run_once calls: {run_once_count}")
        if last_run_once:
            ts = last_run_once.get('ts', '')[:19] if last_run_once.get('ts') else 'N/A'
            print(f"   Last run_once: {ts}")
            # Calculate age
            try:
                if last_run_once.get('ts'):
                    last_ts = datetime.fromisoformat(last_run_once['ts'].replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    age_min = (now - last_ts).total_seconds() / 60
                    print(f"   Age: {age_min:.1f} minutes ago")
            except:
                pass
        else:
            print("   STATUS: No run_once activity found")
    print()
    
    # 8. Check freeze state
    print("STEP 8: Freeze/Block State")
    print("-" * 80)
    freeze_file = Path("state/freeze_active.json")
    if freeze_file.exists():
        try:
            with open(freeze_file, 'r') as f:
                freeze_data = json.load(f)
                print(f"   STATUS: FROZEN")
                print(f"   Freeze data: {json.dumps(freeze_data, indent=2)}")
        except Exception as e:
            print(f"   ERROR reading freeze file: {e}")
    else:
        print("   STATUS: NOT FROZEN")
    print()
    
    # Summary
    print("="*80)
    print("WORKFLOW SUMMARY")
    print("="*80)
    print()
    print("Workflow Steps:")
    print("  1. Signals generated → Check signals.jsonl")
    print("  2. decide_and_execute called → Check system.jsonl")
    print("  3. Gates/checks passed → Check trading.jsonl")
    print("  4. Orders submitted → Check order.jsonl")
    print("  5. API calls succeed → Check critical_api_failure.log")
    print("  6. Positions open → Check Alpaca API")
    print()
    print("Next: Review each step to identify where workflow breaks")

if __name__ == "__main__":
    analyze_workflow()
