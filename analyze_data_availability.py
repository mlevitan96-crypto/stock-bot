#!/usr/bin/env python3
"""
Analyze Data Availability - See what historical data we have

Shows:
- Total trades by time period
- Data coverage (daily/weekly/monthly)
- Oldest and newest trades
- Recommendations for analysis time windows
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

LOGS_DIR = Path("logs")
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"

def analyze_data_availability():
    """Analyze what historical data is available"""
    if not ATTRIBUTION_LOG.exists():
        print("attribution.jsonl not found")
        return
    
    trades = []
    dates = []
    
    with ATTRIBUTION_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                trade = json.loads(line)
                if trade.get("type") != "attribution":
                    continue
                
                trade_id = trade.get("trade_id", "")
                if not trade_id or trade_id.startswith("open_"):
                    continue
                
                # Extract date from various sources
                trade_date = None
                context = trade.get("context", {})
                entry_ts_str = context.get("entry_ts") or trade.get("entry_ts") or trade.get("ts", "")
                
                if entry_ts_str:
                    try:
                        if isinstance(entry_ts_str, str):
                            trade_dt = datetime.fromisoformat(entry_ts_str.replace("Z", "+00:00"))
                        else:
                            trade_dt = datetime.fromtimestamp(entry_ts_str, tz=timezone.utc)
                        trade_date = trade_dt.date()
                    except:
                        pass
                
                # Try trade_id
                if trade_date is None and trade_id.startswith("close_"):
                    try:
                        parts = trade_id.split("_")
                        if len(parts) >= 3:
                            date_str = "_".join(parts[2:])
                            trade_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            trade_date = trade_dt.date()
                    except:
                        pass
                
                if trade_date:
                    dates.append(trade_date)
                    trades.append({
                        "date": trade_date,
                        "symbol": trade.get("symbol", ""),
                        "pnl_usd": trade.get("pnl_usd", 0.0),
                        "pnl_pct": trade.get("pnl_pct", 0.0)
                    })
            except:
                continue
    
    if not trades:
        print("No trades found with dates")
        return
    
    dates.sort()
    oldest = dates[0]
    newest = dates[-1]
    days_span = (newest - oldest).days + 1
    
    print("="*80)
    print("DATA AVAILABILITY ANALYSIS")
    print("="*80)
    print(f"\nTotal Trades: {len(trades)}")
    print(f"Date Range: {oldest} to {newest} ({days_span} days)")
    
    # Trades by time period
    print(f"\n" + "="*80)
    print("TRADES BY TIME PERIOD")
    print("="*80)
    
    now = datetime.now(timezone.utc).date()
    
    periods = {
        "Last 7 days": (now - timedelta(days=7), now),
        "Last 14 days": (now - timedelta(days=14), now),
        "Last 30 days": (now - timedelta(days=30), now),
        "Last 60 days": (now - timedelta(days=60), now),
        "Last 90 days": (now - timedelta(days=90), now),
        "All historical": (oldest, newest)
    }
    
    for period_name, (start, end) in periods.items():
        count = sum(1 for t in trades if start <= t["date"] <= end)
        if count > 0:
            wins = sum(1 for t in trades if start <= t["date"] <= end and t["pnl_usd"] > 0)
            pnl = sum(t["pnl_usd"] for t in trades if start <= t["date"] <= end)
            win_rate = (wins / count * 100) if count > 0 else 0
            print(f"  {period_name}: {count} trades, {wins} wins ({win_rate:.1f}%), P&L: ${pnl:.2f}")
    
    # Daily breakdown (last 30 days)
    print(f"\n" + "="*80)
    print("DAILY BREAKDOWN (Last 30 Days)")
    print("="*80)
    
    daily_counts = defaultdict(int)
    daily_pnl = defaultdict(float)
    for t in trades:
        if (now - t["date"]).days <= 30:
            daily_counts[t["date"]] += 1
            daily_pnl[t["date"]] += t["pnl_usd"]
    
    if daily_counts:
        sorted_days = sorted(daily_counts.keys(), reverse=True)[:30]
        for day in sorted_days:
            count = daily_counts[day]
            pnl = daily_pnl[day]
            wins = sum(1 for t in trades if t["date"] == day and t["pnl_usd"] > 0)
            print(f"  {day}: {count} trades, {wins} wins, P&L: ${pnl:.2f}")
    
    # Recommendations
    print(f"\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    # Find period with most data
    best_period = None
    best_count = 0
    for period_name, (start, end) in periods.items():
        count = sum(1 for t in trades if start <= t["date"] <= end)
        if count > best_count and period_name != "All historical":
            best_count = count
            best_period = period_name
    
    if best_period:
        print(f"\n1. For statistical significance, analyze: {best_period}")
        print(f"   ({best_count} trades)")
    
    print(f"\n2. For maximum data, analyze: All historical")
    print(f"   ({len(trades)} trades across {days_span} days)")
    
    # Check if we have enough data for meaningful analysis
    if len(trades) < 50:
        print(f"\n3. ⚠️  WARNING: Only {len(trades)} trades available")
        print(f"   Need at least 50-100 trades for reliable pattern recognition")
        print(f"   Consider analyzing all historical data")
    elif len(trades) < 200:
        print(f"\n3. ⚠️  CAUTION: {len(trades)} trades available")
        print(f"   Good for initial analysis, but more data (200+) would improve reliability")
    else:
        print(f"\n3. ✅ Good data volume: {len(trades)} trades")
        print(f"   Sufficient for reliable pattern recognition")

if __name__ == "__main__":
    analyze_data_availability()
