#!/usr/bin/env python3
"""
30-Day Historical Backtest
Simulates trading bot performance over the last 30 days using historical data.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

def load_historical_logs(days: int = 30) -> Dict:
    """Load historical logs from the last N days."""
    log_dir = Path("logs")
    if not log_dir.exists():
        return {"error": "Logs directory not found"}
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    results = {
        "trades": [],
        "exits": [],
        "signals": [],
        "orders": [],
        "blocked_trades": [],
        "date_range": {
            "start": cutoff_date.isoformat(),
            "end": datetime.now(timezone.utc).isoformat()
        }
    }
    
    # Load attribution (trades)
    attribution_file = log_dir / "attribution.jsonl"
    if attribution_file.exists():
        with open(attribution_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    ts_str = rec.get("timestamp") or rec.get("ts", "")
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_date:
                                results["trades"].append(rec)
                        except:
                            pass
                except:
                    continue
    
    # Load exits
    exit_file = log_dir / "exit.jsonl"
    if exit_file.exists():
        with open(exit_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    ts_str = rec.get("timestamp") or rec.get("ts", "")
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_date:
                                results["exits"].append(rec)
                        except:
                            pass
                except:
                    continue
    
    # Load signals
    signal_file = log_dir / "signals.jsonl"
    if signal_file.exists():
        with open(signal_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    ts_str = rec.get("timestamp") or rec.get("ts", "")
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_date:
                                results["signals"].append(rec)
                        except:
                            pass
                except:
                    continue
    
    # Load orders
    order_file = log_dir / "orders.jsonl"
    if order_file.exists():
        with open(order_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    ts_str = rec.get("timestamp") or rec.get("ts", "")
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_date:
                                results["orders"].append(rec)
                        except:
                            pass
                except:
                    continue
    
    # Load blocked trades
    blocked_file = Path("state/blocked_trades.jsonl")
    if not blocked_file.exists():
        blocked_file = Path("data/blocked_trades.jsonl")
    
    if blocked_file.exists():
        with open(blocked_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    ts_str = rec.get("timestamp") or rec.get("ts", "")
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_date:
                                results["blocked_trades"].append(rec)
                        except:
                            pass
                except:
                    continue
    
    return results

def analyze_performance(data: Dict) -> Dict:
    """Analyze trading performance from historical data."""
    trades = data.get("trades", [])
    exits = data.get("exits", [])
    signals = data.get("signals", [])
    orders = data.get("orders", [])
    blocked = data.get("blocked_trades", [])
    
    # Calculate P&L from exits
    total_pnl_usd = 0.0
    total_pnl_pct = 0.0
    winning_trades = 0
    losing_trades = 0
    trade_count = 0
    
    for exit_rec in exits:
        pnl_usd = exit_rec.get("realized_pnl", 0.0) or exit_rec.get("pnl_usd", 0.0)
        pnl_pct = exit_rec.get("realized_pnl_pct", 0.0) or exit_rec.get("pnl_pct", 0.0)
        
        if pnl_usd != 0 or pnl_pct != 0:
            total_pnl_usd += float(pnl_usd)
            total_pnl_pct += float(pnl_pct)
            trade_count += 1
            
            if float(pnl_usd) > 0:
                winning_trades += 1
            elif float(pnl_usd) < 0:
                losing_trades += 1
    
    # Calculate win rate
    win_rate = (winning_trades / trade_count * 100) if trade_count > 0 else 0.0
    
    # Analyze signals
    signal_count = len(signals)
    bullish_signals = sum(1 for s in signals if s.get("direction") == "bullish")
    bearish_signals = sum(1 for s in signals if s.get("direction") == "bearish")
    
    # Analyze orders
    order_count = len(orders)
    filled_orders = sum(1 for o in orders if o.get("status") == "filled")
    filled_rate = (filled_orders / order_count * 100) if order_count > 0 else 0.0
    
    # Analyze blocked trades
    blocked_count = len(blocked)
    block_reasons = defaultdict(int)
    for b in blocked:
        reason = b.get("reason", "unknown")
        block_reasons[reason] += 1
    
    # Calculate average trade metrics
    avg_pnl_usd = total_pnl_usd / trade_count if trade_count > 0 else 0.0
    avg_pnl_pct = total_pnl_pct / trade_count if trade_count > 0 else 0.0
    
    return {
        "period": data.get("date_range", {}),
        "trades": {
            "total": trade_count,
            "winning": winning_trades,
            "losing": losing_trades,
            "win_rate_pct": round(win_rate, 2),
            "total_pnl_usd": round(total_pnl_usd, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "avg_pnl_usd": round(avg_pnl_usd, 2),
            "avg_pnl_pct": round(avg_pnl_pct, 4)
        },
        "signals": {
            "total": signal_count,
            "bullish": bullish_signals,
            "bearish": bearish_signals
        },
        "orders": {
            "total": order_count,
            "filled": filled_orders,
            "fill_rate_pct": round(filled_rate, 2)
        },
        "blocked_trades": {
            "total": blocked_count,
            "reasons": dict(block_reasons)
        }
    }

def main():
    """Run 30-day backtest."""
    print("=" * 80)
    print("30-DAY HISTORICAL BACKTEST")
    print("=" * 80)
    print()
    
    print("Loading historical data (last 30 days)...")
    data = load_historical_logs(30)
    
    if "error" in data:
        print(f"[ERROR] {data['error']}")
        print("\nNo historical data found. The bot needs to run and generate logs first.")
        return 1
    
    print(f"  Trades found: {len(data.get('trades', []))}")
    print(f"  Exits found: {len(data.get('exits', []))}")
    print(f"  Signals found: {len(data.get('signals', []))}")
    print(f"  Orders found: {len(data.get('orders', []))}")
    print(f"  Blocked trades found: {len(data.get('blocked_trades', []))}")
    print()
    
    if len(data.get('exits', [])) == 0:
        print("[WARNING] No exit data found. Cannot calculate performance metrics.")
        print("The bot needs to have closed some trades to generate backtest data.")
        return 1
    
    print("Analyzing performance...")
    performance = analyze_performance(data)
    
    print()
    print("=" * 80)
    print("BACKTEST RESULTS (Last 30 Days)")
    print("=" * 80)
    print()
    
    print("PERIOD:")
    date_range = performance.get("period", {})
    print(f"  Start: {date_range.get('start', 'N/A')}")
    print(f"  End: {date_range.get('end', 'N/A')}")
    print()
    
    print("TRADING PERFORMANCE:")
    trades = performance.get("trades", {})
    print(f"  Total Trades: {trades.get('total', 0)}")
    print(f"  Winning: {trades.get('winning', 0)}")
    print(f"  Losing: {trades.get('losing', 0)}")
    print(f"  Win Rate: {trades.get('win_rate_pct', 0):.2f}%")
    print(f"  Total P&L: ${trades.get('total_pnl_usd', 0):,.2f} ({trades.get('total_pnl_pct', 0):.2f}%)")
    print(f"  Avg P&L per Trade: ${trades.get('avg_pnl_usd', 0):,.2f} ({trades.get('avg_pnl_pct', 0):.4f}%)")
    print()
    
    print("SIGNALS:")
    signals = performance.get("signals", {})
    print(f"  Total Signals: {signals.get('total', 0)}")
    print(f"  Bullish: {signals.get('bullish', 0)}")
    print(f"  Bearish: {signals.get('bearish', 0)}")
    print()
    
    print("ORDERS:")
    orders = performance.get("orders", {})
    print(f"  Total Orders: {orders.get('total', 0)}")
    print(f"  Filled: {orders.get('filled', 0)}")
    print(f"  Fill Rate: {orders.get('fill_rate_pct', 0):.2f}%")
    print()
    
    print("BLOCKED TRADES:")
    blocked = performance.get("blocked_trades", {})
    print(f"  Total Blocked: {blocked.get('total', 0)}")
    if blocked.get('reasons'):
        print("  Block Reasons:")
        for reason, count in sorted(blocked['reasons'].items(), key=lambda x: x[1], reverse=True):
            print(f"    {reason}: {count}")
    print()
    
    # Save results
    results_file = Path("backtest_30day_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            "backtest_date": datetime.now(timezone.utc).isoformat(),
            "period_days": 30,
            "performance": performance,
            "raw_data_summary": {
                "trades_count": len(data.get('trades', [])),
                "exits_count": len(data.get('exits', [])),
                "signals_count": len(data.get('signals', [])),
                "orders_count": len(data.get('orders', [])),
                "blocked_count": len(data.get('blocked_trades', []))
            }
        }, f, indent=2)
    
    print(f"Results saved to: {results_file}")
    print()
    
    # Summary
    if trades.get('total', 0) > 0:
        if trades.get('total_pnl_usd', 0) > 0:
            print("[SUCCESS] Backtest shows profitable trading over 30 days")
        else:
            print("[WARNING] Backtest shows negative P&L over 30 days")
    else:
        print("[INFO] No trades found in the last 30 days")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

