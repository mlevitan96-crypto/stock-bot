#!/usr/bin/env python3
"""Comprehensive workflow blocker diagnosis - run on droplet"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

def main():
    print("="*80)
    print("WORKFLOW BLOCKER DIAGNOSIS")
    print("="*80)
    print()
    
    blockers = []
    
    # 1. Freeze state
    print("1. FREEZE STATE:")
    freeze_file = Path("state/freeze_active.json")
    if freeze_file.exists():
        try:
            with open(freeze_file, 'r') as f:
                freeze_data = json.load(f)
                print(f"   BLOCKER FOUND: Freeze active")
                print(f"   Reason: {freeze_data.get('reason', 'unknown')}")
                blockers.append("FREEZE_STATE")
        except:
            print("   Freeze file exists but unreadable")
            blockers.append("FREEZE_STATE")
    else:
        print("   OK: No freeze file")
    print()
    
    # 2. Run once activity
    print("2. BOT LOOP ACTIVITY:")
    system_log = Path("logs/system.jsonl")
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
        print(f"   run_once calls: {run_once_count}")
        if last_run_once:
            ts = last_run_once.get('ts', '')[:19] if last_run_once.get('ts') else 'N/A'
            print(f"   Last run_once: {ts}")
            if run_once_count == 0:
                blockers.append("NO_RUN_ONCE")
        else:
            print("   WARNING: No run_once activity found")
            blockers.append("NO_RUN_ONCE")
    print()
    
    # 3. Trading armed
    print("3. TRADING ARMED:")
    armed_logs = []
    if system_log.exists():
        with open(system_log, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg = data.get('msg', '').lower()
                    if 'not_armed' in msg or 'reduce_only' in msg:
                        armed_logs.append(data)
                except:
                    pass
        if armed_logs:
            print(f"   BLOCKER FOUND: {len(armed_logs)} not_armed/reduce_only events")
            for log in armed_logs[-3:]:
                ts = log.get('ts', '')[:19] if log.get('ts') else 'N/A'
                msg = log.get('msg', '')[:60]
                print(f"   {ts}: {msg}")
            blockers.append("NOT_ARMED")
        else:
            print("   OK: No not_armed/reduce_only logs")
    print()
    
    # 4. Signals
    print("4. SIGNAL GENERATION:")
    signal_log = Path("logs/signals.jsonl")
    signal_count = 0
    if signal_log.exists():
        with open(signal_log, 'r') as f:
            signal_count = len([l for l in f if l.strip()])
        print(f"   Total signals: {signal_count}")
        if signal_count == 0:
            blockers.append("NO_SIGNALS")
        else:
            with open(signal_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_sig = json.loads(lines[-1])
                    cluster = last_sig.get('cluster', {})
                    ts = last_sig.get('ts', '')[:19] if last_sig.get('ts') else 'N/A'
                    symbol = cluster.get('ticker', 'N/A')
                    print(f"   Last signal: {ts} | {symbol}")
    else:
        print("   WARNING: Signal log missing")
        blockers.append("NO_SIGNALS")
    print()
    
    # 5. Clusters/composite
    print("5. CLUSTERS & COMPOSITE:")
    cluster_count = 0
    decide_calls = 0
    if system_log.exists():
        with open(system_log, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg = data.get('msg', '').lower()
                    raw_msg = data.get('msg', '')
                    if 'decide_and_execute' in raw_msg or 'Processing' in raw_msg and 'clusters' in raw_msg:
                        cluster_count += 1
                    if 'decide_and_execute returned' in raw_msg:
                        decide_calls += 1
                        orders = data.get('order_count', 0)
                        if orders == 0:
                            print(f"   decide_and_execute returned 0 orders: {raw_msg}")
                except:
                    pass
        print(f"   Cluster/composite events: {cluster_count}")
        print(f"   decide_and_execute calls: {decide_calls}")
        if decide_calls > 0 and cluster_count == 0:
            blockers.append("NO_CLUSTERS")
    print()
    
    # 6. Gate blocks
    print("6. GATE BLOCKS:")
    trading_log = Path("logs/trading.jsonl")
    blocked_count = 0
    recent_blocks = []
    if trading_log.exists():
        with open(trading_log, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg = data.get('msg', '').lower()
                    if 'blocked' in msg or 'BLOCKED' in str(data):
                        blocked_count += 1
                        recent_blocks.append(data)
                except:
                    pass
        print(f"   Total blocks: {blocked_count}")
        if recent_blocks:
            print(f"   Recent blocks (last 5):")
            for b in recent_blocks[-5:]:
                sym = b.get('symbol', 'N/A')
                reason = b.get('reason', b.get('msg', 'N/A'))[:60]
                ts = b.get('ts', '')[:19] if b.get('ts') else 'N/A'
                print(f"   {ts} | {sym}: {reason}")
    else:
        print("   No trading log found")
    print()
    
    # 7. Orders
    print("7. ORDER SUBMISSIONS:")
    order_log = Path("logs/order.jsonl")
    order_count = 0
    if order_log.exists():
        with open(order_log, 'r') as f:
            order_count = len([l for l in f if l.strip()])
        print(f"   Total orders: {order_count}")
        if order_count > 0:
            with open(order_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_order = json.loads(lines[-1])
                    ts = last_order.get('ts', '')[:19] if last_order.get('ts') else 'N/A'
                    symbol = last_order.get('symbol', 'N/A')
                    action = last_order.get('action', last_order.get('msg', 'N/A'))[:40]
                    print(f"   Last order: {ts} | {symbol} | {action}")
    else:
        print("   No order log found")
    print()
    
    # 8. API failures
    print("8. API FAILURES (after fix):")
    failure_log = Path("logs/critical_api_failure.log")
    failure_count = 0
    if failure_log.exists():
        with open(failure_log, 'r') as f:
            all_lines = f.readlines()
            failure_count = len(all_lines)
            # Check failures after 18:55 (fix deployment)
            fix_time = datetime(2026, 1, 5, 18, 55, 0, tzinfo=timezone.utc)
            recent_failures = []
            for line in all_lines:
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
            print(f"   Total failures: {failure_count}")
            print(f"   Failures after fix: {len(recent_failures)}")
            if recent_failures:
                print("   Recent failures:")
                for line in recent_failures[-3:]:
                    parts = line.split(' | ', 2)
                    print(f"   {parts[0][:19]} | {parts[1]}")
            else:
                print("   OK: No failures after fix")
    else:
        print("   No failure log")
    print()
    
    # 9. Alpaca positions
    print("9. ALPACA POSITIONS:")
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
    
    # Summary
    print("="*80)
    print("BLOCKER SUMMARY")
    print("="*80)
    if blockers:
        print(f"BLOCKERS IDENTIFIED: {', '.join(blockers)}")
        print()
        print("Recommended actions:")
        if "FREEZE_STATE" in blockers:
            print("  - Check state/freeze_active.json and clear if appropriate")
        if "NOT_ARMED" in blockers:
            print("  - Check TRADING_MODE vs ALPACA_BASE_URL configuration")
        if "NO_SIGNALS" in blockers:
            print("  - Check UW cache, signal generation, composite scoring")
        if "NO_CLUSTERS" in blockers:
            print("  - Check composite scoring, gate rejections")
    else:
        print("NO OBVIOUS BLOCKERS FOUND")
        print("Trades may be blocked by:")
        print("  - Gate rejections (check gate logs)")
        print("  - Score thresholds (MIN_EXEC_SCORE = 2.0)")
        print("  - Cooldowns")
        print("  - Concentration limits")
        print("  - Expectancy gate")
    print()
    print("="*80)
    print("DIAGNOSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
