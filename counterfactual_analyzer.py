#!/usr/bin/env python3
"""
Counterfactual Analyzer

Analyzes blocked trades to compute theoretical P&L if we had taken them.
This enables learning from missed opportunities.

Usage:
    python3 counterfactual_analyzer.py
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

STATE_DIR = Path("state")
BLOCKED_TRADES = STATE_DIR / "blocked_trades.jsonl"
ATTRIBUTION_LOG = Path("logs/attribution.jsonl")

def get_price_at_time(symbol: str, target_time: datetime, lookback_hours: int = 24) -> Optional[float]:
    """
    Get price for symbol at a specific time using Alpaca historical data.
    
    Args:
        symbol: Symbol to get price for
        target_time: Target timestamp
        lookback_hours: Hours to look back for price data
    
    Returns:
        Price at target time, or None if unavailable
    """
    try:
        import alpaca_trade_api as tradeapi
        import os
        from datetime import timedelta
        
        # Get Alpaca API
        key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
        secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not key or not secret:
            return None
        
        api = tradeapi.REST(key, secret, base_url)
        
        # Get bars around target time
        start_time = target_time - timedelta(hours=lookback_hours)
        end_time = target_time + timedelta(hours=1)
        
        try:
            bars = api.get_bars(
                symbol,
                "1Min",
                start=start_time.isoformat(),
                end=end_time.isoformat(),
                limit=1000
            ).df
            
            if bars.empty:
                return None
            
            # Find closest bar to target time
            bars.index = bars.index.tz_localize('UTC') if bars.index.tz is None else bars.index
            target_time_tz = target_time if target_time.tzinfo else target_time.replace(tzinfo=timezone.utc)
            
            # Get bar at or before target time
            before_bars = bars[bars.index <= target_time_tz]
            if not before_bars.empty:
                closest_bar = before_bars.iloc[-1]
                return float(closest_bar['close'])
            
            # If no bar before, use first bar after
            after_bars = bars[bars.index > target_time_tz]
            if not after_bars.empty:
                closest_bar = after_bars.iloc[0]
                return float(closest_bar['open'])
            
            return None
        except Exception as e:
            # Fallback: try with simpler query
            try:
                bars = api.get_bars(symbol, "1Min", limit=100).df
                if not bars.empty:
                    # Use most recent price as approximation
                    return float(bars.iloc[-1]['close'])
            except:
                pass
            return None
    except ImportError:
        return None
    except Exception:
        return None

def compute_counterfactual_pnl(blocked_trade: Dict) -> Optional[float]:
    """
    Compute theoretical P&L for a blocked trade.
    
    Args:
        blocked_trade: Blocked trade record with decision_price, direction, timestamp
    
    Returns:
        Theoretical P&L percentage, or None if can't compute
    """
    decision_price = blocked_trade.get("decision_price", 0.0)
    direction = blocked_trade.get("direction", "unknown")
    timestamp_str = blocked_trade.get("timestamp", "")
    
    if not decision_price or decision_price <= 0:
        return None
    
    if not timestamp_str:
        return None
    
    try:
        decision_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if decision_time.tzinfo is None:
            decision_time = decision_time.replace(tzinfo=timezone.utc)
    except:
        return None
    
    # Compute counterfactual P&L using price data
    # Get entry price (decision_price)
    entry_price = decision_price
    
    # Get symbol from blocked trade
    symbol = blocked_trade.get("symbol", "")
    if not symbol:
        return None
    
    # Get exit price (use current price or price 4 hours later as proxy)
    exit_time = decision_time + timedelta(hours=4)  # Assume 4-hour hold period
    exit_price = get_price_at_time(symbol, exit_time)
    
    if not exit_price or exit_price <= 0:
        return None
    
    # Calculate P&L based on direction
    if direction.lower() == "bullish" or direction.lower() == "buy":
        pnl_pct = (exit_price - entry_price) / entry_price
    elif direction.lower() == "bearish" or direction.lower() == "sell":
        pnl_pct = (entry_price - exit_price) / entry_price
    else:
        return None
    
    return pnl_pct

def analyze_blocked_trades():
    """
    Analyze blocked trades for counterfactual learning.
    
    This helps answer:
    - Were we too conservative? (blocked good trades)
    - Were we too aggressive? (blocked bad trades correctly)
    - Which gates are most effective?
    - Which signal combinations should we have taken?
    """
    if not BLOCKED_TRADES.exists():
        print("No blocked trades log found")
        return
    
    blocked_trades = []
    with open(BLOCKED_TRADES, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    rec = json.loads(line)
                    blocked_trades.append(rec)
                except:
                    continue
    
    print("=" * 80)
    print("COUNTERFACTUAL ANALYSIS - BLOCKED TRADES")
    print("=" * 80)
    print()
    print(f"Total blocked trades: {len(blocked_trades)}")
    print()
    
    # Group by blocking reason
    by_reason = defaultdict(list)
    by_score_range = defaultdict(list)
    
    for trade in blocked_trades:
        reason = trade.get("reason", "unknown")
        score = trade.get("score", 0.0)
        by_reason[reason].append(trade)
        
        if score >= 4.0:
            by_score_range["high (4.0+)"].append(trade)
        elif score >= 3.0:
            by_score_range["medium (3.0-4.0)"].append(trade)
        else:
            by_score_range["low (<3.0)"].append(trade)
    
    print("Blocked Trades by Reason:")
    print("-" * 80)
    for reason, trades in sorted(by_reason.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {reason:40s} {len(trades):4d} trades")
    print()
    
    print("Blocked Trades by Score:")
    print("-" * 80)
    for score_range, trades in sorted(by_score_range.items()):
        print(f"  {score_range:20s} {len(trades):4d} trades")
    print()
    
    # Analyze components of blocked trades
    components_in_blocked = defaultdict(int)
    for trade in blocked_trades:
        comps = trade.get("components", {})
        for comp, value in comps.items():
            if value and value != 0:
                components_in_blocked[comp] += 1
    
    if components_in_blocked:
        print("Most Common Components in Blocked Trades:")
        print("-" * 80)
        for comp, count in sorted(components_in_blocked.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {comp:30s} {count:4d} times")
        print()
    
    print("=" * 80)
    print("NOTE: Counterfactual P&L computation requires price data")
    print("      This is a placeholder for future implementation")
    print("=" * 80)

if __name__ == "__main__":
    analyze_blocked_trades()
