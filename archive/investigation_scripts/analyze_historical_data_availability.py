#!/usr/bin/env python3
"""
Analyze Historical Data Availability - Why only 124 trades?

This script answers:
1. How many days of trading data do we actually have?
2. Why only 124 closed trades when there are 276 attribution records?
3. Are there older logs we're not using?
4. Can we backfill or use more historical data?
5. What's the date range of our data?
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

LOGS_DIR = Path("logs")
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"
BLOCKED_TRADES_LOG = Path("state/blocked_trades.jsonl")
UW_ATTRIBUTION_LOG = Path("data/uw_attribution.jsonl")

def parse_timestamp(ts_str):
    """Parse various timestamp formats"""
    if not ts_str:
        return None
    try:
        if isinstance(ts_str, (int, float)):
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        if isinstance(ts_str, str):
            if "T" in ts_str or "Z" in ts_str or "+" in ts_str:
                ts_str = ts_str.replace("Z", "+00:00")
                return datetime.fromisoformat(ts_str)
            # Try as Unix timestamp string
            try:
                return datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
            except:
                pass
    except:
        pass
    return None

def extract_timestamp_from_trade_id(trade_id):
    """Extract timestamp from trade_id like 'close_SYMBOL_2025-12-19T17:47:18.334162+00:00'"""
    if not trade_id:
        return None
    try:
        # Format: close_SYMBOL_ISO_TIMESTAMP or open_SYMBOL_ISO_TIMESTAMP
        parts = trade_id.split("_", 2)
        if len(parts) >= 3:
            ts_str = parts[2]
            return parse_timestamp(ts_str)
    except:
        pass
    return None

def analyze_attribution_data():
    """Analyze attribution.jsonl to understand data availability"""
    print("="*80)
    print("HISTORICAL DATA AVAILABILITY ANALYSIS")
    print("="*80)
    
    if not ATTRIBUTION_LOG.exists():
        print("\n❌ Attribution log not found")
        return
    
    all_records = []
    closed_trades = []
    open_trades = []
    
    with ATTRIBUTION_LOG.open("r") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                all_records.append(record)
                
                trade_id = record.get("trade_id", "")
                if not trade_id:
                    continue
                
                # Extract timestamp
                ts = None
                context = record.get("context", {})
                for ts_field in ["entry_ts", "ts", "timestamp"]:
                    ts_val = context.get(ts_field) or record.get(ts_field)
                    if ts_val:
                        ts = parse_timestamp(ts_val)
                        if ts:
                            break
                
                # Try extracting from trade_id
                if not ts:
                    ts = extract_timestamp_from_trade_id(trade_id)
                
                record["parsed_ts"] = ts
                
                if trade_id.startswith("open_"):
                    open_trades.append(record)
                elif trade_id.startswith("close_"):
                    closed_trades.append(record)
                else:
                    # Try to determine from pnl
                    pnl = record.get("pnl_usd", 0.0) or record.get("pnl_pct", 0.0)
                    if pnl != 0.0 or context.get("close_reason"):
                        closed_trades.append(record)
                    else:
                        open_trades.append(record)
            except Exception as e:
                print(f"  ⚠️  Error parsing line {line_num}: {e}")
                continue
    
    print(f"\nTotal Attribution Records: {len(all_records)}")
    print(f"  Closed trades: {len(closed_trades)}")
    print(f"  Open trades: {len(open_trades)}")
    print(f"  Other records: {len(all_records) - len(closed_trades) - len(open_trades)}")
    
    # Date range analysis
    print("\n" + "="*80)
    print("DATE RANGE ANALYSIS")
    print("="*80)
    
    dates_with_ts = [r["parsed_ts"] for r in all_records if r.get("parsed_ts")]
    
    if dates_with_ts:
        dates_with_ts.sort()
        earliest = dates_with_ts[0]
        latest = dates_with_ts[-1]
        date_range = (latest - earliest).days
        
        print(f"\nDate Range:")
        print(f"  Earliest: {earliest.strftime('%Y-%m-%d %H:%M:%S UTC') if earliest else 'Unknown'}")
        print(f"  Latest: {latest.strftime('%Y-%m-%d %H:%M:%S UTC') if latest else 'Unknown'}")
        print(f"  Span: {date_range} days")
        
        # Daily breakdown
        daily_counts = defaultdict(lambda: {"closed": 0, "open": 0, "total": 0})
        for record in all_records:
            ts = record.get("parsed_ts")
            if ts:
                day = ts.date()
                daily_counts[day]["total"] += 1
                trade_id = record.get("trade_id", "")
                if trade_id.startswith("close_") or (record.get("pnl_usd", 0.0) != 0.0):
                    daily_counts[day]["closed"] += 1
                elif trade_id.startswith("open_"):
                    daily_counts[day]["open"] += 1
        
        print(f"\nDaily Breakdown (last 30 days):")
        sorted_days = sorted(daily_counts.keys(), reverse=True)[:30]
        for day in sorted_days:
            counts = daily_counts[day]
            print(f"  {day}: {counts['closed']} closed, {counts['open']} open, {counts['total']} total")
        
        # Trading days calculation
        trading_days = len(daily_counts)
        print(f"\nTrading Days with Data: {trading_days}")
        print(f"Average Closed Trades per Day: {len(closed_trades) / trading_days:.1f}" if trading_days > 0 else "")
    
    # Why only 124 closed trades?
    print("\n" + "="*80)
    print("WHY ONLY 124 CLOSED TRADES?")
    print("="*80)
    
    # Check for records without timestamps
    no_ts = sum(1 for r in all_records if not r.get("parsed_ts"))
    print(f"\nRecords without timestamps: {no_ts}")
    
    # Check for records that might be closed but not marked
    potential_closed = []
    for record in all_records:
        trade_id = record.get("trade_id", "")
        pnl = record.get("pnl_usd", 0.0) or record.get("pnl_pct", 0.0)
        context = record.get("context", {})
        close_reason = context.get("close_reason")
        
        if not trade_id.startswith("open_") and not trade_id.startswith("close_"):
            if pnl != 0.0 or close_reason:
                potential_closed.append(record)
    
    print(f"Records that look closed but aren't marked: {len(potential_closed)}")
    
    # Check for duplicate trade_ids
    trade_ids = [r.get("trade_id") for r in all_records if r.get("trade_id")]
    unique_ids = set(trade_ids)
    duplicates = len(trade_ids) - len(unique_ids)
    print(f"Duplicate trade IDs: {duplicates}")
    
    # Historical data check
    print("\n" + "="*80)
    print("HISTORICAL DATA CHECK")
    print("="*80)
    
    # Check if there are backup logs or older files
    log_dir = ATTRIBUTION_LOG.parent
    backup_files = list(log_dir.glob("attribution*.jsonl*"))
    backup_files.extend(list(log_dir.glob("attribution*.bak")))
    backup_files.extend(list(log_dir.glob("attribution*.old")))
    
    if backup_files:
        print(f"\nFound {len(backup_files)} potential backup/old attribution files:")
        for f in backup_files:
            size = f.stat().st_size
            print(f"  {f.name}: {size:,} bytes")
    else:
        print("\nNo backup attribution files found")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    print("\n1. DATA COLLECTION:")
    if len(closed_trades) < 200:
        print(f"   ⚠️  Only {len(closed_trades)} closed trades - need more data")
        print(f"      - Current: {len(closed_trades)} closed trades")
        print(f"      - Target: 375+ trades for reliable statistics")
        print(f"      - Need: {375 - len(closed_trades)} more closed trades")
        print(f"      - At current rate: {len(closed_trades) / trading_days:.1f} trades/day")
        if trading_days > 0:
            days_needed = (375 - len(closed_trades)) / (len(closed_trades) / trading_days)
            print(f"      - Estimated days needed: {days_needed:.0f} days")
    
    print("\n2. DATA QUALITY:")
    if no_ts > 0:
        print(f"   ⚠️  {no_ts} records missing timestamps")
        print(f"      - Fix: Ensure all attribution records include timestamps")
    
    if len(potential_closed) > 0:
        print(f"   ⚠️  {len(potential_closed)} records look closed but aren't marked")
        print(f"      - These might be usable for analysis")
    
    print("\n3. HISTORICAL DATA:")
    if backup_files:
        print(f"   ✓ Found {len(backup_files)} backup files - could merge for more data")
    else:
        print(f"   ⚠️  No backup files found - all data is in current log")
    
    print("\n4. TRADING ACTIVITY:")
    if trading_days > 0:
        avg_per_day = len(closed_trades) / trading_days
        print(f"   Current rate: {avg_per_day:.1f} closed trades per day")
        if avg_per_day < 5:
            print(f"   ⚠️  Low trading activity - consider:")
            print(f"      - Are entry criteria too strict?")
            print(f"      - Are positions being held too long?")
            print(f"      - Is the bot running consistently?")
    
    print("\n5. IMMEDIATE ACTIONS:")
    print(f"   - Continue trading to accumulate more closed trades")
    print(f"   - Monitor daily close rate (target: 5-10 trades/day)")
    print(f"   - Don't adjust weights until we have 200+ closed trades")
    print(f"   - Use causal analysis to understand WHY patterns exist")

if __name__ == "__main__":
    analyze_attribution_data()
