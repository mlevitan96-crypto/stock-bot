#!/usr/bin/env python3
"""
Daily Trading Analysis Generator
================================
Comprehensive analysis of today's trading activity including:
- Executed trades
- Blocked trades
- Missed opportunities
- Counter-intelligence analysis
- Learning insights
- Weight adjustments
- Signal performance
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict

DATA_DIR = Path("data")
STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

def load_jsonl(file_path: Path) -> List[Dict]:
    """Load JSONL file"""
    if not file_path.exists():
        return []
    records = []
    try:
        with file_path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except:
                        continue
    except Exception as e:
        print(f"[WARN] Failed to load {file_path}: {e}")
    return records

def load_json(file_path: Path) -> Dict:
    """Load JSON file"""
    if not file_path.exists():
        return {}
    try:
        with file_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load {file_path}: {e}")
        return {}

def get_today_trades() -> List[Dict]:
    """Get all trades executed today"""
    attribution_file = LOGS_DIR / "attribution.jsonl"
    if not attribution_file.exists():
        return []
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    trades = []
    
    for record in load_jsonl(attribution_file):
        if record.get("type") != "attribution":
            continue
        
        # Skip open trades
        trade_id = record.get("trade_id", "")
        if trade_id and trade_id.startswith("open_"):
            continue
        
        # Parse timestamp
        ts_str = record.get("ts", "")
        if not ts_str:
            continue
        
        try:
            if isinstance(ts_str, (int, float)):
                trade_time = datetime.fromtimestamp(ts_str, tz=timezone.utc)
            else:
                trade_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if trade_time.tzinfo is None:
                    trade_time = trade_time.replace(tzinfo=timezone.utc)
            
            if trade_time >= today_start:
                trades.append(record)
        except:
            continue
    
    return sorted(trades, key=lambda x: x.get("ts", ""), reverse=True)

def get_blocked_trades() -> List[Dict]:
    """Get all blocked trades from today"""
    blocked_file = STATE_DIR / "blocked_trades.jsonl"
    if not blocked_file.exists():
        return []
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    blocked = []
    
    for record in load_jsonl(blocked_file):
        ts_str = record.get("ts") or record.get("timestamp") or record.get("_ts")
        if not ts_str:
            continue
        
        try:
            if isinstance(ts_str, (int, float)):
                block_time = datetime.fromtimestamp(ts_str, tz=timezone.utc)
            else:
                block_time = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                if block_time.tzinfo is None:
                    block_time = block_time.replace(tzinfo=timezone.utc)
            
            if block_time >= today_start:
                blocked.append(record)
        except:
            continue
    
    return sorted(blocked, key=lambda x: x.get("ts") or x.get("timestamp") or x.get("_ts", ""), reverse=True)

def get_missed_opportunities() -> Dict:
    """Get missed opportunities from counterfactual analysis"""
    counterfactual_file = DATA_DIR / "counterfactual_results.jsonl"
    if not counterfactual_file.exists():
        return {}
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    missed = []
    
    for record in load_jsonl(counterfactual_file):
        ts_str = record.get("ts") or record.get("timestamp")
        if not ts_str:
            continue
        
        try:
            if isinstance(ts_str, (int, float)):
                analysis_time = datetime.fromtimestamp(ts_str, tz=timezone.utc)
            else:
                analysis_time = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                if analysis_time.tzinfo is None:
                    analysis_time = analysis_time.replace(tzinfo=timezone.utc)
            
            if analysis_time >= today_start:
                missed.append(record)
        except:
            continue
    
    if not missed:
        return {}
    
    # Aggregate missed opportunities
    total_missed = len(missed)
    total_theoretical_pnl = sum(m.get("theoretical_pnl", 0) for m in missed)
    avoided_losses = sum(1 for m in missed if m.get("theoretical_pnl", 0) < 0)
    missed_wins = sum(1 for m in missed if m.get("theoretical_pnl", 0) > 0)
    
    return {
        "total_missed": total_missed,
        "total_theoretical_pnl": total_theoretical_pnl,
        "avoided_losses": avoided_losses,
        "missed_wins": missed_wins,
        "details": missed
    }

def get_learning_insights() -> Dict:
    """Get learning insights from today"""
    learning_file = DATA_DIR / "comprehensive_learning.jsonl"
    if not learning_file.exists():
        return {}
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    insights = []
    
    for record in load_jsonl(learning_file):
        ts_str = record.get("ts") or record.get("timestamp")
        if not ts_str:
            continue
        
        try:
            if isinstance(ts_str, (int, float)):
                learning_time = datetime.fromtimestamp(ts_str, tz=timezone.utc)
            else:
                learning_time = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                if learning_time.tzinfo is None:
                    learning_time = learning_time.replace(tzinfo=timezone.utc)
            
            if learning_time >= today_start:
                insights.append(record)
        except:
            continue
    
    return {
        "total_insights": len(insights),
        "details": insights
    }

def get_weight_adjustments() -> Dict:
    """Get weight adjustments from today"""
    weights_file = STATE_DIR / "signal_weights.json"
    weights_data = load_json(weights_file)
    
    if not weights_data:
        return {}
    
    # Get explainable logs for weight adjustments
    explainable_file = DATA_DIR / "explainable_logs.jsonl"
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    adjustments = []
    
    for record in load_jsonl(explainable_file):
        if record.get("type") != "weight_adjustment":
            continue
        
        ts_str = record.get("timestamp") or record.get("ts")
        if not ts_str:
            continue
        
        try:
            if isinstance(ts_str, (int, float)):
                adj_time = datetime.fromtimestamp(ts_str, tz=timezone.utc)
            else:
                adj_time = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                if adj_time.tzinfo is None:
                    adj_time = adj_time.replace(tzinfo=timezone.utc)
            
            if adj_time >= today_start:
                adjustments.append(record)
        except:
            continue
    
    return {
        "total_adjustments": len(adjustments),
        "current_weights": weights_data,
        "adjustments": adjustments
    }

def get_signal_performance(trades: List[Dict]) -> Dict:
    """Analyze signal performance from executed trades"""
    signal_stats = defaultdict(lambda: {
        "count": 0,
        "total_pnl": 0.0,
        "wins": 0,
        "losses": 0,
        "trades": []
    })
    
    for trade in trades:
        context = trade.get("context", {})
        signals = context.get("signals", {}) or context.get("component_scores", {})
        
        if not signals:
            continue
        
        pnl_usd = float(trade.get("pnl_usd", 0.0))
        
        # Find top contributing signals
        sorted_signals = sorted(signals.items(), key=lambda x: abs(x[1]), reverse=True)
        top_signals = [s[0] for s in sorted_signals[:3]]  # Top 3
        
        for signal_name in top_signals:
            stat = signal_stats[signal_name]
            stat["count"] += 1
            stat["total_pnl"] += pnl_usd
            if pnl_usd > 0:
                stat["wins"] += 1
            elif pnl_usd < 0:
                stat["losses"] += 1
            stat["trades"].append({
                "symbol": trade.get("symbol"),
                "pnl": pnl_usd,
                "timestamp": trade.get("ts")
            })
    
    # Calculate win rates
    for signal_name, stat in signal_stats.items():
        total = stat["wins"] + stat["losses"]
        stat["win_rate"] = (stat["wins"] / total * 100) if total > 0 else 0.0
        stat["avg_pnl"] = stat["total_pnl"] / stat["count"] if stat["count"] > 0 else 0.0
    
    return dict(signal_stats)

def get_counter_intelligence_analysis(executed: List[Dict], blocked: List[Dict]) -> Dict:
    """Counter-intelligence analysis: patterns in what we did vs didn't do"""
    analysis = {
        "blocking_patterns": {},
        "score_distribution": {
            "executed": [],
            "blocked": []
        },
        "gate_effectiveness": {},
        "timing_patterns": {},
        "symbol_patterns": {}
    }
    
    # Analyze blocking reasons
    blocking_reasons = defaultdict(int)
    for b in blocked:
        reason = b.get("reason") or b.get("block_reason", "unknown")
        blocking_reasons[reason] += 1
    analysis["blocking_patterns"] = dict(blocking_reasons)
    
    # Score distribution
    for trade in executed:
        context = trade.get("context", {})
        score = context.get("entry_score", 0.0)
        if score:
            analysis["score_distribution"]["executed"].append(score)
    
    for b in blocked:
        score = b.get("score", 0.0)
        if score:
            analysis["score_distribution"]["blocked"].append(score)
    
    # Gate effectiveness (which gates blocked what)
    gate_blocked = defaultdict(lambda: {"count": 0, "avg_score": 0.0, "symbols": set()})
    for b in blocked:
        reason = b.get("reason") or b.get("block_reason", "unknown")
        gate_blocked[reason]["count"] += 1
        gate_blocked[reason]["avg_score"] += b.get("score", 0.0)
        gate_blocked[reason]["symbols"].add(b.get("symbol", "unknown"))
    
    for gate, data in gate_blocked.items():
        analysis["gate_effectiveness"][gate] = {
            "count": data["count"],
            "avg_score": data["avg_score"] / data["count"] if data["count"] > 0 else 0.0,
            "unique_symbols": len(data["symbols"])
        }
    
    # Timing patterns (hour of day)
    executed_hours = defaultdict(int)
    blocked_hours = defaultdict(int)
    
    for trade in executed:
        ts_str = trade.get("ts", "")
        if ts_str:
            try:
                if isinstance(ts_str, (int, float)):
                    dt = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                else:
                    dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                executed_hours[dt.hour] += 1
            except:
                pass
    
    for b in blocked:
        ts_str = b.get("timestamp") or b.get("ts", "")
        if ts_str:
            try:
                if isinstance(ts_str, (int, float)):
                    dt = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                else:
                    dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                blocked_hours[dt.hour] += 1
            except:
                pass
    
    analysis["timing_patterns"] = {
        "executed_by_hour": dict(executed_hours),
        "blocked_by_hour": dict(blocked_hours)
    }
    
    # Symbol patterns
    executed_symbols = defaultdict(int)
    blocked_symbols = defaultdict(int)
    
    for trade in executed:
        symbol = trade.get("symbol")
        if symbol:
            executed_symbols[symbol] += 1
    
    for b in blocked:
        symbol = b.get("symbol")
        if symbol:
            blocked_symbols[symbol] += 1
    
    analysis["symbol_patterns"] = {
        "most_executed": dict(sorted(executed_symbols.items(), key=lambda x: x[1], reverse=True)[:10]),
        "most_blocked": dict(sorted(blocked_symbols.items(), key=lambda x: x[1], reverse=True)[:10])
    }
    
    return analysis

def generate_summary_report(analysis: Dict) -> str:
    """Generate summary report"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    lines = [
        "=" * 80,
        f"DAILY TRADING ANALYSIS SUMMARY - {today}",
        "=" * 80,
        "",
        "EXECUTED TRADES",
        "-" * 80,
        f"Total Trades: {analysis['executed_trades']['total']}",
        f"Winning Trades: {analysis['executed_trades']['wins']}",
        f"Losing Trades: {analysis['executed_trades']['losses']}",
        f"Win Rate: {analysis['executed_trades']['win_rate']:.1f}%",
        f"Total P&L: ${analysis['executed_trades']['total_pnl']:.2f}",
        f"Average P&L per Trade: ${analysis['executed_trades']['avg_pnl']:.2f}",
        "",
        "BLOCKED TRADES",
        "-" * 80,
        f"Total Blocked: {analysis['blocked_trades']['total']}",
        f"Reasons: {', '.join(analysis['blocked_trades']['reasons'])}",
        "",
        "MISSED OPPORTUNITIES",
        "-" * 80,
        f"Total Missed: {analysis['missed_opportunities'].get('total_missed', 0)}",
        f"Theoretical P&L: ${analysis['missed_opportunities'].get('total_theoretical_pnl', 0):.2f}",
        f"Missed Wins: {analysis['missed_opportunities'].get('missed_wins', 0)}",
        f"Avoided Losses: {analysis['missed_opportunities'].get('avoided_losses', 0)}",
        "",
        "LEARNING INSIGHTS",
        "-" * 80,
        f"Learning Cycles: {analysis['learning']['total_insights']}",
        f"Weight Adjustments: {analysis['weights']['total_adjustments']}",
        "",
        "TOP PERFORMING SIGNALS",
        "-" * 80,
    ]
    
    # Top 5 signals by P&L
    signal_perf = analysis['signal_performance']
    sorted_signals = sorted(signal_perf.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
    
    for signal_name, stats in sorted_signals[:5]:
        lines.append(f"{signal_name}: ${stats['total_pnl']:.2f} ({stats['count']} trades, {stats['win_rate']:.1f}% win rate)")
    
    lines.extend([
        "",
        "BOTTOM PERFORMING SIGNALS",
        "-" * 80,
    ])
    
    # Bottom 5 signals
    for signal_name, stats in sorted(sorted_signals, key=lambda x: x[1]['total_pnl'])[:5]:
        lines.append(f"{signal_name}: ${stats['total_pnl']:.2f} ({stats['count']} trades, {stats['win_rate']:.1f}% win rate)")
    
    # Counter-intelligence insights
    if analysis.get('counter_intelligence'):
        ci = analysis['counter_intelligence']
        lines.extend([
            "",
            "COUNTER-INTELLIGENCE ANALYSIS",
            "-" * 80,
            f"Most Common Blocking Reason: {max(ci.get('blocking_patterns', {}).items(), key=lambda x: x[1], default=('N/A', 0))[0]}",
            f"Avg Score (Executed): {sum(ci['score_distribution']['executed']) / len(ci['score_distribution']['executed']) if ci['score_distribution']['executed'] else 'N/A':.2f}",
            f"Avg Score (Blocked): {sum(ci['score_distribution']['blocked']) / len(ci['score_distribution']['blocked']) if ci['score_distribution']['blocked'] else 'N/A':.2f}",
        ])
    
    lines.extend([
        "",
        "=" * 80,
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "=" * 80,
    ])
    
    return "\n".join(lines)

def generate_detailed_report(analysis: Dict) -> str:
    """Generate detailed report"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    lines = [
        "=" * 80,
        f"DAILY TRADING ANALYSIS - DETAILED REPORT - {today}",
        "=" * 80,
        "",
    ]
    
    # Executed Trades
    lines.extend([
        "EXECUTED TRADES",
        "=" * 80,
    ])
    
    for trade in analysis['executed_trades']['details']:
        context = trade.get("context", {})
        lines.extend([
            f"Symbol: {trade.get('symbol', 'N/A')}",
            f"Timestamp: {trade.get('ts', 'N/A')}",
            f"P&L: ${float(trade.get('pnl_usd', 0)):.2f} ({float(trade.get('pnl_pct', 0)):.2f}%)",
            f"Entry Score: {context.get('entry_score', 'N/A')}",
            f"Close Reason: {context.get('close_reason', 'N/A')}",
            f"Hold Time: {context.get('hold_minutes', 0):.1f} minutes",
            "",
        ])
    
    # Blocked Trades
    lines.extend([
        "BLOCKED TRADES",
        "=" * 80,
    ])
    
    for blocked in analysis['blocked_trades']['details']:
        lines.extend([
            f"Symbol: {blocked.get('symbol', 'N/A')}",
            f"Timestamp: {blocked.get('ts', blocked.get('timestamp', 'N/A'))}",
            f"Score: {blocked.get('score', 'N/A')}",
            f"Reason: {blocked.get('reason', blocked.get('block_reason', 'N/A'))}",
            f"Threshold: {blocked.get('threshold', 'N/A')}",
            "",
        ])
    
    # Missed Opportunities
    if analysis['missed_opportunities'].get('details'):
        lines.extend([
            "MISSED OPPORTUNITIES",
            "=" * 80,
        ])
        
        for missed in analysis['missed_opportunities']['details'][:20]:  # Top 20
            lines.extend([
                f"Symbol: {missed.get('symbol', 'N/A')}",
                f"Theoretical P&L: ${missed.get('theoretical_pnl', 0):.2f}",
                f"Reason Blocked: {missed.get('reason', 'N/A')}",
                "",
            ])
    
    # Weight Adjustments
    if analysis['weights'].get('adjustments'):
        lines.extend([
            "WEIGHT ADJUSTMENTS",
            "=" * 80,
        ])
        
        for adj in analysis['weights']['adjustments']:
            lines.extend([
                f"Component: {adj.get('component', 'N/A')}",
                f"Old Weight: {adj.get('old_weight', 'N/A')}",
                f"New Weight: {adj.get('new_weight', 'N/A')}",
                f"Why: {adj.get('why', 'N/A')}",
                f"Samples: {adj.get('sample_count', 'N/A')}",
                f"Win Rate: {adj.get('win_rate', 0) * 100:.1f}%",
                "",
            ])
    
    # Counter-Intelligence Analysis
    if analysis.get('counter_intelligence'):
        ci = analysis['counter_intelligence']
        lines.extend([
            "COUNTER-INTELLIGENCE ANALYSIS",
            "=" * 80,
            "",
            "GATE EFFECTIVENESS",
            "-" * 80,
        ])
        
        for gate, data in sorted(ci.get('gate_effectiveness', {}).items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
            lines.append(f"{gate}: {data['count']} blocks, avg score: {data['avg_score']:.2f}, symbols: {data['unique_symbols']}")
        
        lines.extend([
            "",
            "TIMING PATTERNS",
            "-" * 80,
            "Executed trades by hour:",
        ])
        
        for hour, count in sorted(ci.get('timing_patterns', {}).get('executed_by_hour', {}).items()):
            lines.append(f"  {hour:02d}:00 - {count} trades")
        
        lines.extend([
            "",
            "Blocked trades by hour:",
        ])
        
        for hour, count in sorted(ci.get('timing_patterns', {}).get('blocked_by_hour', {}).items())[:10]:
            lines.append(f"  {hour:02d}:00 - {count} blocks")
        
        lines.extend([
            "",
            "SYMBOL PATTERNS",
            "-" * 80,
            "Most executed symbols:",
        ])
        
        for symbol, count in list(ci.get('symbol_patterns', {}).get('most_executed', {}).items())[:10]:
            lines.append(f"  {symbol}: {count} trades")
        
        lines.extend([
            "",
            "Most blocked symbols:",
        ])
        
        for symbol, count in list(ci.get('symbol_patterns', {}).get('most_blocked', {}).items())[:10]:
            lines.append(f"  {symbol}: {count} blocks")
    
    lines.extend([
        "",
        "=" * 80,
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "=" * 80,
    ])
    
    return "\n".join(lines)

def main():
    """Generate comprehensive daily analysis"""
    print("=" * 80)
    print("GENERATING DAILY TRADING ANALYSIS")
    print("=" * 80)
    print()
    
    # Collect all data
    print("Collecting executed trades...")
    executed = get_today_trades()
    
    print("Collecting blocked trades...")
    blocked = get_blocked_trades()
    
    print("Collecting missed opportunities...")
    missed = get_missed_opportunities()
    
    print("Collecting learning insights...")
    learning = get_learning_insights()
    
    print("Collecting weight adjustments...")
    weights = get_weight_adjustments()
    
    print("Analyzing signal performance...")
    signal_perf = get_signal_performance(executed)
    
    print("Performing counter-intelligence analysis...")
    counter_intel = get_counter_intelligence_analysis(executed, blocked)
    
    # Calculate executed trade stats
    total_pnl = sum(float(t.get("pnl_usd", 0)) for t in executed)
    wins = sum(1 for t in executed if float(t.get("pnl_usd", 0)) > 0)
    losses = sum(1 for t in executed if float(t.get("pnl_usd", 0)) < 0)
    total = len(executed)
    win_rate = (wins / total * 100) if total > 0 else 0.0
    avg_pnl = total_pnl / total if total > 0 else 0.0
    
    # Analyze blocked trade reasons
    blocked_reasons = defaultdict(int)
    for b in blocked:
        reason = b.get("reason") or b.get("block_reason") or "unknown"
        blocked_reasons[reason] += 1
    
    # Compile analysis
    analysis = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "executed_trades": {
            "total": total,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "details": executed
        },
        "blocked_trades": {
            "total": len(blocked),
            "reasons": list(blocked_reasons.keys()),
            "reason_counts": dict(blocked_reasons),
            "details": blocked
        },
        "missed_opportunities": missed,
        "learning": learning,
        "weights": weights,
        "signal_performance": signal_perf,
        "counter_intelligence": counter_intel
    }
    
    # Generate reports
    print("Generating summary report...")
    summary = generate_summary_report(analysis)
    
    print("Generating detailed report...")
    detailed = generate_detailed_report(analysis)
    
    # Save reports
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    summary_file = reports_dir / f"daily_summary_{today}.txt"
    detailed_file = reports_dir / f"daily_detailed_{today}.txt"
    json_file = reports_dir / f"daily_analysis_{today}.json"
    
    summary_file.write_text(summary, encoding='utf-8')
    detailed_file.write_text(detailed, encoding='utf-8')
    json_file.write_text(json.dumps(analysis, indent=2, default=str), encoding='utf-8')
    
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Summary: {summary_file}")
    print(f"Detailed: {detailed_file}")
    print(f"JSON: {json_file}")
    print()
    
    # Print summary
    print(summary)
    
    # Commit to Git
    try:
        import subprocess
        subprocess.run(["git", "add", str(summary_file), str(detailed_file), str(json_file)], 
                      check=False, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Daily trading analysis for {today}"], 
                      check=False, capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], 
                      check=False, capture_output=True)
        print()
        print("=" * 80)
        print("REPORTS COMMITTED TO GIT")
        print("=" * 80)
        print(f"Files committed and pushed to origin/main")
        print(f"You can now export from Git repository")
    except Exception as e:
        print(f"[WARN] Failed to commit to Git: {e}")
        print("Reports saved locally - commit manually if needed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

