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
from datetime import datetime, timezone, timedelta

LOGS_DIR = Path("logs")
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"

def analyze_winning_trades(lookback_days: int = None):
    """
    Deep dive into winning trades to find patterns
    
    Args:
        lookback_days: Number of days to look back (None = all historical data)
    """
    if not ATTRIBUTION_LOG.exists():
        print("attribution.jsonl not found")
        return
    
    # Calculate cutoff timestamp if lookback specified
    cutoff_ts = None
    if lookback_days:
        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        cutoff_ts = cutoff_dt.timestamp()
    
    wins = []
    losses = []
    skipped_old = 0
    
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
                
                # V4.5: Filter by time if lookback specified
                if cutoff_ts:
                    # Try to get timestamp from various fields
                    trade_ts = None
                    context = trade.get("context", {})
                    entry_ts_str = context.get("entry_ts") or trade.get("entry_ts") or trade.get("ts", "")
                    
                    if entry_ts_str:
                        try:
                            if isinstance(entry_ts_str, str):
                                trade_dt = datetime.fromisoformat(entry_ts_str.replace("Z", "+00:00"))
                            else:
                                trade_dt = datetime.fromtimestamp(entry_ts_str, tz=timezone.utc)
                            trade_ts = trade_dt.timestamp()
                        except:
                            pass
                    
                    # If no timestamp found, try trade_id (format: close_SYMBOL_ISO_DATE)
                    if trade_ts is None and trade_id.startswith("close_"):
                        try:
                            parts = trade_id.split("_")
                            if len(parts) >= 3:
                                date_str = "_".join(parts[2:])
                                trade_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                                trade_ts = trade_dt.timestamp()
                        except:
                            pass
                    
                    if trade_ts and trade_ts < cutoff_ts:
                        skipped_old += 1
                        continue
                
                pnl_usd = trade.get("pnl_usd", 0.0)
                pnl_pct = trade.get("pnl_pct", 0.0)
                context = trade.get("context", {})
                components = context.get("components", {})
                
                # V4.6: Extract entry_score from multiple sources
                entry_score = context.get("entry_score", 0.0)
                if entry_score == 0.0:
                    # Try top-level
                    entry_score = trade.get("entry_score", 0.0)
                if entry_score == 0.0:
                    # Try metadata if available
                    entry_score = context.get("metadata", {}).get("entry_score", 0.0) if isinstance(context.get("metadata"), dict) else 0.0
                
                # V4.6: Extract time_of_day from entry_ts if missing
                time_of_day = context.get("time_of_day", "unknown")
                if time_of_day == "unknown":
                    entry_ts_str = context.get("entry_ts") or trade.get("entry_ts") or trade.get("ts", "")
                    if entry_ts_str:
                        try:
                            if isinstance(entry_ts_str, str):
                                entry_dt = datetime.fromisoformat(entry_ts_str.replace("Z", "+00:00"))
                            else:
                                entry_dt = datetime.fromtimestamp(entry_ts_str, tz=timezone.utc)
                            hour = entry_dt.hour
                            if hour < 9 or hour >= 16:
                                time_of_day = "AFTER_HOURS"
                            elif hour == 9:
                                time_of_day = "OPEN"
                            elif hour >= 15:
                                time_of_day = "CLOSE"
                            else:
                                time_of_day = "MID_DAY"
                        except:
                            pass
                
                # V4.6: Extract signal_strength from entry_score if missing
                signal_strength = context.get("signal_strength", "unknown")
                if signal_strength == "unknown" and entry_score > 0:
                    if entry_score < 2.5:
                        signal_strength = "WEAK"
                    elif entry_score < 3.5:
                        signal_strength = "MODERATE"
                    else:
                        signal_strength = "STRONG"
                
                # V4.6: Extract flow_magnitude from components if missing
                flow_magnitude = context.get("flow_magnitude", "unknown")
                if flow_magnitude == "unknown":
                    flow_comp = components.get("flow") or components.get("options_flow")
                    if isinstance(flow_comp, dict):
                        flow_conv = flow_comp.get("conviction", 0.0)
                    elif isinstance(flow_comp, (int, float)):
                        flow_conv = float(flow_comp)
                    else:
                        flow_conv = 0.0
                    
                    if flow_conv > 0:
                        if flow_conv < 0.3:
                            flow_magnitude = "LOW"
                        elif flow_conv < 0.7:
                            flow_magnitude = "MEDIUM"
                        else:
                            flow_magnitude = "HIGH"
                
                trade_data = {
                    "trade_id": trade_id,
                    "symbol": trade.get("symbol", ""),
                    "pnl_usd": pnl_usd,
                    "pnl_pct": pnl_pct,
                    "context": context,
                    "components": components,
                    "market_regime": context.get("market_regime", "unknown"),
                    "time_of_day": time_of_day,
                    "signal_strength": signal_strength,
                    "flow_magnitude": flow_magnitude,
                    "entry_score": entry_score,
                }
                
                if pnl_usd > 0 or pnl_pct > 0:
                    wins.append(trade_data)
                else:
                    losses.append(trade_data)
            except Exception as e:
                continue
    
    print("="*80)
    print("DEEP TRADE ANALYSIS")
    if lookback_days:
        print(f"Time Period: Last {lookback_days} days")
    else:
        print("Time Period: ALL HISTORICAL DATA")
    print("="*80)
    print(f"\nTotal Trades: {len(wins) + len(losses)}")
    if skipped_old > 0:
        print(f"Skipped (outside time window): {skipped_old}")
    print(f"Wins: {len(wins)} ({len(wins)/(len(wins)+len(losses))*100:.1f}%)" if (len(wins)+len(losses)) > 0 else "Wins: 0")
    print(f"Losses: {len(losses)} ({len(losses)/(len(wins)+len(losses))*100:.1f}%)" if (len(wins)+len(losses)) > 0 else "Losses: 0")
    
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
    
    # Entry score buckets analysis
    print(f"\n" + "="*80)
    print("ENTRY SCORE BUCKET ANALYSIS")
    print("="*80)
    
    buckets = {
        "2.5-3.0": {"wins": 0, "losses": 0, "win_pnl": [], "loss_pnl": []},
        "3.0-3.5": {"wins": 0, "losses": 0, "win_pnl": [], "loss_pnl": []},
        "3.5-4.0": {"wins": 0, "losses": 0, "win_pnl": [], "loss_pnl": []},
        "4.0-4.5": {"wins": 0, "losses": 0, "win_pnl": [], "loss_pnl": []},
        "4.5-5.0": {"wins": 0, "losses": 0, "win_pnl": [], "loss_pnl": []},
        "5.0+": {"wins": 0, "losses": 0, "win_pnl": [], "loss_pnl": []},
    }
    
    for w in wins:
        score = w["entry_score"]
        pnl = w["pnl_pct"]
        if 2.5 <= score < 3.0:
            buckets["2.5-3.0"]["wins"] += 1
            buckets["2.5-3.0"]["win_pnl"].append(pnl)
        elif 3.0 <= score < 3.5:
            buckets["3.0-3.5"]["wins"] += 1
            buckets["3.0-3.5"]["win_pnl"].append(pnl)
        elif 3.5 <= score < 4.0:
            buckets["3.5-4.0"]["wins"] += 1
            buckets["3.5-4.0"]["win_pnl"].append(pnl)
        elif 4.0 <= score < 4.5:
            buckets["4.0-4.5"]["wins"] += 1
            buckets["4.0-4.5"]["win_pnl"].append(pnl)
        elif 4.5 <= score < 5.0:
            buckets["4.5-5.0"]["wins"] += 1
            buckets["4.5-5.0"]["win_pnl"].append(pnl)
        elif score >= 5.0:
            buckets["5.0+"]["wins"] += 1
            buckets["5.0+"]["win_pnl"].append(pnl)
    
    for l in losses:
        score = l["entry_score"]
        pnl = l["pnl_pct"]
        if 2.5 <= score < 3.0:
            buckets["2.5-3.0"]["losses"] += 1
            buckets["2.5-3.0"]["loss_pnl"].append(pnl)
        elif 3.0 <= score < 3.5:
            buckets["3.0-3.5"]["losses"] += 1
            buckets["3.0-3.5"]["loss_pnl"].append(pnl)
        elif 3.5 <= score < 4.0:
            buckets["3.5-4.0"]["losses"] += 1
            buckets["3.5-4.0"]["loss_pnl"].append(pnl)
        elif 4.0 <= score < 4.5:
            buckets["4.0-4.5"]["losses"] += 1
            buckets["4.0-4.5"]["loss_pnl"].append(pnl)
        elif 4.5 <= score < 5.0:
            buckets["4.5-5.0"]["losses"] += 1
            buckets["4.5-5.0"]["loss_pnl"].append(pnl)
        elif score >= 5.0:
            buckets["5.0+"]["losses"] += 1
            buckets["5.0+"]["loss_pnl"].append(pnl)
    
    print(f"\nWin Rate by Entry Score Bucket:")
    for bucket_name, bucket in buckets.items():
        total = bucket["wins"] + bucket["losses"]
        if total > 0:
            win_rate = bucket["wins"] / total * 100
            avg_win = sum(bucket["win_pnl"]) / len(bucket["win_pnl"]) if bucket["win_pnl"] else 0
            avg_loss = sum(bucket["loss_pnl"]) / len(bucket["loss_pnl"]) if bucket["loss_pnl"] else 0
            net_pnl = sum(bucket["win_pnl"]) + sum(bucket["loss_pnl"])
            print(f"  {bucket_name}: {win_rate:.1f}% ({bucket['wins']}W/{bucket['losses']}L) | "
                  f"Avg Win: {avg_win:.2f}% | Avg Loss: {avg_loss:.2f}% | Net: {net_pnl:.2f}%")
    
    # Symbol analysis
    print(f"\n" + "="*80)
    print("SYMBOL PERFORMANCE")
    print("="*80)
    
    symbol_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "win_pnl": [], "loss_pnl": []})
    for w in wins:
        symbol_stats[w["symbol"]]["wins"] += 1
        symbol_stats[w["symbol"]]["win_pnl"].append(w["pnl_pct"])
    for l in losses:
        symbol_stats[l["symbol"]]["losses"] += 1
        symbol_stats[l["symbol"]]["loss_pnl"].append(l["pnl_pct"])
    
    # Sort by total trades
    sorted_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]["wins"] + x[1]["losses"], reverse=True)
    
    print(f"\nTop 15 Symbols by Trade Count:")
    for symbol, stats in sorted_symbols[:15]:
        total = stats["wins"] + stats["losses"]
        win_rate = stats["wins"] / total * 100 if total > 0 else 0
        avg_win = sum(stats["win_pnl"]) / len(stats["win_pnl"]) if stats["win_pnl"] else 0
        avg_loss = sum(stats["loss_pnl"]) / len(stats["loss_pnl"]) if stats["loss_pnl"] else 0
        net_pnl = sum(stats["win_pnl"]) + sum(stats["loss_pnl"])
        print(f"  {symbol}: {win_rate:.1f}% ({stats['wins']}W/{stats['losses']}L) | "
              f"Net: {net_pnl:.2f}% | Avg Win: {avg_win:.2f}% | Avg Loss: {avg_loss:.2f}%")
    
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
    
    # Component analysis - what components are in winning vs losing trades
    print("\n" + "="*80)
    print("COMPONENT PRESENCE IN WINS vs LOSSES")
    print("="*80)
    
    win_components = defaultdict(int)
    loss_components = defaultdict(int)
    
    for w in wins:
        comps = w.get("components", {})
        for comp_name, comp_value in comps.items():
            if comp_value and (isinstance(comp_value, (int, float)) and comp_value != 0 or 
                              isinstance(comp_value, dict) and any(v != 0 for v in comp_value.values() if isinstance(v, (int, float)))):
                win_components[comp_name] += 1
    
    for l in losses:
        comps = l.get("components", {})
        for comp_name, comp_value in comps.items():
            if comp_value and (isinstance(comp_value, (int, float)) and comp_value != 0 or 
                              isinstance(comp_value, dict) and any(v != 0 for v in comp_value.values() if isinstance(v, (int, float)))):
                loss_components[comp_name] += 1
    
    all_components = set(win_components.keys()) | set(loss_components.keys())
    print(f"\nComponent Frequency (present in X% of trades):")
    for comp in sorted(all_components):
        win_pct = (win_components[comp] / len(wins) * 100) if len(wins) > 0 else 0
        loss_pct = (loss_components[comp] / len(losses) * 100) if len(losses) > 0 else 0
        print(f"  {comp}: Wins {win_components[comp]} ({win_pct:.1f}%) | Losses {loss_components[comp]} ({loss_pct:.1f}%)")
    
    # Key insights
    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)
    
    if win_scores and loss_scores:
        score_diff = (sum(win_scores)/len(win_scores)) - (sum(loss_scores)/len(loss_scores))
        print(f"\n1. Entry Score Matters:")
        print(f"   Wins have {score_diff:.2f} higher entry scores on average")
        print(f"   Recommendation: Consider raising entry threshold above 4.5")
    
    # Find best performing entry score range
    best_bucket = None
    best_win_rate = 0
    for bucket_name, bucket in buckets.items():
        total = bucket["wins"] + bucket["losses"]
        if total >= 5:  # Need at least 5 trades
            win_rate = bucket["wins"] / total
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_bucket = bucket_name
    
    if best_bucket:
        print(f"\n2. Best Performing Entry Score Range: {best_bucket}")
        print(f"   Win Rate: {best_win_rate*100:.1f}%")
        print(f"   Recommendation: Focus on trades in this score range")
    
    # Find worst performing symbols
    worst_symbols = [s for s in sorted_symbols if (s[1]["wins"] + s[1]["losses"]) >= 3 and 
                     (s[1]["wins"] / (s[1]["wins"] + s[1]["losses"]) < 0.3)]
    if worst_symbols:
        print(f"\n3. Worst Performing Symbols (avoid):")
        for symbol, stats in worst_symbols[:5]:
            total = stats["wins"] + stats["losses"]
            win_rate = stats["wins"] / total * 100
            print(f"   {symbol}: {win_rate:.1f}% win rate ({stats['wins']}W/{stats['losses']}L)")
    
    # Find best performing symbols
    best_symbols = [s for s in sorted_symbols if (s[1]["wins"] + s[1]["losses"]) >= 3 and 
                    (s[1]["wins"] / (s[1]["wins"] + s[1]["losses"]) > 0.6)]
    if best_symbols:
        print(f"\n4. Best Performing Symbols (favor):")
        for symbol, stats in best_symbols[:5]:
            total = stats["wins"] + stats["losses"]
            win_rate = stats["wins"] / total * 100
            print(f"   {symbol}: {win_rate:.1f}% win rate ({stats['wins']}W/{stats['losses']}L)")
    
    print(f"\n5. Overall Performance:")
    print(f"   Win Rate: {len(wins)/(len(wins)+len(losses))*100:.1f}%")
    print(f"   Total P&L: ${sum(w['pnl_usd'] for w in wins) + sum(l['pnl_usd'] for l in losses):.2f}")
    if len(wins) > 0 and len(losses) > 0:
        avg_win = sum(w["pnl_pct"] for w in wins) / len(wins)
        avg_loss = sum(l["pnl_pct"] for l in losses) / len(losses)
        print(f"   Avg Win: {avg_win:.2f}% | Avg Loss: {avg_loss:.2f}%")
        print(f"   Risk/Reward: {abs(avg_win/avg_loss):.2f}:1" if avg_loss != 0 else "   Risk/Reward: N/A")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Deep trade analysis")
    parser.add_argument("--days", type=int, help="Lookback days (default: all historical)")
    parser.add_argument("--week", action="store_true", help="Analyze last 7 days")
    parser.add_argument("--month", action="store_true", help="Analyze last 30 days")
    
    args = parser.parse_args()
    
    lookback = None
    if args.week:
        lookback = 7
    elif args.month:
        lookback = 30
    elif args.days:
        lookback = args.days
    
    analyze_winning_trades(lookback_days=lookback)
