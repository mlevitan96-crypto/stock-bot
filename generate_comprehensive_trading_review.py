#!/usr/bin/env python3
"""
Comprehensive Trading Review Generator
Generates a complete trading review report including:
- Executed trades (all analytics)
- Blocked trades (with counter-intelligence)
- Missed opportunities analysis
- Counter-intelligence deep dive
- Performance recommendations
- External review summary
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics

# Import analysis scripts
sys.path.insert(0, str(Path(__file__).parent))
from counter_intelligence_analysis import (
    load_all_trades, load_blocked_trades, load_uw_blocked,
    load_gate_events, load_all_signals, estimate_blocked_outcome
)

def parse_timestamp(ts_str):
    """Parse various timestamp formats"""
    if not ts_str:
        return None
    try:
        if isinstance(ts_str, (int, float)):
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        if isinstance(ts_str, str):
            ts_str = ts_str.replace("Z", "+00:00")
            return datetime.fromisoformat(ts_str)
    except:
        pass
    return None

def is_today(dt: Optional[datetime], target_date: datetime) -> bool:
    """Check if datetime is today"""
    if not dt:
        return False
    return dt.date() == target_date.date()

def filter_today_records(records: List[Dict], target_date: datetime) -> List[Dict]:
    """Filter records to target date only"""
    today_records = []
    for rec in records:
        dt = None
        for ts_field in ["timestamp", "ts", "_ts", "entry_ts", "exit_ts"]:
            ts_val = rec.get(ts_field)
            if ts_val:
                dt = parse_timestamp(ts_val)
                if dt:
                    break
        if is_today(dt, target_date):
            rec["_parsed_timestamp"] = dt
            today_records.append(rec)
    return today_records

def analyze_today_performance(trades: List[Dict]) -> Dict[str, Any]:
    """Deep performance analysis"""
    if not trades:
        return {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_pnl_usd": 0.0,
            "total_pnl_pct": 0.0,
            "avg_pnl_usd": 0.0,
            "avg_pnl_pct": 0.0,
            "best_trade": None,
            "worst_trade": None,
            "by_symbol": {},
            "by_hour": {},
            "by_entry_score": {},
            "by_exit_reason": {},
        }
    
    wins = [t for t in trades if t.get("pnl_usd", 0) > 0 or t.get("pnl_pct", 0) > 0]
    losses = [t for t in trades if t.get("pnl_usd", 0) < 0 or t.get("pnl_pct", 0) < 0]
    
    total_pnl_usd = sum(float(t.get("pnl_usd", 0) or 0) for t in trades)
    total_pnl_pct = sum(float(t.get("pnl_pct", 0) or 0) for t in trades)
    
    best_trade = max(trades, key=lambda t: float(t.get("pnl_pct", 0) or 0))
    worst_trade = min(trades, key=lambda t: float(t.get("pnl_pct", 0) or 0))
    
    by_symbol = defaultdict(list)
    by_hour = defaultdict(list)
    by_entry_score = defaultdict(list)
    by_exit_reason = defaultdict(list)
    
    for trade in trades:
        symbol = trade.get("symbol", "UNKNOWN")
        by_symbol[symbol].append(trade)
        
        dt = trade.get("_parsed_timestamp")
        if dt:
            by_hour[dt.hour].append(trade)
        
        entry_score = trade.get("entry_score") or trade.get("context", {}).get("entry_score", 0)
        if entry_score:
            score_bucket = f"{int(entry_score)}-{int(entry_score)+1}"
            by_entry_score[score_bucket].append(trade)
        
        exit_reason = trade.get("context", {}).get("close_reason", "unknown")
        by_exit_reason[exit_reason].append(trade)
    
    return {
        "total": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": (len(wins) / len(trades) * 100) if trades else 0.0,
        "total_pnl_usd": total_pnl_usd,
        "total_pnl_pct": total_pnl_pct,
        "avg_pnl_usd": total_pnl_usd / len(trades) if trades else 0.0,
        "avg_pnl_pct": total_pnl_pct / len(trades) if trades else 0.0,
        "best_trade": {
            "symbol": best_trade.get("symbol"),
            "pnl_usd": best_trade.get("pnl_usd"),
            "pnl_pct": best_trade.get("pnl_pct"),
        },
        "worst_trade": {
            "symbol": worst_trade.get("symbol"),
            "pnl_usd": worst_trade.get("pnl_usd"),
            "pnl_pct": worst_trade.get("pnl_pct"),
        },
        "by_symbol": {k: {"count": len(v), "pnl": sum(float(t.get("pnl_usd", 0) or 0) for t in v)} for k, v in by_symbol.items()},
        "by_hour": {k: len(v) for k, v in by_hour.items()},
        "by_entry_score": {k: len(v) for k, v in by_entry_score.items()},
        "by_exit_reason": {k: len(v) for k, v in by_exit_reason.items()},
    }

def generate_comprehensive_report(target_date: datetime) -> Dict[str, Any]:
    """Generate comprehensive trading review"""
    
    print(f"Loading data for {target_date.date()}...", file=sys.stderr)
    
    # Load all data (not filtered by date for counter-intelligence)
    all_executed = load_all_trades()
    all_blocked = load_blocked_trades()
    all_uw_blocked = load_uw_blocked()
    all_gates = load_gate_events()
    all_signals = load_all_signals()
    
    # Filter to target date
    today_executed = filter_today_records(all_executed, target_date)
    today_blocked = filter_today_records(all_blocked, target_date)
    today_uw_blocked = filter_today_records(all_uw_blocked, target_date)
    today_gates = filter_today_records(all_gates, target_date)
    today_signals = filter_today_records(all_signals, target_date)
    
    print(f"  Today's executed: {len(today_executed)}", file=sys.stderr)
    print(f"  Today's blocked: {len(today_blocked)}", file=sys.stderr)
    print(f"  Today's UW blocked: {len(today_uw_blocked)}", file=sys.stderr)
    
    # Performance analysis
    performance = analyze_today_performance(today_executed)
    
    # Blocked trades analysis
    blocked_by_reason = defaultdict(list)
    for blocked in today_blocked:
        reason = blocked.get("reason", "unknown")
        blocked_by_reason[reason].append(blocked)
    
    blocked_by_score = {
        "<2.0": [],
        "2.0-2.5": [],
        "2.5-3.5": [],
        "3.5-4.5": [],
        "4.5+": [],
    }
    for blocked in today_blocked:
        score = blocked.get("score", 0)
        if score < 2.0:
            blocked_by_score["<2.0"].append(blocked)
        elif score < 2.5:
            blocked_by_score["2.0-2.5"].append(blocked)
        elif score < 3.5:
            blocked_by_score["2.5-3.5"].append(blocked)
        elif score < 4.5:
            blocked_by_score["3.5-4.5"].append(blocked)
        else:
            blocked_by_score["4.5+"].append(blocked)
    
    # Counter-intelligence: Estimate outcomes for blocked trades
    print("Running counter-intelligence analysis...", file=sys.stderr)
    missed_opportunities = []
    valid_blocks = []
    uncertain_blocks = []
    
    all_blocked_today = today_blocked + today_uw_blocked
    # Use all historical trades for comparison
    for blocked in all_blocked_today[:1000]:  # Limit for performance
        outcome = estimate_blocked_outcome(blocked, all_executed)
        if outcome:
            blocked["_estimated_outcome"] = outcome
            if outcome["would_win"] and outcome["estimated_win_rate"] > 0.55:
                missed_opportunities.append(blocked)
            elif not outcome["would_win"] and outcome["estimated_win_rate"] < 0.45:
                valid_blocks.append(blocked)
            else:
                uncertain_blocks.append(blocked)
    
    # Calculate opportunity cost
    opportunity_cost = {
        "missed_count": len(missed_opportunities),
        "valid_blocks_count": len(valid_blocks),
        "uncertain_count": len(uncertain_blocks),
        "estimated_missed_pnl": sum(
            m.get("_estimated_outcome", {}).get("estimated_avg_pnl", 0) 
            for m in missed_opportunities
        ) if missed_opportunities else 0.0,
        "estimated_avoided_losses": sum(
            abs(v.get("_estimated_outcome", {}).get("estimated_avg_pnl", 0))
            for v in valid_blocks
            if v.get("_estimated_outcome", {}).get("estimated_avg_pnl", 0) < 0
        ) if valid_blocks else 0.0,
    }
    
    # Signal execution rate
    execution_rate = (len(today_executed) / len(today_signals) * 100) if today_signals else 0.0
    
    # Build comprehensive report
    report = {
        "report_date": target_date.date().isoformat(),
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "executed_trades": {
            "count": performance["total"],
            "performance": performance,
            "details": today_executed[:50],  # Limit details
        },
        "blocked_trades": {
            "count": len(today_blocked),
            "by_reason": {k: len(v) for k, v in blocked_by_reason.items()},
            "by_score_range": {k: len(v) for k, v in blocked_by_score.items()},
            "details": today_blocked[:50],  # Limit details
        },
        "uw_blocked": {
            "count": len(today_uw_blocked),
            "details": today_uw_blocked[:50],
        },
        "counter_intelligence": {
            "missed_opportunities": {
                "count": opportunity_cost["missed_count"],
                "estimated_missed_pnl_pct": opportunity_cost["estimated_missed_pnl"],
                "top_missed": [
                    {
                        "symbol": m.get("symbol"),
                        "score": m.get("score"),
                        "reason": m.get("reason"),
                        "estimated_win_rate": m.get("_estimated_outcome", {}).get("estimated_win_rate", 0) * 100,
                        "estimated_pnl": m.get("_estimated_outcome", {}).get("estimated_avg_pnl", 0),
                    }
                    for m in sorted(
                        missed_opportunities, 
                        key=lambda x: x.get("_estimated_outcome", {}).get("estimated_win_rate", 0),
                        reverse=True
                    )[:20]
                ],
            },
            "valid_blocks": {
                "count": opportunity_cost["valid_blocks_count"],
                "estimated_avoided_losses_pct": opportunity_cost["estimated_avoided_losses"],
            },
            "uncertain_blocks": {
                "count": opportunity_cost["uncertain_count"],
            },
        },
        "signals": {
            "generated": len(today_signals),
            "executed": len(today_executed),
            "execution_rate": execution_rate,
        },
        "gate_events": {
            "count": len(today_gates),
            "details": today_gates[:50],
        },
    }
    
    return report

def format_external_review_summary(report: Dict[str, Any]) -> str:
    """Format summary for external review"""
    lines = []
    lines.append("=" * 100)
    lines.append(f"COMPREHENSIVE TRADING REVIEW - {report['report_date']}")
    lines.append("=" * 100)
    lines.append(f"Generated: {report['report_generated_at']}")
    lines.append("")
    
    # Executive Summary
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 100)
    perf = report["executed_trades"]["performance"]
    lines.append(f"Trading Activity: {perf['total']} trades executed")
    lines.append(f"Performance: ${perf['total_pnl_usd']:.2f} ({perf['total_pnl_pct']:.2f}%)")
    lines.append(f"Win Rate: {perf['win_rate']:.1f}% ({perf['wins']}W / {perf['losses']}L)")
    if perf['best_trade']:
        lines.append(f"Best Trade: {perf['best_trade']['symbol']} ({perf['best_trade']['pnl_pct']:.2f}%)")
    if perf['worst_trade']:
        lines.append(f"Worst Trade: {perf['worst_trade']['symbol']} ({perf['worst_trade']['pnl_pct']:.2f}%)")
    lines.append("")
    
    # Blocked Trades
    blocked = report["blocked_trades"]
    lines.append(f"BLOCKED TRADES: {blocked['count']} total")
    lines.append("-" * 100)
    if blocked['by_reason']:
        lines.append("Blocked by Reason:")
        for reason, count in sorted(blocked['by_reason'].items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"  {reason}: {count}")
    if blocked['by_score_range']:
        lines.append("Blocked by Score Range:")
        for score_range, count in sorted(blocked['by_score_range'].items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                lines.append(f"  {score_range}: {count}")
    lines.append("")
    
    # Counter-Intelligence
    ci = report["counter_intelligence"]
    lines.append("COUNTER-INTELLIGENCE ANALYSIS")
    lines.append("-" * 100)
    lines.append(f"Missed Opportunities: {ci['missed_opportunities']['count']} trades")
    lines.append(f"  Estimated Missed P&L: {ci['missed_opportunities']['estimated_missed_pnl_pct']:.2f}%")
    if ci['missed_opportunities']['top_missed']:
        lines.append("  Top Missed Opportunities:")
        for i, missed in enumerate(ci['missed_opportunities']['top_missed'][:10], 1):
            lines.append(f"    {i}. {missed['symbol']} (Score: {missed['score']:.2f}, Est. Win Rate: {missed['estimated_win_rate']:.1f}%, Est. P&L: {missed['estimated_pnl']:.2f}%)")
    lines.append("")
    lines.append(f"Valid Blocks (Avoided Losses): {ci['valid_blocks']['count']} trades")
    lines.append(f"  Estimated Losses Avoided: {ci['valid_blocks']['estimated_avoided_losses_pct']:.2f}%")
    lines.append(f"Uncertain Blocks: {ci['uncertain_blocks']['count']} trades")
    lines.append("")
    
    # Signal Analysis
    signals = report["signals"]
    lines.append("SIGNAL EXECUTION ANALYSIS")
    lines.append("-" * 100)
    lines.append(f"Signals Generated: {signals['generated']}")
    lines.append(f"Signals Executed: {signals['executed']}")
    lines.append(f"Execution Rate: {signals['execution_rate']:.1f}%")
    lines.append("")
    
    # Recommendations
    lines.append("RECOMMENDATIONS FOR IMPROVEMENT")
    lines.append("-" * 100)
    
    if perf['win_rate'] < 50:
        lines.append(f"1. LOW WIN RATE ({perf['win_rate']:.1f}%)")
        lines.append("   - Review entry criteria and signal quality")
        lines.append("   - Analyze losing trades for common patterns")
        lines.append("   - Consider tightening entry thresholds")
    
    if ci['missed_opportunities']['count'] > ci['valid_blocks']['count'] * 0.5:
        lines.append(f"2. MISSING OPPORTUNITIES ({ci['missed_opportunities']['count']} missed vs {ci['valid_blocks']['count']} valid blocks)")
        lines.append("   - Consider relaxing blocking criteria for high-score signals")
        lines.append("   - Review score thresholds and gate effectiveness")
    
    if signals['execution_rate'] < 10:
        lines.append(f"3. VERY LOW EXECUTION RATE ({signals['execution_rate']:.1f}%)")
        lines.append("   - May be over-filtering signals")
        lines.append("   - Review all gate criteria and thresholds")
    
    if perf['total_pnl_pct'] < 0:
        lines.append(f"4. NEGATIVE TOTAL P&L ({perf['total_pnl_pct']:.2f}%)")
        lines.append("   - Strategy review required")
        lines.append("   - Analyze exit timing and risk management")
    
    if not any([perf['win_rate'] < 50, signals['execution_rate'] < 10, perf['total_pnl_pct'] < 0]):
        lines.append("Trading activity within normal parameters")
    
    lines.append("")
    lines.append("=" * 100)
    
    return "\n".join(lines)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate comprehensive trading review")
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Error: Invalid date format. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = datetime.now(timezone.utc)
    
    report = generate_comprehensive_report(target_date)
    
    if args.json:
        output = json.dumps(report, indent=2, default=str)
    else:
        output = format_external_review_summary(report)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        try:
            print(output)
        except UnicodeEncodeError:
            print(output.encode('ascii', 'replace').decode('ascii'))

if __name__ == "__main__":
    main()
