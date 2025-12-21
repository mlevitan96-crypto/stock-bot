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

def get_price_at_time(symbol: str, target_time: datetime) -> Optional[float]:
    """
    Get price for symbol at a specific time.
    
    This is a placeholder - in production, you'd query:
    - Alpaca historical data
    - Market data API
    - Cached price data
    """
    # TODO: Implement actual price lookup
    # For now, return None to indicate we can't compute counterfactual
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
    
    # For now, we can't compute without price data
    # This is a placeholder for future implementation
    return None

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
