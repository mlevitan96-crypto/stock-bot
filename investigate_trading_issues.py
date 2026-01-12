#!/usr/bin/env python3
"""
Comprehensive Trading Investigation - Check droplet for GOOG concentration and losses
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from droplet_client import DropletClient
except ImportError as e:
    print(f"ERROR: Could not import droplet_client: {e}")
    sys.exit(1)

def main():
    print("=" * 80)
    print("COMPREHENSIVE TRADING INVESTIGATION")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    client = DropletClient()
    investigation = {
        "timestamp": datetime.now().isoformat(),
        "positions": {},
        "recent_trades": [],
        "signals_today": [],
        "logs_analysis": {},
        "goog_analysis": {},
        "issues_found": []
    }
    
    try:
        # Step 1: Check current positions
        print("Step 1: Checking current positions...")
        print("-" * 80)
        result = client.execute_command(
            """cd ~/stock-bot && python3 -c "
import os
from dotenv import load_dotenv
import alpaca_trade_api as api
load_dotenv()
a = api.REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), os.getenv('ALPACA_BASE_URL'))
positions = a.list_positions()
print(json.dumps([{
    'symbol': p.symbol,
    'qty': float(p.qty),
    'side': 'long' if float(p.qty) > 0 else 'short',
    'market_value': float(p.market_value),
    'unrealized_pl': float(p.unrealized_pl),
    'unrealized_plpc': float(p.unrealized_plpc),
    'avg_entry_price': float(p.avg_entry_price),
    'current_price': float(p.current_price)
} for p in positions], indent=2))
" """,
            timeout=30
        )
        
        if result.get('success') and result.get('stdout'):
            try:
                positions = json.loads(result.get('stdout', '[]'))
                investigation['positions'] = positions
                print(f"Found {len(positions)} positions:")
                goog_count = 0
                total_pl = 0.0
                for p in positions:
                    symbol = p.get('symbol', '')
                    pl = p.get('unrealized_pl', 0.0)
                    total_pl += pl
                    if 'GOOG' in symbol:
                        goog_count += 1
                    print(f"  {symbol}: {p.get('qty', 0):.2f} @ ${p.get('avg_entry_price', 0):.2f} | P/L: ${pl:.2f} ({p.get('unrealized_plpc', 0)*100:.2f}%)")
                print(f"\nTotal P/L: ${total_pl:.2f}")
                print(f"GOOG positions: {goog_count}/{len(positions)}")
                investigation['goog_analysis']['position_count'] = goog_count
                investigation['goog_analysis']['total_positions'] = len(positions)
                investigation['goog_analysis']['goog_pct'] = (goog_count / len(positions) * 100) if positions else 0
            except json.JSONDecodeError:
                print(f"Error parsing positions: {result.get('stdout', '')[:200]}")
        else:
            print(f"Error getting positions: {result.get('stderr', 'Unknown error')}")
        print()
        
        # Step 2: Check recent trades today
        print("Step 2: Checking recent trades today...")
        print("-" * 80)
        today = datetime.now().strftime('%Y-%m-%d')
        result = client.execute_command(
            f"""cd ~/stock-bot && python3 -c "
import os
from dotenv import load_dotenv
import alpaca_trade_api as api
from datetime import datetime, timedelta
load_dotenv()
a = api.REST(os.getenv('ALPACA_KEY'), os.getenv('ALPACA_SECRET'), os.getenv('ALPACA_BASE_URL'))
today = datetime.now().date()
orders = a.list_orders(status='all', after={today.isoformat()}, limit=100)
trades = []
for o in orders:
    if o.filled_at:
        filled_date = datetime.fromisoformat(o.filled_at.replace('Z', '+00:00')).date()
        if filled_date == today:
            trades.append({{
                'symbol': o.symbol,
                'side': o.side,
                'qty': float(o.filled_qty),
                'filled_price': float(o.filled_avg_price) if o.filled_avg_price else 0,
                'filled_at': o.filled_at,
                'order_type': o.order_type,
                'status': o.status
            }})
print(json.dumps(trades, indent=2))
" """,
            timeout=30
        )
        
        if result.get('success') and result.get('stdout'):
            try:
                trades = json.loads(result.get('stdout', '[]'))
                investigation['recent_trades'] = trades
                print(f"Found {len(trades)} trades today:")
                goog_trades = 0
                for t in trades:
                    symbol = t.get('symbol', '')
                    if 'GOOG' in symbol:
                        goog_trades += 1
                    print(f"  {symbol}: {t.get('side', '')} {t.get('qty', 0):.2f} @ ${t.get('filled_price', 0):.2f} ({t.get('filled_at', '')})")
                print(f"\nGOOG trades: {goog_trades}/{len(trades)}")
                investigation['goog_analysis']['trade_count'] = goog_trades
            except json.JSONDecodeError:
                print(f"Error parsing trades: {result.get('stdout', '')[:200]}")
        else:
            print(f"Error getting trades: {result.get('stderr', 'Unknown error')}")
        print()
        
        # Step 3: Check recent signals and logs
        print("Step 3: Checking recent signals and logs...")
        print("-" * 80)
        result = client.execute_command(
            """cd ~/stock-bot && tail -1000 logs/trading.log | grep -E 'composite_score|signal|GOOG|decide_and_execute' | tail -50""",
            timeout=30
        )
        if result.get('stdout'):
            print(result.get('stdout'))
            investigation['logs_analysis']['recent_signals'] = result.get('stdout')
        print()
        
        # Step 4: Check UW cache for GOOG signals
        print("Step 4: Checking UW cache for GOOG signals...")
        print("-" * 80)
        result = client.execute_command(
            """cd ~/stock-bot && python3 -c "
import json
from pathlib import Path
try:
    cache = json.load(open('data/uw_flow_cache.json'))
    goog_signals = {}
    for sym in ['GOOG', 'GOOGL']:
        if sym in cache:
            d = cache[sym]
            goog_signals[sym] = {
                'sentiment': d.get('sentiment', 'MISS'),
                'conviction': d.get('conviction', 0),
                'freshness': d.get('freshness', 0),
                'flow_conv': d.get('flow_conv', 0),
                'flow_magnitude': d.get('flow_magnitude', 0),
                'has_darkpool': bool(d.get('dark_pool')),
                'has_insider': bool(d.get('insider')),
                'timestamp': d.get('timestamp', 'MISS')
            }
    print(json.dumps(goog_signals, indent=2))
except Exception as e:
    print(json.dumps({'error': str(e)}))
" """,
            timeout=30
        )
        if result.get('stdout'):
            try:
                goog_data = json.loads(result.get('stdout', '{}'))
                investigation['goog_analysis']['uw_cache'] = goog_data
                print(json.dumps(goog_data, indent=2))
            except:
                print(result.get('stdout'))
        print()
        
        # Step 5: Check blocked trades
        print("Step 5: Checking blocked trades...")
        print("-" * 80)
        result = client.execute_command(
            """cd ~/stock-bot && tail -500 logs/trading.log | grep -E 'blocked|gate|concentration|theme' | tail -30""",
            timeout=30
        )
        if result.get('stdout'):
            print(result.get('stdout'))
            investigation['logs_analysis']['blocked_trades'] = result.get('stdout')
        print()
        
        # Step 6: Check order.jsonl for today
        print("Step 6: Checking order.jsonl for today...")
        print("-" * 80)
        result = client.execute_command(
            f"""cd ~/stock-bot && tail -100 data/order.jsonl | python3 -c "
import json
import sys
from datetime import datetime
today = datetime.now().date().isoformat()
orders = []
for line in sys.stdin:
    if line.strip():
        try:
            o = json.loads(line)
            if today in o.get('ts', ''):
                orders.append(o)
        except:
            pass
print(json.dumps(orders, indent=2))
" """,
            timeout=30
        )
        if result.get('stdout'):
            try:
                orders = json.loads(result.get('stdout', '[]'))
                investigation['recent_trades'].extend(orders)
                goog_orders = sum(1 for o in orders if 'GOOG' in o.get('symbol', ''))
                print(f"Found {len(orders)} orders today, {goog_orders} for GOOG")
            except:
                print(result.get('stdout'))
        print()
        
        # Step 7: Analyze issues
        print("Step 7: Analyzing issues...")
        print("-" * 80)
        
        # Check for GOOG concentration
        if investigation['goog_analysis'].get('goog_pct', 0) > 50:
            issue = f"GOOG concentration too high: {investigation['goog_analysis'].get('goog_pct', 0):.1f}% of positions"
            investigation['issues_found'].append(issue)
            print(f"⚠️  {issue}")
        
        # Check for losses
        total_pl = sum(p.get('unrealized_pl', 0) for p in investigation.get('positions', []))
        if total_pl < 0:
            issue = f"Total unrealized P/L is negative: ${total_pl:.2f}"
            investigation['issues_found'].append(issue)
            print(f"⚠️  {issue}")
        
        # Check for GOOG losses
        goog_pl = sum(p.get('unrealized_pl', 0) for p in investigation.get('positions', []) if 'GOOG' in p.get('symbol', ''))
        if goog_pl < 0:
            issue = f"GOOG positions showing losses: ${goog_pl:.2f}"
            investigation['issues_found'].append(issue)
            print(f"⚠️  {issue}")
        
        print()
        
        # Save investigation report
        report_file = f"reports/trading_investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('reports', exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(investigation, f, indent=2)
        
        print("=" * 80)
        print("INVESTIGATION COMPLETE")
        print(f"Report saved to: {report_file}")
        print("=" * 80)
        
        return investigation
        
    except Exception as e:
        print(f"\n[ERROR] Investigation failed: {e}")
        import traceback
        traceback.print_exc()
        investigation['error'] = str(e)
        return investigation
    finally:
        client.close()

if __name__ == "__main__":
    result = main()
    sys.exit(0 if not result.get('issues_found') else 1)
