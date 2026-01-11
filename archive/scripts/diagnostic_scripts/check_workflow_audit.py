#!/usr/bin/env python3
"""Full workflow audit - check signals, orders, and trade execution"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

def check_recent_signals(hours: int = 2) -> Dict[str, Any]:
    """Check recent signal generation"""
    signal_log = Path("logs/signals.jsonl")
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    signals = []
    if signal_log.exists():
        with open(signal_log, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    ts_str = data.get('ts', '')
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_time:
                                cluster = data.get('cluster', {})
                                signals.append({
                                    'timestamp': ts_str,
                                    'symbol': cluster.get('ticker', 'N/A'),
                                    'score': cluster.get('composite_score', 0.0),
                                    'source': cluster.get('source', 'unknown'),
                                    'direction': cluster.get('direction', 'unknown')
                                })
                        except:
                            pass
                except:
                    pass
    
    return {
        'total_recent': len(signals),
        'signals': signals[-10:],  # Last 10
        'has_recent': len(signals) > 0
    }

def check_recent_orders(hours: int = 2) -> Dict[str, Any]:
    """Check recent order submissions"""
    # CORRECT PATH: Use logs/orders.jsonl (plural) per config/registry.py LogFiles.ORDERS
    # For total orders/trades, count from logs/attribution.jsonl as authoritative source
    order_log = Path("logs/orders.jsonl")
    attribution_log = Path("logs/attribution.jsonl")
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Count total trades from attribution.jsonl (authoritative source)
    total_trades_all_time = 0
    if attribution_log.exists():
        with open(attribution_log, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'attribution':
                            total_trades_all_time += 1
                    except:
                        pass
    
    # Check recent order events from orders.jsonl
    orders = []
    if order_log.exists():
        with open(order_log, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    ts_str = data.get('ts', '')
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_time:
                                orders.append({
                                    'timestamp': ts_str,
                                    'symbol': data.get('symbol', 'N/A'),
                                    'action': data.get('action', 'N/A'),
                                    'status': data.get('entry_status', data.get('status', 'N/A')),
                                    'qty': data.get('qty', 0),
                                    'side': data.get('side', 'N/A')
                                })
                        except:
                            pass
                except:
                    pass
    
    filled = [o for o in orders if o['status'] in ('FILLED', 'filled')]
    
    return {
        'total_trades_all_time': total_trades_all_time,  # From attribution.jsonl (authoritative)
        'total_recent': len(orders),
        'filled_count': len(filled),
        'orders': orders[-10:],
        'filled_orders': filled
    }

def check_alpaca_positions() -> Dict[str, Any]:
    """Check current Alpaca positions"""
    try:
        from alpaca_trade_api import REST
        from dotenv import load_dotenv
        load_dotenv()
        
        api = REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), 
                  os.getenv('ALPACA_BASE_URL'), api_version='v2')
        positions = api.list_positions()
        
        pos_list = []
        for p in positions:
            pos_list.append({
                'symbol': p.symbol,
                'qty': int(p.qty),
                'avg_entry_price': float(p.avg_entry_price),
                'current_price': float(p.current_price),
                'market_value': float(p.market_value),
                'unrealized_pl': float(p.unrealized_pl),
                'side': 'long' if int(p.qty) > 0 else 'short'
            })
        
        return {
            'count': len(positions),
            'positions': pos_list,
            'total_market_value': sum(p['market_value'] for p in pos_list)
        }
    except Exception as e:
        return {'error': str(e), 'count': 0}

def check_recent_blocks(hours: int = 2) -> Dict[str, Any]:
    """Check recent blocked trades"""
    trading_log = Path("logs/trading.jsonl")
    blocked_log = Path("state/blocked_trades.jsonl")
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    blocks = []
    
    # Check trading.jsonl
    if trading_log.exists():
        with open(trading_log, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if 'BLOCKED' in data.get('msg', '') or 'blocked' in str(data).lower():
                        ts_str = data.get('ts', '')
                        if ts_str:
                            try:
                                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                                if ts >= cutoff_time:
                                    blocks.append({
                                        'timestamp': ts_str,
                                        'symbol': data.get('symbol', 'N/A'),
                                        'reason': data.get('reason', data.get('msg', 'N/A'))
                                    })
                            except:
                                pass
                except:
                    pass
    
    # Check blocked_trades.jsonl
    if blocked_log.exists():
        with open(blocked_log, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    ts_str = data.get('timestamp', '')
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_time:
                                blocks.append({
                                    'timestamp': ts_str,
                                    'symbol': data.get('symbol', 'N/A'),
                                    'reason': data.get('reason', 'N/A')
                                })
                        except:
                            pass
                except:
                    pass
    
    # Group by reason
    by_reason = {}
    for block in blocks:
        reason = block['reason']
        by_reason[reason] = by_reason.get(reason, 0) + 1
    
    return {
        'total_recent': len(blocks),
        'by_reason': by_reason,
        'recent_blocks': blocks[-10:]
    }

def check_bot_status() -> Dict[str, Any]:
    """Check if bot process is running"""
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'python.*main.py'], 
                              capture_output=True, text=True)
        is_running = result.returncode == 0
        pids = result.stdout.strip().split('\n') if is_running else []
        return {
            'running': is_running,
            'pids': [p for p in pids if p],
            'pid_count': len([p for p in pids if p])
        }
    except:
        return {'running': False, 'error': 'Could not check process'}

def check_run_once_activity(hours: int = 2) -> Dict[str, Any]:
    """Check run_once activity"""
    system_log = Path("logs/system.jsonl")
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    run_once_count = 0
    last_run_once = None
    
    if system_log.exists():
        with open(system_log, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    msg = data.get('msg', '').lower()
                    if 'run_once' in msg:
                        ts_str = data.get('ts', '')
                        if ts_str:
                            try:
                                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                                if ts >= cutoff_time:
                                    run_once_count += 1
                                    last_run_once = data
                            except:
                                pass
                except:
                    pass
    
    return {
        'count_recent': run_once_count,
        'last_run_once': last_run_once.get('ts', '') if last_run_once else None,
        'active': run_once_count > 0
    }

def main():
    print("="*80)
    print("FULL WORKFLOW AUDIT")
    print("="*80)
    print()
    
    # 1. Bot Status
    print("1. BOT STATUS:")
    bot_status = check_bot_status()
    print(f"   Running: {bot_status.get('running', False)}")
    if bot_status.get('pids'):
        print(f"   PIDs: {', '.join(bot_status['pids'])}")
    print()
    
    # 2. Run Once Activity
    print("2. RUN_ONCE ACTIVITY (last 2 hours):")
    run_activity = check_run_once_activity()
    print(f"   Count: {run_activity.get('count_recent', 0)}")
    if run_activity.get('last_run_once'):
        print(f"   Last: {run_activity['last_run_once'][:19]}")
    print(f"   Active: {run_activity.get('active', False)}")
    print()
    
    # 3. Signal Generation
    print("3. SIGNAL GENERATION (last 2 hours):")
    signals = check_recent_signals()
    print(f"   Total signals: {signals.get('total_recent', 0)}")
    if signals.get('signals'):
        print("   Recent signals:")
        for sig in signals['signals'][-5:]:
            print(f"     {sig['timestamp'][:19]} | {sig['symbol']:6} | score={sig['score']:.2f} | source={sig['source']}")
    print(f"   Signals active: {signals.get('has_recent', False)}")
    print()
    
    # 4. Orders
    print("4. ORDER SUBMISSIONS:")
    orders = check_recent_orders()
    print(f"   Total trades (all time): {orders.get('total_trades_all_time', 0)} (from attribution.jsonl)")
    print(f"   Recent order events (last 2 hours): {orders.get('total_recent', 0)} (from orders.jsonl)")
    print(f"   Filled orders (last 2 hours): {orders.get('filled_count', 0)}")
    if orders.get('orders'):
        print("   Recent orders:")
        for order in orders['orders'][-5:]:
            print(f"     {order['timestamp'][:19]} | {order['symbol']:6} | {order['action']:20} | status={order['status']}")
    print()
    
    # 5. Alpaca Positions
    print("5. ALPACA POSITIONS:")
    positions = check_alpaca_positions()
    print(f"   Count: {positions.get('count', 0)}")
    if positions.get('positions'):
        for pos in positions['positions']:
            print(f"     {pos['symbol']}: {pos['qty']} @ ${pos['avg_entry_price']:.2f} (MV: ${pos['market_value']:.2f})")
    if positions.get('error'):
        print(f"   Error: {positions['error']}")
    print()
    
    # 6. Blocked Trades
    print("6. BLOCKED TRADES (last 2 hours):")
    blocks = check_recent_blocks()
    print(f"   Total blocks: {blocks.get('total_recent', 0)}")
    if blocks.get('by_reason'):
        print("   Blocks by reason:")
        for reason, count in sorted(blocks['by_reason'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"     {reason[:60]}: {count}")
    print()
    
    # Summary
    print("="*80)
    print("AUDIT SUMMARY")
    print("="*80)
    
    workflow_ok = (
        bot_status.get('running', False) and
        run_activity.get('active', False) and
        signals.get('has_recent', False) and
        orders.get('total_trades_all_time', 0) > 0  # Check total trades from attribution.jsonl
    )
    
    if workflow_ok:
        print("✅ WORKFLOW OPERATIONAL")
        print(f"   - Bot running: {bot_status.get('running', False)}")
        print(f"   - Run_once active: {run_activity.get('active', False)}")
        print(f"   - Signals generating: {signals.get('has_recent', False)} ({signals.get('total_recent', 0)} signals)")
        print(f"   - Total trades (all time): {orders.get('total_trades_all_time', 0)} (from attribution.jsonl)")
        print(f"   - Recent order events: {orders.get('total_recent', 0)} orders ({orders.get('filled_count', 0)} filled)")
        print(f"   - Positions: {positions.get('count', 0)}")
    else:
        print("⚠️  WORKFLOW ISSUES DETECTED")
        if not bot_status.get('running', False):
            print("   ❌ Bot not running")
        if not run_activity.get('active', False):
            print("   ❌ Run_once not active")
        if not signals.get('has_recent', False):
            print("   ❌ No recent signals")
        if orders.get('total_trades_all_time', 0) == 0:
            print("   ❌ No trades found in attribution.jsonl")
    
    print("="*80)

if __name__ == "__main__":
    main()
