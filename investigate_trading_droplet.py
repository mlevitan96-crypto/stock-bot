#!/usr/bin/env python3
"""
Comprehensive Trading Investigation Script
Run this on the droplet to investigate GOOG concentration and losses
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

# Try to load .env manually if dotenv not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback: read .env file manually
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

import alpaca_trade_api as api

def main():
    print("=" * 80)
    print("COMPREHENSIVE TRADING INVESTIGATION")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    investigation = {
        "timestamp": datetime.now().isoformat(),
        "positions": [],
        "recent_trades": [],
        "goog_analysis": {},
        "issues": []
    }
    
    # Step 1: Current positions
    print("1. CURRENT POSITIONS")
    print("-" * 80)
    try:
        alpaca_api = api.REST(
            os.getenv('ALPACA_KEY'),
            os.getenv('ALPACA_SECRET'),
            os.getenv('ALPACA_BASE_URL')
        )
        positions = alpaca_api.list_positions()
        
        goog_positions = []
        total_pl = 0.0
        goog_pl = 0.0
        
        print(f"Total positions: {len(positions)}")
        print()
        
        for p in positions:
            pos_data = {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "side": "long" if float(p.qty) > 0 else "short",
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": float(p.unrealized_plpc),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price)
            }
            investigation["positions"].append(pos_data)
            total_pl += pos_data["unrealized_pl"]
            
            if "GOOG" in p.symbol:
                goog_positions.append(pos_data)
                goog_pl += pos_data["unrealized_pl"]
            
            pl_pct = pos_data["unrealized_plpc"] * 100
            print(f"  {p.symbol:6s} {pos_data['qty']:8.2f} @ ${pos_data['avg_entry_price']:7.2f} | "
                  f"P/L: ${pos_data['unrealized_pl']:8.2f} ({pl_pct:6.2f}%)")
        
        print()
        print(f"Total P/L: ${total_pl:.2f}")
        print(f"GOOG positions: {len(goog_positions)}/{len(positions)} "
              f"({len(goog_positions)/len(positions)*100:.1f}%)" if positions else "0")
        print(f"GOOG P/L: ${goog_pl:.2f}")
        
        investigation["goog_analysis"]["position_count"] = len(goog_positions)
        investigation["goog_analysis"]["total_positions"] = len(positions)
        investigation["goog_analysis"]["goog_pct"] = (len(goog_positions)/len(positions)*100) if positions else 0
        investigation["goog_analysis"]["goog_pl"] = goog_pl
        investigation["goog_analysis"]["total_pl"] = total_pl
        
        if len(goog_positions) > len(positions) * 0.5:
            investigation["issues"].append(f"GOOG concentration too high: {len(goog_positions)/len(positions)*100:.1f}%")
        if total_pl < 0:
            investigation["issues"].append(f"Total P/L negative: ${total_pl:.2f}")
        if goog_pl < 0:
            investigation["issues"].append(f"GOOG P/L negative: ${goog_pl:.2f}")
            
    except Exception as e:
        print(f"Error getting positions: {e}")
        investigation["issues"].append(f"Failed to get positions: {e}")
    print()
    
    # Step 2: Recent trades today
    print("2. RECENT TRADES TODAY")
    print("-" * 80)
    try:
        today = datetime.now().date()
        orders = alpaca_api.list_orders(status='all', after=today.isoformat(), limit=100)
        
        trades_today = []
        goog_trades = []
        
        for o in orders:
            if o.filled_at:
                filled_date = datetime.fromisoformat(o.filled_at.replace('Z', '+00:00')).date()
                if filled_date == today:
                    trade_data = {
                        "symbol": o.symbol,
                        "side": o.side,
                        "qty": float(o.filled_qty),
                        "filled_price": float(o.filled_avg_price) if o.filled_avg_price else 0,
                        "filled_at": o.filled_at,
                        "order_type": o.order_type,
                        "status": o.status
                    }
                    trades_today.append(trade_data)
                    if "GOOG" in o.symbol:
                        goog_trades.append(trade_data)
        
        investigation["recent_trades"] = trades_today
        investigation["goog_analysis"]["trade_count"] = len(goog_trades)
        
        print(f"Total trades today: {len(trades_today)}")
        print(f"GOOG trades: {len(goog_trades)}")
        print()
        
        if trades_today:
            print("Recent trades:")
            for t in trades_today[-20:]:
                print(f"  {t['symbol']:6s} {t['side']:4s} {t['qty']:8.2f} @ ${t['filled_price']:7.2f} "
                      f"({t['filled_at'][:19]})")
        else:
            print("No trades today")
            
    except Exception as e:
        print(f"Error getting trades: {e}")
    print()
    
    # Step 3: Check UW cache for GOOG
    print("3. GOOG SIGNALS IN UW CACHE")
    print("-" * 80)
    try:
        cache_file = Path("data/uw_flow_cache.json")
        if cache_file.exists():
            cache = json.load(open(cache_file))
            for sym in ["GOOG", "GOOGL"]:
                if sym in cache:
                    d = cache[sym]
                    print(f"{sym}:")
                    print(f"  sentiment: {d.get('sentiment', 'MISS')}")
                    print(f"  conviction: {d.get('conviction', 0):.3f}")
                    print(f"  freshness: {d.get('freshness', 0):.3f}")
                    print(f"  flow_conv: {d.get('flow_conv', 0):.3f}")
                    print(f"  flow_magnitude: {d.get('flow_magnitude', 0):.3f}")
                    print(f"  has_darkpool: {bool(d.get('dark_pool'))}")
                    print(f"  has_insider: {bool(d.get('insider'))}")
                    print(f"  timestamp: {d.get('timestamp', 'MISS')}")
                    print()
                    investigation["goog_analysis"][f"{sym}_cache"] = {
                        "sentiment": d.get('sentiment'),
                        "conviction": d.get('conviction', 0),
                        "freshness": d.get('freshness', 0),
                        "flow_conv": d.get('flow_conv', 0),
                        "flow_magnitude": d.get('flow_magnitude', 0)
                    }
                else:
                    print(f"{sym}: NOT IN CACHE")
        else:
            print("UW cache file not found")
    except Exception as e:
        print(f"Error checking cache: {e}")
    print()
    
    # Step 4: Check recent logs for GOOG activity
    print("4. RECENT GOOG ACTIVITY IN LOGS")
    print("-" * 80)
    try:
        log_file = Path("logs/trading.log")
        if log_file.exists():
            # Read last 1000 lines
            with open(log_file, 'r') as f:
                lines = f.readlines()
                recent_lines = lines[-1000:] if len(lines) > 1000 else lines
            
            goog_mentions = []
            for line in recent_lines:
                if "GOOG" in line.upper():
                    goog_mentions.append(line.strip())
            
            print(f"GOOG mentions in last 1000 log lines: {len(goog_mentions)}")
            if goog_mentions:
                print("\nRecent GOOG activity:")
                for line in goog_mentions[-10:]:
                    print(f"  {line[:150]}")
        else:
            print("Log file not found")
    except Exception as e:
        print(f"Error checking logs: {e}")
    print()
    
    # Step 5: Check order.jsonl
    print("5. ORDERS FROM ORDER.JSONL (today)")
    print("-" * 80)
    try:
        order_file = Path("data/order.jsonl")
        if order_file.exists():
            today_str = datetime.now().date().isoformat()
            orders_today = []
            goog_orders = []
            
            with open(order_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            o = json.loads(line)
                            if today_str in o.get('ts', ''):
                                orders_today.append(o)
                                if "GOOG" in o.get('symbol', ''):
                                    goog_orders.append(o)
                        except:
                            pass
            
            print(f"Orders today: {len(orders_today)}")
            print(f"GOOG orders: {len(goog_orders)}")
            if orders_today:
                print("\nRecent orders:")
                for o in orders_today[-10:]:
                    print(f"  {o.get('symbol', ''):6s} {o.get('side', ''):4s} {o.get('qty', 0):8.2f} "
                          f"@ ${o.get('price', 0):7.2f} ({o.get('ts', '')[:19]})")
        else:
            print("order.jsonl not found")
    except Exception as e:
        print(f"Error checking orders: {e}")
    print()
    
    # Step 6: Summary and issues
    print("6. SUMMARY AND ISSUES")
    print("-" * 80)
    if investigation["issues"]:
        print("⚠️  ISSUES FOUND:")
        for issue in investigation["issues"]:
            print(f"  - {issue}")
    else:
        print("✅ No critical issues detected")
    print()
    
    # Save investigation
    report_file = f"reports/trading_investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("reports", exist_ok=True)
    with open(report_file, 'w') as f:
        json.dump(investigation, f, indent=2)
    
    print("=" * 80)
    print("INVESTIGATION COMPLETE")
    print(f"Report saved to: {report_file}")
    print("=" * 80)
    
    return investigation

if __name__ == "__main__":
    main()
