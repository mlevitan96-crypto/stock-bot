#!/usr/bin/env python3
"""
Deep Pattern Investigation - Why do high entry scores still lose?

Investigates:
1. What's different about winning 5.0+ trades vs losing 5.0+ trades?
2. Component VALUE analysis (not just presence) - what values work?
3. Hold time optimization - when should we exit?
4. Price action patterns - what happens after entry?
5. Predictive rule generation - create actionable rules
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import statistics

LOGS_DIR = Path("logs")
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"

def extract_entry_score(trade: dict, context: dict) -> float:
    """Extract entry score from multiple possible locations"""
    score = context.get("entry_score", 0.0)
    if score > 0:
        return score
    score = trade.get("entry_score", 0.0)
    if score > 0:
        return score
    metadata = context.get("metadata", {})
    if isinstance(metadata, dict):
        score = metadata.get("entry_score", 0.0)
        if score > 0:
            return score
    return 0.0

def analyze_high_score_trades():
    """Deep dive: Why do high entry score trades (5.0+) still lose?"""
    if not ATTRIBUTION_LOG.exists():
        print("attribution.jsonl not found")
        return
    
    high_score_wins = []
    high_score_losses = []
    all_trades = []
    
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
                
                context = trade.get("context", {})
                entry_score = extract_entry_score(trade, context)
                pnl_usd = trade.get("pnl_usd", 0.0)
                pnl_pct = trade.get("pnl_pct", 0.0)
                components = context.get("components", {})
                win = pnl_usd > 0 or pnl_pct > 0
                
                trade_data = {
                    "symbol": trade.get("symbol", ""),
                    "entry_score": entry_score,
                    "pnl_usd": pnl_usd,
                    "pnl_pct": pnl_pct,
                    "win": win,
                    "components": components,
                    "market_regime": context.get("market_regime", "unknown"),
                    "close_reason": context.get("close_reason", "unknown"),
                    "hold_minutes": context.get("hold_minutes", 0),
                }
                
                all_trades.append(trade_data)
                
                if entry_score >= 5.0:
                    if win:
                        high_score_wins.append(trade_data)
                    else:
                        high_score_losses.append(trade_data)
            except:
                continue
    
    print("="*80)
    print("DEEP PATTERN INVESTIGATION")
    print("="*80)
    print(f"\nTotal Trades: {len(all_trades)}")
    print(f"High Score (5.0+) Wins: {len(high_score_wins)}")
    print(f"High Score (5.0+) Losses: {len(high_score_losses)}")
    
    if not high_score_wins or not high_score_losses:
        print("\n⚠️  Need more high-score trades for comparison")
        return
    
    # 1. Component VALUE Analysis - What values work?
    print("\n" + "="*80)
    print("1. COMPONENT VALUE ANALYSIS")
    print("="*80)
    print("\nWhat component VALUES lead to wins vs losses?")
    
    component_values_win = defaultdict(list)
    component_values_loss = defaultdict(list)
    
    for t in high_score_wins:
        for comp_name, comp_value in t["components"].items():
            if isinstance(comp_value, (int, float)) and comp_value != 0:
                component_values_win[comp_name].append(comp_value)
            elif isinstance(comp_value, dict):
                # Extract numeric values from dict
                for k, v in comp_value.items():
                    if isinstance(v, (int, float)) and v != 0:
                        component_values_win[f"{comp_name}.{k}"].append(v)
    
    for t in high_score_losses:
        for comp_name, comp_value in t["components"].items():
            if isinstance(comp_value, (int, float)) and comp_value != 0:
                component_values_loss[comp_name].append(comp_value)
            elif isinstance(comp_value, dict):
                for k, v in comp_value.items():
                    if isinstance(v, (int, float)) and v != 0:
                        component_values_loss[f"{comp_name}.{k}"].append(v)
    
    print("\nComponent Value Comparison (Wins vs Losses):")
    all_components = set(component_values_win.keys()) | set(component_values_loss.keys())
    for comp in sorted(all_components):
        win_vals = component_values_win[comp]
        loss_vals = component_values_loss[comp]
        if win_vals and loss_vals:
            win_avg = sum(win_vals) / len(win_vals)
            loss_avg = sum(loss_vals) / len(loss_vals)
            win_median = sorted(win_vals)[len(win_vals)//2]
            loss_median = sorted(loss_vals)[len(loss_vals)//2]
            print(f"  {comp}:")
            print(f"    Wins - Avg: {win_avg:.3f}, Median: {win_median:.3f} ({len(win_vals)} samples)")
            print(f"    Losses - Avg: {loss_avg:.3f}, Median: {loss_median:.3f} ({len(loss_vals)} samples)")
            if abs(win_avg - loss_avg) > 0.1:
                print(f"    ⚠️  SIGNIFICANT DIFFERENCE: {abs(win_avg - loss_avg):.3f}")
    
    # 2. Hold Time Analysis
    print("\n" + "="*80)
    print("2. HOLD TIME OPTIMIZATION")
    print("="*80)
    
    hold_time_buckets = {
        "0-60min": [],
        "60-240min": [],
        "240-480min": [],
        "480-1440min": [],
        "1440min+": []
    }
    
    for t in all_trades:
        hold_min = t["hold_minutes"]
        if hold_min < 60:
            hold_time_buckets["0-60min"].append(t)
        elif hold_min < 240:
            hold_time_buckets["60-240min"].append(t)
        elif hold_min < 480:
            hold_time_buckets["240-480min"].append(t)
        elif hold_min < 1440:
            hold_time_buckets["480-1440min"].append(t)
        else:
            hold_time_buckets["1440min+"].append(t)
    
    print("\nHold Time Performance:")
    for bucket_name, bucket_trades in hold_time_buckets.items():
        if not bucket_trades:
            continue
        wins = [t for t in bucket_trades if t["win"]]
        win_rate = len(wins) / len(bucket_trades) * 100
        avg_pnl = sum(t["pnl_pct"] for t in bucket_trades) / len(bucket_trades)
        avg_win = sum(t["pnl_pct"] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t["pnl_pct"] for t in bucket_trades if not t["win"]) / (len(bucket_trades) - len(wins)) if (len(bucket_trades) - len(wins)) > 0 else 0
        print(f"  {bucket_name}: {win_rate:.1f}% ({len(wins)}W/{len(bucket_trades)-len(wins)}L) | "
              f"Avg: {avg_pnl:.2f}% | Win: {avg_win:.2f}% | Loss: {avg_loss:.2f}%")
    
    # 3. What Makes High-Score Winners Different?
    print("\n" + "="*80)
    print("3. HIGH-SCORE WINNERS vs LOSERS")
    print("="*80)
    
    # Symbol analysis for high scores
    symbol_high_score = defaultdict(lambda: {"wins": 0, "losses": 0, "win_pnl": [], "loss_pnl": []})
    for t in high_score_wins:
        symbol_high_score[t["symbol"]]["wins"] += 1
        symbol_high_score[t["symbol"]]["win_pnl"].append(t["pnl_pct"])
    for t in high_score_losses:
        symbol_high_score[t["symbol"]]["losses"] += 1
        symbol_high_score[t["symbol"]]["loss_pnl"].append(t["pnl_pct"])
    
    print("\nHigh-Score (5.0+) Performance by Symbol:")
    for symbol in sorted(symbol_high_score.keys()):
        stats = symbol_high_score[symbol]
        total = stats["wins"] + stats["losses"]
        if total >= 2:
            win_rate = stats["wins"] / total * 100
            avg_win = sum(stats["win_pnl"]) / len(stats["win_pnl"]) if stats["win_pnl"] else 0
            avg_loss = sum(stats["loss_pnl"]) / len(stats["loss_pnl"]) if stats["loss_pnl"] else 0
            print(f"  {symbol}: {win_rate:.1f}% ({stats['wins']}W/{stats['losses']}L) | "
                  f"Win: {avg_win:.2f}% | Loss: {avg_loss:.2f}%")
    
    # Market regime for high scores
    regime_high_score = defaultdict(lambda: {"wins": 0, "losses": 0})
    for t in high_score_wins:
        regime_high_score[t["market_regime"]]["wins"] += 1
    for t in high_score_losses:
        regime_high_score[t["market_regime"]]["losses"] += 1
    
    print("\nHigh-Score (5.0+) Performance by Market Regime:")
    for regime in sorted(regime_high_score.keys()):
        stats = regime_high_score[regime]
        total = stats["wins"] + stats["losses"]
        if total >= 3:
            win_rate = stats["wins"] / total * 100
            print(f"  {regime}: {win_rate:.1f}% ({stats['wins']}W/{stats['losses']}L)")
    
    # 4. Exit Timing Analysis
    print("\n" + "="*80)
    print("4. EXIT TIMING ANALYSIS")
    print("="*80)
    
    # Analyze exit reasons for high-score trades
    exit_reasons_high = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": []})
    for t in high_score_wins + high_score_losses:
        reason = t["close_reason"]
        if reason and reason != "unknown":
            primary = reason.split("+")[0].strip()
            exit_reasons_high[primary]["wins" if t["win"] else "losses"] += 1
            exit_reasons_high[primary]["pnl"].append(t["pnl_pct"])
    
    print("\nExit Reasons for High-Score (5.0+) Trades:")
    for reason, stats in sorted(exit_reasons_high.items(), key=lambda x: x[1]["wins"] + x[1]["losses"], reverse=True):
        total = stats["wins"] + stats["losses"]
        if total >= 2:
            win_rate = stats["wins"] / total * 100
            avg_pnl = sum(stats["pnl"]) / len(stats["pnl"])
            print(f"  {reason}: {win_rate:.1f}% ({stats['wins']}W/{stats['losses']}L) | Avg: {avg_pnl:.2f}%")
    
    # 5. Predictive Rules Generation
    print("\n" + "="*80)
    print("5. PREDICTIVE RULES GENERATION")
    print("="*80)
    
    rules = []
    
    # Rule 1: Entry score threshold
    score_5_plus_wins = [t for t in all_trades if t["entry_score"] >= 5.0 and t["win"]]
    score_5_plus_total = [t for t in all_trades if t["entry_score"] >= 5.0]
    if score_5_plus_total:
        win_rate_5plus = len(score_5_plus_wins) / len(score_5_plus_total) * 100
        if win_rate_5plus >= 45:
            rules.append({
                "rule": "Entry Score >= 5.0",
                "win_rate": win_rate_5plus,
                "confidence": "HIGH" if len(score_5_plus_total) >= 20 else "MEDIUM"
            })
    
    # Rule 2: Symbol-specific rules
    for symbol in ["SPY", "QQQ", "AVGO", "AAPL", "MSTR"]:
        symbol_trades = [t for t in all_trades if t["symbol"] == symbol]
        if len(symbol_trades) >= 3:
            wins = [t for t in symbol_trades if t["win"]]
            win_rate = len(wins) / len(symbol_trades) * 100
            avg_pnl = sum(t["pnl_pct"] for t in symbol_trades) / len(symbol_trades)
            if win_rate >= 60 and avg_pnl > 0:
                rules.append({
                    "rule": f"Symbol = {symbol}",
                    "win_rate": win_rate,
                    "avg_pnl": avg_pnl,
                    "confidence": "HIGH" if len(symbol_trades) >= 5 else "MEDIUM"
                })
    
    # Rule 3: Hold time rules
    best_hold_bucket = None
    best_metric = 0
    for bucket_name, bucket_trades in hold_time_buckets.items():
        if len(bucket_trades) >= 5:
            wins = [t for t in bucket_trades if t["win"]]
            win_rate = len(wins) / len(bucket_trades)
            avg_pnl = sum(t["pnl_pct"] for t in bucket_trades) / len(bucket_trades)
            metric = win_rate * 100 + avg_pnl * 10
            if metric > best_metric:
                best_metric = metric
                best_hold_bucket = bucket_name
    
    if best_hold_bucket:
        bucket_trades = hold_time_buckets[best_hold_bucket]
        wins = [t for t in bucket_trades if t["win"]]
        win_rate = len(wins) / len(bucket_trades) * 100
        avg_pnl = sum(t["pnl_pct"] for t in bucket_trades) / len(bucket_trades)
        rules.append({
            "rule": f"Hold Time: {best_hold_bucket}",
            "win_rate": win_rate,
            "avg_pnl": avg_pnl,
            "confidence": "MEDIUM"
        })
    
    print("\nGenerated Predictive Rules:")
    for i, rule in enumerate(rules, 1):
        print(f"\n  Rule {i}: {rule['rule']}")
        print(f"    Win Rate: {rule['win_rate']:.1f}%")
        if 'avg_pnl' in rule:
            print(f"    Avg P&L: {rule['avg_pnl']:.2f}%")
        print(f"    Confidence: {rule['confidence']}")
    
    # 6. What We're Missing
    print("\n" + "="*80)
    print("6. DATA QUALITY & MISSING INSIGHTS")
    print("="*80)
    
    missing_entry_scores = sum(1 for t in all_trades if t["entry_score"] == 0.0)
    missing_context = sum(1 for t in all_trades if t["market_regime"] == "unknown")
    
    print(f"\nData Quality Issues:")
    print(f"  Missing Entry Scores: {missing_entry_scores}/{len(all_trades)} ({missing_entry_scores/len(all_trades)*100:.1f}%)")
    print(f"  Missing Market Regime: {missing_context}/{len(all_trades)} ({missing_context/len(all_trades)*100:.1f}%)")
    
    if missing_entry_scores > len(all_trades) * 0.3:
        print(f"\n  ⚠️  CRITICAL: {missing_entry_scores/len(all_trades)*100:.1f}% of trades missing entry scores")
        print(f"     This prevents accurate pattern analysis")
        print(f"     Recommendation: Fix entry_score logging in log_exit_attribution()")
    
    # 7. Recommendations
    print("\n" + "="*80)
    print("7. FINAL RECOMMENDATIONS")
    print("="*80)
    
    print("\nBased on Deep Analysis:")
    
    # Best performing combination
    if high_score_wins:
        best_symbols_high = []
        for symbol, stats in symbol_high_score.items():
            total = stats["wins"] + stats["losses"]
            if total >= 2:
                win_rate = stats["wins"] / total
                if win_rate >= 0.6:
                    best_symbols_high.append(symbol)
        
        if best_symbols_high:
            print(f"\n1. HIGH-SCORE WINNERS: Focus on {', '.join(best_symbols_high)}")
            print(f"   These symbols perform well even at high entry scores")
    
    # Hold time recommendation
    if best_hold_bucket:
        print(f"\n2. OPTIMAL HOLD TIME: {best_hold_bucket}")
        print(f"   Trades in this time range show best performance")
    
    # Entry score recommendation
    if score_5_plus_total and len(score_5_plus_total) >= 10:
        win_rate_5plus = len(score_5_plus_wins) / len(score_5_plus_total) * 100
        if win_rate_5plus < 50:
            print(f"\n3. ⚠️  ENTRY SCORE ALONE NOT ENOUGH")
            print(f"   Even 5.0+ scores only win {win_rate_5plus:.1f}% of the time")
            print(f"   Need additional filters (symbol, regime, component values)")
        else:
            print(f"\n3. ENTRY SCORE WORKS: 5.0+ threshold is effective")
    
    print(f"\n4. NEED MORE DATA:")
    print(f"   Current: {len(all_trades)} trades over 8 days")
    print(f"   Recommended: 200+ trades for reliable patterns")
    print(f"   Continue trading to build dataset")

if __name__ == "__main__":
    analyze_high_score_trades()
