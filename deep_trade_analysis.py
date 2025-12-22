#!/usr/bin/env python3
"""
Deep Trade Analysis - Find what's actually working

Analyzes individual trades to find:
1. What conditions lead to wins (even if rare)
2. What conditions lead to losses (to avoid)
3. Feature combinations that work
4. Context patterns that predict success
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

LOGS_DIR = Path("logs")
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"

def analyze_winning_trades():
    """Deep dive into winning trades to find patterns"""
    if not ATTRIBUTION_LOG.exists():
        print("attribution.jsonl not found")
        return
    
    wins = []
    losses = []
    
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
                
                pnl_usd = trade.get("pnl_usd", 0.0)
                pnl_pct = trade.get("pnl_pct", 0.0)
                context = trade.get("context", {})
                components = context.get("components", {})
                
                trade_data = {
                    "trade_id": trade_id,
                    "symbol": trade.get("symbol", ""),
                    "pnl_usd": pnl_usd,
                    "pnl_pct": pnl_pct,
                    "context": context,
                    "components": components,
                    "market_regime": context.get("market_regime", "unknown"),
                    "time_of_day": context.get("time_of_day", "unknown"),
                    "signal_strength": context.get("signal_strength", "unknown"),
                    "flow_magnitude": context.get("flow_magnitude", "unknown"),
                    "entry_score": context.get("entry_score", 0.0),
                }
                
                if pnl_usd > 0 or pnl_pct > 0:
                    wins.append(trade_data)
                else:
                    losses.append(trade_data)
            except Exception as e:
                continue
    
    print("="*80)
    print("DEEP TRADE ANALYSIS")
    print("="*80)
    print(f"\nTotal Trades: {len(wins) + len(losses)}")
    print(f"Wins: {len(wins)} ({len(wins)/(len(wins)+len(losses))*100:.1f}%)")
    print(f"Losses: {len(losses)} ({len(losses)/(len(wins)+len(losses))*100:.1f}%)")
    
    if not wins:
        print("\n⚠️  NO WINNING TRADES FOUND - This explains why no success patterns are identified")
        print("   Need to focus on understanding why trades are losing")
        return
    
    # Analyze winning trade patterns
    print("\n" + "="*80)
    print("WINNING TRADE PATTERNS")
    print("="*80)
    
    # Market regime in wins
    regime_counts = defaultdict(int)
    for w in wins:
        regime_counts[w["market_regime"]] += 1
    print(f"\nMarket Regime in Wins:")
    for regime, count in sorted(regime_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {regime}: {count} ({count/len(wins)*100:.1f}%)")
    
    # Time of day in wins
    time_counts = defaultdict(int)
    for w in wins:
        time_counts[w["time_of_day"]] += 1
    print(f"\nTime of Day in Wins:")
    for time, count in sorted(time_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {time}: {count} ({count/len(wins)*100:.1f}%)")
    
    # Signal strength in wins
    strength_counts = defaultdict(int)
    for w in wins:
        strength_counts[w["signal_strength"]] += 1
    print(f"\nSignal Strength in Wins:")
    for strength, count in sorted(strength_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {strength}: {count} ({count/len(wins)*100:.1f}%)")
    
    # Entry score distribution in wins
    win_scores = [w["entry_score"] for w in wins if w["entry_score"] > 0]
    if win_scores:
        print(f"\nEntry Score in Wins:")
        print(f"  Min: {min(win_scores):.2f}")
        print(f"  Max: {max(win_scores):.2f}")
        print(f"  Avg: {sum(win_scores)/len(win_scores):.2f}")
        print(f"  Median: {sorted(win_scores)[len(win_scores)//2]:.2f}")
    
    # Compare with losses
    print("\n" + "="*80)
    print("COMPARISON: WINS vs LOSSES")
    print("="*80)
    
    # Entry score comparison
    loss_scores = [l["entry_score"] for l in losses if l["entry_score"] > 0]
    if win_scores and loss_scores:
        print(f"\nEntry Score:")
        print(f"  Wins - Avg: {sum(win_scores)/len(win_scores):.2f}, Min: {min(win_scores):.2f}")
        print(f"  Losses - Avg: {sum(loss_scores)/len(loss_scores):.2f}, Min: {min(loss_scores):.2f}")
    
    # Market regime comparison
    loss_regime_counts = defaultdict(int)
    for l in losses:
        loss_regime_counts[l["market_regime"]] += 1
    
    print(f"\nMarket Regime Distribution:")
    all_regimes = set(regime_counts.keys()) | set(loss_regime_counts.keys())
    for regime in sorted(all_regimes):
        win_pct = (regime_counts[regime] / len(wins) * 100) if len(wins) > 0 else 0
        loss_pct = (loss_regime_counts[regime] / len(losses) * 100) if len(losses) > 0 else 0
        print(f"  {regime}: Wins {regime_counts[regime]} ({win_pct:.1f}%) | Losses {loss_regime_counts[regime]} ({loss_pct:.1f}%)")
    
    # Top winning trades
    print("\n" + "="*80)
    print("TOP 10 WINNING TRADES")
    print("="*80)
    top_wins = sorted(wins, key=lambda x: x["pnl_usd"], reverse=True)[:10]
    for i, w in enumerate(top_wins, 1):
        print(f"\n{i}. {w['symbol']} - ${w['pnl_usd']:.2f} ({w['pnl_pct']:.2f}%)")
        print(f"   Regime: {w['market_regime']}, Time: {w['time_of_day']}, Strength: {w['signal_strength']}")
        print(f"   Entry Score: {w['entry_score']:.2f}, Flow: {w['flow_magnitude']}")
    
    # Worst losing trades
    print("\n" + "="*80)
    print("TOP 10 LOSING TRADES")
    print("="*80)
    worst_losses = sorted(losses, key=lambda x: x["pnl_usd"])[:10]
    for i, l in enumerate(worst_losses, 1):
        print(f"\n{i}. {l['symbol']} - ${l['pnl_usd']:.2f} ({l['pnl_pct']:.2f}%)")
        print(f"   Regime: {l['market_regime']}, Time: {l['time_of_day']}, Strength: {l['signal_strength']}")
        print(f"   Entry Score: {l['entry_score']:.2f}, Flow: {l['flow_magnitude']}")

if __name__ == "__main__":
    analyze_winning_trades()
