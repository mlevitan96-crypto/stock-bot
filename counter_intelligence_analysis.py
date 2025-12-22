#!/usr/bin/env python3
"""
Counter Intelligence Analysis - Deep analysis of blocked signals and missed opportunities

Analyzes:
1. Blocked trades (blocked_trades.jsonl) - What signals were rejected?
2. UW blocked entries (uw_attribution.jsonl) - What did UW reject and why?
3. Gate events (gate.jsonl) - All gate decisions
4. Signals (signals.jsonl) - All signals generated vs executed
5. Missed opportunities - What blocked signals would have been winners?
6. Valid blocks - What blocked signals would have been losers? (good blocks)
7. Pattern analysis - What patterns exist in blocked vs executed?

This answers:
- Are we blocking too many winners?
- Are we blocking too few losers?
- What patterns should we block/unblock?
- What's the opportunity cost of our filters?
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import statistics

LOGS_DIR = Path("logs")
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"
BLOCKED_TRADES_LOG = LOGS_DIR / "blocked_trades.jsonl"
UW_ATTRIBUTION_LOG = LOGS_DIR / "uw_attribution.jsonl"
GATE_LOG = LOGS_DIR / "gate.jsonl"
SIGNALS_LOG = LOGS_DIR / "signals.jsonl"

def parse_timestamp(ts_str):
    """Parse various timestamp formats"""
    if not ts_str:
        return None
    try:
        if isinstance(ts_str, (int, float)):
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        if isinstance(ts_str, str):
            if ts_str.replace(".", "").replace("-", "").replace(":", "").replace("T", "").replace("Z", "").replace("+", "").isdigit():
                # ISO format
                ts_str = ts_str.replace("Z", "+00:00")
                return datetime.fromisoformat(ts_str)
    except:
        pass
    return None

def load_all_trades():
    """Load all executed trades with outcomes"""
    trades = []
    if not ATTRIBUTION_LOG.exists():
        return trades
    
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
                entry_score = context.get("entry_score", 0.0) or trade.get("entry_score", 0.0)
                pnl_usd = trade.get("pnl_usd", 0.0)
                pnl_pct = trade.get("pnl_pct", 0.0)
                symbol = trade.get("symbol", "")
                
                # Parse timestamp
                entry_ts = None
                for ts_field in ["entry_ts", "ts", "timestamp"]:
                    ts_val = context.get(ts_field) or trade.get(ts_field)
                    if ts_val:
                        entry_ts = parse_timestamp(ts_val)
                        if entry_ts:
                            break
                
                trades.append({
                    "symbol": symbol,
                    "entry_score": entry_score,
                    "pnl_usd": pnl_usd,
                    "pnl_pct": pnl_pct,
                    "win": pnl_usd > 0 or pnl_pct > 0,
                    "entry_ts": entry_ts,
                    "components": context.get("components", {}),
                    "market_regime": context.get("market_regime", "unknown"),
                })
            except:
                continue
    
    return trades

def load_blocked_trades():
    """Load all blocked trades"""
    blocked = []
    if not BLOCKED_TRADES_LOG.exists():
        return blocked
    
    with BLOCKED_TRADES_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                symbol = record.get("symbol", "")
                score = record.get("score", 0.0)
                reason = record.get("reason", "unknown")
                components = record.get("components", {})
                ts = parse_timestamp(record.get("ts") or record.get("timestamp"))
                
                blocked.append({
                    "symbol": symbol,
                    "score": score,
                    "reason": reason,
                    "components": components,
                    "ts": ts,
                    "market_regime": record.get("market_regime", "unknown"),
                })
            except:
                continue
    
    return blocked

def load_uw_blocked():
    """Load UW attribution (blocked entries)"""
    uw_blocked = []
    if not UW_ATTRIBUTION_LOG.exists():
        return uw_blocked
    
    with UW_ATTRIBUTION_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if record.get("decision") != "rejected":
                    continue
                
                symbol = record.get("symbol", "")
                score = record.get("score", 0.0)
                components = record.get("components", {})
                ts = parse_timestamp(record.get("ts"))
                
                uw_blocked.append({
                    "symbol": symbol,
                    "score": score,
                    "components": components,
                    "ts": ts,
                    "source": record.get("source", "uw_v3"),
                    "version": record.get("version", "V3"),
                    "toxicity": record.get("toxicity", 0.0),
                    "freshness": record.get("freshness", 1.0),
                })
            except:
                continue
    
    return uw_blocked

def load_gate_events():
    """Load all gate events"""
    gate_events = []
    if not GATE_LOG.exists():
        return gate_events
    
    with GATE_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                symbol = record.get("symbol", "")
                decision = record.get("decision", "unknown")
                reason = record.get("reason", "unknown")
                score = record.get("score", 0.0)
                ts = parse_timestamp(record.get("ts") or record.get("timestamp"))
                
                gate_events.append({
                    "symbol": symbol,
                    "decision": decision,
                    "reason": reason,
                    "score": score,
                    "ts": ts,
                })
            except:
                continue
    
    return gate_events

def load_all_signals():
    """Load all signals generated"""
    signals = []
    if not SIGNALS_LOG.exists():
        return signals
    
    with SIGNALS_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                symbol = record.get("symbol", "")
                score = record.get("score", 0.0)
                components = record.get("components", {})
                ts = parse_timestamp(record.get("ts") or record.get("timestamp"))
                
                signals.append({
                    "symbol": symbol,
                    "score": score,
                    "components": components,
                    "ts": ts,
                })
            except:
                continue
    
    return signals

def estimate_blocked_outcome(blocked_signal, executed_trades):
    """Estimate if a blocked signal would have been a winner/loser based on similar executed trades"""
    symbol = blocked_signal["symbol"]
    score = blocked_signal["score"]
    
    # Find similar executed trades (same symbol, similar score)
    similar_trades = [
        t for t in executed_trades
        if t["symbol"] == symbol
        and abs(t["entry_score"] - score) < 0.5
    ]
    
    if not similar_trades:
        # Try same symbol, any score
        similar_trades = [
            t for t in executed_trades
            if t["symbol"] == symbol
        ]
    
    if not similar_trades:
        return None
    
    # Calculate expected outcome
    wins = sum(1 for t in similar_trades if t["win"])
    win_rate = wins / len(similar_trades)
    avg_pnl = sum(t["pnl_pct"] for t in similar_trades) / len(similar_trades)
    
    return {
        "estimated_win_rate": win_rate,
        "estimated_avg_pnl": avg_pnl,
        "would_win": win_rate > 0.5,
        "similar_trades_count": len(similar_trades),
    }

def analyze_counter_intelligence():
    """Main analysis function"""
    print("="*80)
    print("COUNTER INTELLIGENCE ANALYSIS")
    print("Deep Analysis of Blocked Signals & Missed Opportunities")
    print("="*80)
    
    # Load all data
    print("\nLoading data...")
    executed_trades = load_all_trades()
    blocked_trades = load_blocked_trades()
    uw_blocked = load_uw_blocked()
    gate_events = load_gate_events()
    all_signals = load_all_signals()
    
    print(f"  Executed trades: {len(executed_trades)}")
    print(f"  Blocked trades: {len(blocked_trades)}")
    print(f"  UW blocked entries: {len(uw_blocked)}")
    print(f"  Gate events: {len(gate_events)}")
    print(f"  All signals: {len(all_signals)}")
    
    # 1. Overall Statistics
    print("\n" + "="*80)
    print("1. OVERALL STATISTICS")
    print("="*80)
    
    if executed_trades:
        executed_wins = sum(1 for t in executed_trades if t["win"])
        executed_win_rate = executed_wins / len(executed_trades) * 100
        executed_avg_pnl = sum(t["pnl_pct"] for t in executed_trades) / len(executed_trades)
        print(f"\nExecuted Trades:")
        print(f"  Total: {len(executed_trades)}")
        print(f"  Win Rate: {executed_win_rate:.1f}% ({executed_wins}W/{len(executed_trades)-executed_wins}L)")
        print(f"  Avg P&L: {executed_avg_pnl:.2f}%")
    
    print(f"\nBlocked Signals:")
    print(f"  Blocked trades: {len(blocked_trades)}")
    print(f"  UW blocked: {len(uw_blocked)}")
    print(f"  Total blocked: {len(blocked_trades) + len(uw_blocked)}")
    
    if all_signals:
        execution_rate = len(executed_trades) / len(all_signals) * 100 if all_signals else 0
        print(f"\nSignal Execution Rate:")
        print(f"  Signals generated: {len(all_signals)}")
        print(f"  Signals executed: {len(executed_trades)}")
        print(f"  Execution rate: {execution_rate:.1f}%")
        print(f"  Block rate: {100 - execution_rate:.1f}%")
    
    # 2. Blocked Signal Analysis
    print("\n" + "="*80)
    print("2. BLOCKED SIGNAL ANALYSIS")
    print("="*80)
    
    # Analyze blocked trades by reason
    blocked_by_reason = defaultdict(list)
    for blocked in blocked_trades:
        reason = blocked["reason"]
        blocked_by_reason[reason].append(blocked)
    
    print("\nBlocked Trades by Reason:")
    for reason, blocks in sorted(blocked_by_reason.items(), key=lambda x: len(x[1]), reverse=True):
        avg_score = sum(b["score"] for b in blocks) / len(blocks) if blocks else 0
        print(f"  {reason}: {len(blocks)} blocks | Avg Score: {avg_score:.2f}")
    
    # Analyze UW blocked by score range
    uw_by_score = {
        "0-2.5": [],
        "2.5-3.5": [],
        "3.5-4.5": [],
        "4.5+": []
    }
    for uw in uw_blocked:
        score = uw["score"]
        if score < 2.5:
            uw_by_score["0-2.5"].append(uw)
        elif score < 3.5:
            uw_by_score["2.5-3.5"].append(uw)
        elif score < 4.5:
            uw_by_score["3.5-4.5"].append(uw)
        else:
            uw_by_score["4.5+"].append(uw)
    
    print("\nUW Blocked Entries by Score Range:")
    for range_name, blocks in uw_by_score.items():
        if blocks:
            avg_score = sum(b["score"] for b in blocks) / len(blocks)
            print(f"  {range_name}: {len(blocks)} blocks | Avg Score: {avg_score:.2f}")
    
    # 3. Missed Opportunities Analysis
    print("\n" + "="*80)
    print("3. MISSED OPPORTUNITIES ANALYSIS")
    print("="*80)
    print("\nEstimating outcomes for blocked signals...")
    
    missed_winners = []
    valid_blocks = []
    uncertain_blocks = []
    
    all_blocked = blocked_trades + uw_blocked
    
    for blocked in all_blocked[:500]:  # Limit for performance
        outcome = estimate_blocked_outcome(blocked, executed_trades)
        if outcome:
            blocked["estimated_outcome"] = outcome
            if outcome["would_win"] and outcome["estimated_win_rate"] > 0.55:
                missed_winners.append(blocked)
            elif not outcome["would_win"] and outcome["estimated_win_rate"] < 0.45:
                valid_blocks.append(blocked)
            else:
                uncertain_blocks.append(blocked)
    
    print(f"\nMissed Opportunities (would have won): {len(missed_winners)}")
    print(f"Valid Blocks (would have lost): {len(valid_blocks)}")
    print(f"Uncertain Blocks: {len(uncertain_blocks)}")
    
    if missed_winners:
        print("\nTop 10 Missed Opportunities (by estimated win rate):")
        missed_winners_sorted = sorted(missed_winners, 
                                      key=lambda x: x["estimated_outcome"]["estimated_win_rate"], 
                                      reverse=True)[:10]
        for i, blocked in enumerate(missed_winners_sorted, 1):
            outcome = blocked["estimated_outcome"]
            print(f"  {i}. {blocked['symbol']} (Score: {blocked['score']:.2f})")
            print(f"     Est. Win Rate: {outcome['estimated_win_rate']*100:.1f}%")
            print(f"     Est. Avg P&L: {outcome['estimated_avg_pnl']:.2f}%")
            print(f"     Based on {outcome['similar_trades_count']} similar trades")
    
    # 4. Pattern Analysis: Blocked vs Executed
    print("\n" + "="*80)
    print("4. PATTERN ANALYSIS: BLOCKED vs EXECUTED")
    print("="*80)
    
    # Score distribution
    executed_scores = [t["entry_score"] for t in executed_trades if t["entry_score"] > 0]
    blocked_scores = [b["score"] for b in all_blocked if b["score"] > 0]
    
    if executed_scores and blocked_scores:
        print("\nScore Distribution:")
        print(f"  Executed - Avg: {sum(executed_scores)/len(executed_scores):.2f}, "
              f"Min: {min(executed_scores):.2f}, Max: {max(executed_scores):.2f}")
        print(f"  Blocked - Avg: {sum(blocked_scores)/len(blocked_scores):.2f}, "
              f"Min: {min(blocked_scores):.2f}, Max: {max(blocked_scores):.2f}")
    
    # Symbol analysis
    executed_symbols = defaultdict(int)
    blocked_symbols = defaultdict(int)
    
    for t in executed_trades:
        executed_symbols[t["symbol"]] += 1
    for b in all_blocked:
        blocked_symbols[b["symbol"]] += 1
    
    print("\nTop Symbols - Executed vs Blocked:")
    all_symbols = set(executed_symbols.keys()) | set(blocked_symbols.keys())
    symbol_comparison = []
    for symbol in sorted(all_symbols, key=lambda s: executed_symbols[s] + blocked_symbols[s], reverse=True)[:15]:
        exec_count = executed_symbols.get(symbol, 0)
        block_count = blocked_symbols.get(symbol, 0)
        total = exec_count + block_count
        if total > 0:
            exec_pct = exec_count / total * 100
            symbol_comparison.append((symbol, exec_count, block_count, exec_pct))
            print(f"  {symbol}: {exec_count} executed, {block_count} blocked ({exec_pct:.1f}% executed)")
    
    # 5. Component Analysis: What components are in blocked vs executed?
    print("\n" + "="*80)
    print("5. COMPONENT ANALYSIS: BLOCKED vs EXECUTED")
    print("="*80)
    
    executed_components = defaultdict(int)
    blocked_components = defaultdict(int)
    
    for t in executed_trades:
        for comp_name in t.get("components", {}).keys():
            executed_components[comp_name] += 1
    
    for b in all_blocked:
        for comp_name in b.get("components", {}).keys():
            blocked_components[comp_name] += 1
    
    print("\nComponent Frequency:")
    all_comps = set(executed_components.keys()) | set(blocked_components.keys())
    for comp in sorted(all_comps):
        exec_freq = executed_components.get(comp, 0)
        block_freq = blocked_components.get(comp, 0)
        total = exec_freq + block_freq
        if total > 0:
            exec_pct = exec_freq / total * 100
            print(f"  {comp}: {exec_freq} executed, {block_freq} blocked ({exec_pct:.1f}% executed)")
    
    # 6. Opportunity Cost Analysis
    print("\n" + "="*80)
    print("6. OPPORTUNITY COST ANALYSIS")
    print("="*80)
    
    if missed_winners:
        total_missed_pnl = sum(m["estimated_outcome"]["estimated_avg_pnl"] for m in missed_winners)
        avg_missed_pnl = total_missed_pnl / len(missed_winners)
        print(f"\nMissed Opportunities Cost:")
        print(f"  Count: {len(missed_winners)}")
        print(f"  Avg Est. P&L: {avg_missed_pnl:.2f}%")
        print(f"  Total Est. P&L: {total_missed_pnl:.2f}%")
    
    if valid_blocks:
        total_saved_loss = sum(abs(v["estimated_outcome"]["estimated_avg_pnl"]) for v in valid_blocks if v["estimated_outcome"]["estimated_avg_pnl"] < 0)
        avg_saved_loss = total_saved_loss / len(valid_blocks) if valid_blocks else 0
        print(f"\nValid Blocks (Saved Losses):")
        print(f"  Count: {len(valid_blocks)}")
        print(f"  Avg Est. Loss Avoided: {avg_saved_loss:.2f}%")
        print(f"  Total Loss Avoided: {total_saved_loss:.2f}%")
    
    # 7. Recommendations
    print("\n" + "="*80)
    print("7. RECOMMENDATIONS")
    print("="*80)
    
    print("\nBased on Counter Intelligence Analysis:")
    
    # Check if we're blocking too many winners
    if missed_winners and len(missed_winners) > len(valid_blocks) * 0.5:
        print(f"\n1. ⚠️  BLOCKING TOO MANY WINNERS")
        print(f"   {len(missed_winners)} blocked signals would have won")
        print(f"   {len(valid_blocks)} blocked signals would have lost")
        print(f"   Recommendation: Relax blocking criteria, especially for high-score signals")
    
    # Check score thresholds
    if blocked_scores:
        high_score_blocked = [s for s in blocked_scores if s >= 4.5]
        if high_score_blocked:
            print(f"\n2. ⚠️  HIGH-SCORE SIGNALS BEING BLOCKED")
            print(f"   {len(high_score_blocked)} signals with score >= 4.5 were blocked")
            print(f"   Recommendation: Review why high-score signals are being blocked")
    
    # Symbol-specific recommendations
    if symbol_comparison:
        low_exec_symbols = [s for s, e, b, p in symbol_comparison if p < 30 and e + b >= 5]
        if low_exec_symbols:
            print(f"\n3. SYMBOLS WITH LOW EXECUTION RATE:")
            for symbol in low_exec_symbols[:5]:
                print(f"   {symbol}: Consider why execution rate is low")
    
    print(f"\n4. DATA VOLUME:")
    print(f"   Total signals analyzed: {len(all_signals)}")
    print(f"   Executed: {len(executed_trades)} ({len(executed_trades)/len(all_signals)*100:.1f}% if all_signals)")
    print(f"   Blocked: {len(all_blocked)} ({len(all_blocked)/len(all_signals)*100:.1f}% if all_signals)")
    print(f"   Recommendation: Continue collecting data for more reliable patterns")

if __name__ == "__main__":
    analyze_counter_intelligence()
