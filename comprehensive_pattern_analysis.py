#!/usr/bin/env python3
"""
Comprehensive Pattern Analysis - Deep dive into ALL patterns

Analyzes:
1. Entry score patterns (what scores work best)
2. Component combinations (which signals work together)
3. Symbol-specific patterns (which symbols favor which conditions)
4. Time-based patterns (when do trades work best)
5. Market regime patterns (which regimes favor wins)
6. Exit timing patterns (when should we exit)

This goes DEEPER than basic analysis to find actionable patterns.
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
    # Try context first
    score = context.get("entry_score", 0.0)
    if score > 0:
        return score
    
    # Try top-level
    score = trade.get("entry_score", 0.0)
    if score > 0:
        return score
    
    # Try metadata
    metadata = context.get("metadata", {})
    if isinstance(metadata, dict):
        score = metadata.get("entry_score", 0.0)
        if score > 0:
            return score
    
    return 0.0

def extract_time_of_day(trade: dict, context: dict) -> str:
    """Extract time of day from entry timestamp"""
    entry_ts_str = context.get("entry_ts") or trade.get("entry_ts") or trade.get("ts", "")
    if not entry_ts_str:
        return "unknown"
    
    try:
        if isinstance(entry_ts_str, str):
            entry_dt = datetime.fromisoformat(entry_ts_str.replace("Z", "+00:00"))
        else:
            entry_dt = datetime.fromtimestamp(entry_ts_str, tz=timezone.utc)
        hour = entry_dt.hour
        if hour < 9 or hour >= 16:
            return "AFTER_HOURS"
        elif hour == 9:
            return "OPEN"
        elif hour >= 15:
            return "CLOSE"
        else:
            return "MID_DAY"
    except:
        return "unknown"

def analyze_comprehensive_patterns(lookback_days: int = None):
    """Comprehensive pattern analysis"""
    if not ATTRIBUTION_LOG.exists():
        print("attribution.jsonl not found")
        return
    
    cutoff_ts = None
    if lookback_days:
        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        cutoff_ts = cutoff_dt.timestamp()
    
    trades = []
    
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
                
                # Time filter
                if cutoff_ts:
                    entry_ts_str = trade.get("context", {}).get("entry_ts") or trade.get("entry_ts") or trade.get("ts", "")
                    if entry_ts_str:
                        try:
                            if isinstance(entry_ts_str, str):
                                trade_dt = datetime.fromisoformat(entry_ts_str.replace("Z", "+00:00"))
                            else:
                                trade_dt = datetime.fromtimestamp(entry_ts_str, tz=timezone.utc)
                            if trade_dt.timestamp() < cutoff_ts:
                                continue
                        except:
                            pass
                
                context = trade.get("context", {})
                pnl_usd = trade.get("pnl_usd", 0.0)
                pnl_pct = trade.get("pnl_pct", 0.0)
                win = pnl_usd > 0 or pnl_pct > 0
                
                entry_score = extract_entry_score(trade, context)
                time_of_day = extract_time_of_day(trade, context)
                market_regime = context.get("market_regime", "unknown")
                components = context.get("components", {})
                close_reason = context.get("close_reason", "unknown")
                
                trades.append({
                    "symbol": trade.get("symbol", ""),
                    "pnl_usd": pnl_usd,
                    "pnl_pct": pnl_pct,
                    "win": win,
                    "entry_score": entry_score,
                    "time_of_day": time_of_day,
                    "market_regime": market_regime,
                    "components": components,
                    "close_reason": close_reason,
                })
            except:
                continue
    
    if not trades:
        print("No trades found")
        return
    
    wins = [t for t in trades if t["win"]]
    losses = [t for t in trades if not t["win"]]
    
    print("="*80)
    print("COMPREHENSIVE PATTERN ANALYSIS")
    if lookback_days:
        print(f"Time Period: Last {lookback_days} days")
    else:
        print("Time Period: ALL HISTORICAL DATA")
    print("="*80)
    print(f"\nTotal Trades: {len(trades)}")
    print(f"Wins: {len(wins)} ({len(wins)/len(trades)*100:.1f}%)")
    print(f"Losses: {len(losses)} ({len(losses)/len(trades)*100:.1f}%)")
    
    # 1. Entry Score Deep Analysis
    print("\n" + "="*80)
    print("1. ENTRY SCORE DEEP ANALYSIS")
    print("="*80)
    
    # Score ranges with detailed stats
    score_ranges = {
        "2.5-3.0": [],
        "3.0-3.5": [],
        "3.5-4.0": [],
        "4.0-4.5": [],
        "4.5-5.0": [],
        "5.0-5.5": [],
        "5.5+": []
    }
    
    for t in trades:
        score = t["entry_score"]
        if 2.5 <= score < 3.0:
            score_ranges["2.5-3.0"].append(t)
        elif 3.0 <= score < 3.5:
            score_ranges["3.0-3.5"].append(t)
        elif 3.5 <= score < 4.0:
            score_ranges["3.5-4.0"].append(t)
        elif 4.0 <= score < 4.5:
            score_ranges["4.0-4.5"].append(t)
        elif 4.5 <= score < 5.0:
            score_ranges["4.5-5.0"].append(t)
        elif 5.0 <= score < 5.5:
            score_ranges["5.0-5.5"].append(t)
        elif score >= 5.5:
            score_ranges["5.5+"].append(t)
    
    print("\nEntry Score Range Performance:")
    for range_name, range_trades in score_ranges.items():
        if not range_trades:
            continue
        wins_in_range = [t for t in range_trades if t["win"]]
        losses_in_range = [t for t in range_trades if not t["win"]]
        win_rate = len(wins_in_range) / len(range_trades) * 100
        avg_pnl = sum(t["pnl_pct"] for t in range_trades) / len(range_trades)
        net_pnl = sum(t["pnl_pct"] for t in range_trades)
        print(f"  {range_name}: {win_rate:.1f}% ({len(wins_in_range)}W/{len(losses_in_range)}L) | "
              f"Net: {net_pnl:.2f}% | Avg: {avg_pnl:.2f}%")
    
    # 2. Component Combination Analysis
    print("\n" + "="*80)
    print("2. COMPONENT COMBINATION ANALYSIS")
    print("="*80)
    
    # Find active components in each trade
    combo_performance = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": []})
    
    for t in trades:
        active_comps = []
        for comp_name, comp_value in t["components"].items():
            if comp_value and (isinstance(comp_value, (int, float)) and comp_value != 0 or 
                              isinstance(comp_value, dict) and any(v != 0 for v in comp_value.values() if isinstance(v, (int, float)))):
                active_comps.append(comp_name)
        
        if len(active_comps) >= 2:
            # Create combination key (sorted for consistency)
            combo_key = "&".join(sorted(active_comps))
            combo_performance[combo_key]["wins" if t["win"] else "losses"] += 1
            combo_performance[combo_key]["pnl"].append(t["pnl_pct"])
    
    # Top performing combinations
    combo_stats = []
    for combo_key, stats in combo_performance.items():
        total = stats["wins"] + stats["losses"]
        if total >= 3:  # Need at least 3 trades
            win_rate = stats["wins"] / total * 100
            avg_pnl = sum(stats["pnl"]) / len(stats["pnl"])
            combo_stats.append({
                "combo": combo_key,
                "win_rate": win_rate,
                "avg_pnl": avg_pnl,
                "samples": total
            })
    
    combo_stats.sort(key=lambda x: x["win_rate"] * x["samples"], reverse=True)
    
    print("\nTop 10 Component Combinations (by win rate * samples):")
    for i, stat in enumerate(combo_stats[:10], 1):
        print(f"  {i}. {stat['combo']}: {stat['win_rate']:.1f}% ({stat['samples']} trades) | Avg P&L: {stat['avg_pnl']:.2f}%")
    
    # 3. Symbol + Entry Score Analysis
    print("\n" + "="*80)
    print("3. SYMBOL + ENTRY SCORE PATTERNS")
    print("="*80)
    
    symbol_score_perf = defaultdict(lambda: defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": []}))
    
    for t in trades:
        symbol = t["symbol"]
        if t["entry_score"] >= 5.0:
            score_bucket = "5.0+"
        elif t["entry_score"] >= 4.5:
            score_bucket = "4.5-5.0"
        elif t["entry_score"] >= 4.0:
            score_bucket = "4.0-4.5"
        else:
            score_bucket = "<4.0"
        
        symbol_score_perf[symbol][score_bucket]["wins" if t["win"] else "losses"] += 1
        symbol_score_perf[symbol][score_bucket]["pnl"].append(t["pnl_pct"])
    
    print("\nSymbol Performance by Entry Score Range:")
    for symbol in sorted(symbol_score_perf.keys()):
        total_trades = sum(sum(bucket["wins"] + bucket["losses"] for bucket in buckets.values()) 
                          for buckets in [symbol_score_perf[symbol]])
        if total_trades >= 3:
            print(f"\n  {symbol} ({total_trades} trades):")
            for score_bucket in ["5.0+", "4.5-5.0", "4.0-4.5", "<4.0"]:
                if score_bucket in symbol_score_perf[symbol]:
                    bucket = symbol_score_perf[symbol][score_bucket]
                    total = bucket["wins"] + bucket["losses"]
                    if total > 0:
                        win_rate = bucket["wins"] / total * 100
                        avg_pnl = sum(bucket["pnl"]) / len(bucket["pnl"])
                        print(f"    {score_bucket}: {win_rate:.1f}% ({bucket['wins']}W/{bucket['losses']}L) | Avg: {avg_pnl:.2f}%")
    
    # 4. Exit Reason Analysis
    print("\n" + "="*80)
    print("4. EXIT REASON ANALYSIS")
    print("="*80)
    
    exit_performance = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": []})
    
    for t in trades:
        reason = t["close_reason"]
        if reason and reason != "unknown":
            # Extract primary exit reason
            primary = reason.split("+")[0].strip()
            exit_performance[primary]["wins" if t["win"] else "losses"] += 1
            exit_performance[primary]["pnl"].append(t["pnl_pct"])
    
    print("\nExit Reason Performance:")
    for reason, stats in sorted(exit_performance.items(), key=lambda x: x[1]["wins"] + x[1]["losses"], reverse=True):
        total = stats["wins"] + stats["losses"]
        if total >= 3:
            win_rate = stats["wins"] / total * 100
            avg_pnl = sum(stats["pnl"]) / len(stats["pnl"])
            print(f"  {reason}: {win_rate:.1f}% ({stats['wins']}W/{stats['losses']}L) | Avg: {avg_pnl:.2f}%")
    
    # 5. Time of Day Analysis (if we have data)
    print("\n" + "="*80)
    print("5. TIME OF DAY ANALYSIS")
    print("="*80)
    
    time_performance = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": []})
    
    for t in trades:
        time_of_day = t["time_of_day"]
        if time_of_day != "unknown":
            time_performance[time_of_day]["wins" if t["win"] else "losses"] += 1
            time_performance[time_of_day]["pnl"].append(t["pnl_pct"])
    
    if time_performance:
        print("\nTime of Day Performance:")
        for time, stats in sorted(time_performance.items(), key=lambda x: x[1]["wins"] + x[1]["losses"], reverse=True):
            total = stats["wins"] + stats["losses"]
            if total >= 3:
                win_rate = stats["wins"] / total * 100
                avg_pnl = sum(stats["pnl"]) / len(stats["pnl"])
                print(f"  {time}: {win_rate:.1f}% ({stats['wins']}W/{stats['losses']}L) | Avg: {avg_pnl:.2f}%")
    else:
        print("\nNo time of day data available (all 'unknown')")
    
    # 6. Actionable Recommendations
    print("\n" + "="*80)
    print("6. ACTIONABLE RECOMMENDATIONS")
    print("="*80)
    
    # Find best entry score range
    best_range = None
    best_metric = 0
    for range_name, range_trades in score_ranges.items():
        if len(range_trades) >= 5:
            wins_in_range = [t for t in range_trades if t["win"]]
            win_rate = len(wins_in_range) / len(range_trades)
            avg_pnl = sum(t["pnl_pct"] for t in range_trades) / len(range_trades)
            metric = win_rate * 100 + avg_pnl * 10  # Combined metric
            if metric > best_metric:
                best_metric = metric
                best_range = range_name
    
    if best_range:
        print(f"\n1. OPTIMAL ENTRY SCORE RANGE: {best_range}")
        range_trades = score_ranges[best_range]
        wins = [t for t in range_trades if t["win"]]
        win_rate = len(wins) / len(range_trades) * 100
        avg_pnl = sum(t["pnl_pct"] for t in range_trades) / len(range_trades)
        print(f"   Win Rate: {win_rate:.1f}% | Avg P&L: {avg_pnl:.2f}%")
        print(f"   Recommendation: Set entry threshold to {best_range.split('-')[0]}+")
    
    # Find best symbols
    symbol_perf = defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": []})
    for t in trades:
        symbol_perf[t["symbol"]]["wins" if t["win"] else "losses"] += 1
        symbol_perf[t["symbol"]]["pnl"].append(t["pnl_pct"])
    
    best_symbols = []
    for symbol, stats in symbol_perf.items():
        total = stats["wins"] + stats["losses"]
        if total >= 3:
            win_rate = stats["wins"] / total
            avg_pnl = sum(stats["pnl"]) / len(stats["pnl"])
            if win_rate >= 0.6 and avg_pnl > 0:
                best_symbols.append((symbol, win_rate, avg_pnl, total))
    
    if best_symbols:
        best_symbols.sort(key=lambda x: x[1] * x[2], reverse=True)
        print(f"\n2. BEST PERFORMING SYMBOLS (favor these):")
        for symbol, wr, pnl, count in best_symbols[:5]:
            print(f"   {symbol}: {wr*100:.1f}% win rate, {pnl:.2f}% avg P&L ({count} trades)")
    
    # Find worst symbols
    worst_symbols = []
    for symbol, stats in symbol_perf.items():
        total = stats["wins"] + stats["losses"]
        if total >= 3:
            win_rate = stats["wins"] / total
            avg_pnl = sum(stats["pnl"]) / len(stats["pnl"])
            if win_rate < 0.3 or avg_pnl < -1.0:
                worst_symbols.append((symbol, win_rate, avg_pnl, total))
    
    if worst_symbols:
        worst_symbols.sort(key=lambda x: x[1])
        print(f"\n3. WORST PERFORMING SYMBOLS (avoid these):")
        for symbol, wr, pnl, count in worst_symbols[:5]:
            print(f"   {symbol}: {wr*100:.1f}% win rate, {pnl:.2f}% avg P&L ({count} trades)")
    
    # Best component combinations
    if combo_stats:
        best_combo = combo_stats[0]
        print(f"\n4. BEST COMPONENT COMBINATION:")
        print(f"   {best_combo['combo']}: {best_combo['win_rate']:.1f}% win rate")
        print(f"   Recommendation: Look for trades with these components together")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Comprehensive pattern analysis")
    parser.add_argument("--days", type=int, help="Lookback days")
    parser.add_argument("--week", action="store_true", help="Last 7 days")
    parser.add_argument("--month", action="store_true", help="Last 30 days")
    
    args = parser.parse_args()
    
    lookback = None
    if args.week:
        lookback = 7
    elif args.month:
        lookback = 30
    elif args.days:
        lookback = args.days
    
    analyze_comprehensive_patterns(lookback_days=lookback)
