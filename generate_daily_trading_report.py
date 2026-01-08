#!/usr/bin/env python3
"""
Daily Trading Report Generator
Comprehensive analysis of today's trading activity including:
- Executed trades
- Blocked trades
- Missed opportunities
- Counter-intelligence analysis
- Analytics and recommendations
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional
import statistics

# Directory paths
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
STATE_DIR = BASE_DIR / "state"
DATA_DIR = BASE_DIR / "data"

# Log files
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"
BLOCKED_TRADES_LOG = STATE_DIR / "blocked_trades.jsonl"
EXIT_LOG = LOGS_DIR / "exit.jsonl"
SIGNALS_LOG = LOGS_DIR / "signals.jsonl"
ORDERS_LOG = LOGS_DIR / "orders.jsonl"
GATE_LOG = LOGS_DIR / "gate.jsonl"
UW_ATTRIBUTION_LOG = DATA_DIR / "uw_attribution.jsonl"
SHADOW_TRADES_LOG = DATA_DIR / "shadow_trades.jsonl"
DAILY_POSTMORTEM = DATA_DIR / "daily_postmortem.jsonl"
LIVE_ORDERS = DATA_DIR / "live_orders.jsonl"
OPS_ERRORS = DATA_DIR / "ops_errors.jsonl"

def parse_timestamp(ts_str):
    """Parse various timestamp formats"""
    if not ts_str:
        return None
    try:
        if isinstance(ts_str, (int, float)):
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        if isinstance(ts_str, str):
            # ISO format
            ts_str = ts_str.replace("Z", "+00:00")
            if "+" not in ts_str and ts_str.endswith("+00:00") == False:
                ts_str = ts_str + "+00:00"
            return datetime.fromisoformat(ts_str)
    except Exception as e:
        pass
    return None

def is_today(dt: Optional[datetime], target_date: datetime) -> bool:
    """Check if datetime is today (UTC)"""
    if not dt:
        return False
    return dt.date() == target_date.date()

def load_jsonl_file(file_path: Path, target_date: datetime) -> List[Dict]:
    """Load and filter JSONL file for today's records"""
    records = []
    if not file_path.exists():
        return records
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    
                    # Try to find timestamp in various fields
                    dt = None
                    for ts_field in ["timestamp", "ts", "_ts", "_dt", "entry_ts", "exit_ts", "time"]:
                        ts_val = rec.get(ts_field)
                        if ts_val:
                            dt = parse_timestamp(ts_val)
                            if dt:
                                break
                    
                    # If no timestamp found, try context
                    if not dt and "context" in rec:
                        ctx = rec.get("context", {})
                        for ts_field in ["timestamp", "ts", "entry_ts", "exit_ts"]:
                            ts_val = ctx.get(ts_field)
                            if ts_val:
                                dt = parse_timestamp(ts_val)
                                if dt:
                                    break
                    
                    # Only include today's records
                    if is_today(dt, target_date):
                        rec["_parsed_timestamp"] = dt
                        records.append(rec)
                except json.JSONDecodeError as e:
                    print(f"Warning: JSON decode error in {file_path.name} line {line_num}: {e}", file=sys.stderr)
                    continue
                except Exception as e:
                    print(f"Warning: Error parsing {file_path.name} line {line_num}: {e}", file=sys.stderr)
                    continue
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
    
    return records

def analyze_executed_trades(trades: List[Dict]) -> Dict[str, Any]:
    """Analyze executed trades"""
    if not trades:
        return {
            "count": 0,
            "total_pnl_usd": 0.0,
            "total_pnl_pct": 0.0,
            "avg_pnl_pct": 0.0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "largest_win": None,
            "largest_loss": None,
            "trades_by_symbol": {},
            "trades_by_hour": {},
        }
    
    wins = []
    losses = []
    total_pnl_usd = 0.0
    total_pnl_pct = 0.0
    trades_by_symbol = defaultdict(list)
    trades_by_hour = defaultdict(list)
    largest_win = None
    largest_loss = None
    
    for trade in trades:
        pnl_usd = float(trade.get("pnl_usd", 0.0) or 0.0)
        pnl_pct = float(trade.get("pnl_pct", 0.0) or 0.0)
        symbol = trade.get("symbol", "UNKNOWN")
        
        total_pnl_usd += pnl_usd
        total_pnl_pct += pnl_pct
        
        if pnl_usd > 0 or pnl_pct > 0:
            wins.append(trade)
            if not largest_win or pnl_pct > largest_win.get("pnl_pct", 0.0):
                largest_win = {"symbol": symbol, "pnl_usd": pnl_usd, "pnl_pct": pnl_pct}
        else:
            losses.append(trade)
            if not largest_loss or pnl_pct < largest_loss.get("pnl_pct", 0.0):
                largest_loss = {"symbol": symbol, "pnl_usd": pnl_usd, "pnl_pct": pnl_pct}
        
        trades_by_symbol[symbol].append(trade)
        
        dt = trade.get("_parsed_timestamp")
        if dt:
            hour = dt.hour
            trades_by_hour[hour].append(trade)
    
    return {
        "count": len(trades),
        "total_pnl_usd": total_pnl_usd,
        "total_pnl_pct": total_pnl_pct,
        "avg_pnl_pct": total_pnl_pct / len(trades) if trades else 0.0,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": (len(wins) / len(trades) * 100) if trades else 0.0,
        "largest_win": largest_win,
        "largest_loss": largest_loss,
        "trades_by_symbol": {k: len(v) for k, v in trades_by_symbol.items()},
        "trades_by_hour": {k: len(v) for k, v in trades_by_hour.items()},
        "details": trades,
    }

def analyze_blocked_trades(blocked: List[Dict]) -> Dict[str, Any]:
    """Analyze blocked trades"""
    if not blocked:
        return {
            "count": 0,
            "by_reason": {},
            "by_symbol": {},
            "avg_score": 0.0,
            "score_distribution": {},
        }
    
    by_reason = defaultdict(list)
    by_symbol = defaultdict(int)
    scores = []
    
    for block in blocked:
        reason = block.get("reason", "unknown")
        symbol = block.get("symbol", "UNKNOWN")
        score = block.get("score", 0.0)
        
        by_reason[reason].append(block)
        by_symbol[symbol] += 1
        if score:
            scores.append(float(score))
    
    score_dist = {}
    if scores:
        score_dist = {
            "min": min(scores),
            "max": max(scores),
            "avg": sum(scores) / len(scores),
            "median": statistics.median(scores) if len(scores) > 1 else scores[0],
        }
    
    return {
        "count": len(blocked),
        "by_reason": {k: len(v) for k, v in by_reason.items()},
        "by_symbol": dict(by_symbol),
        "avg_score": score_dist.get("avg", 0.0) if score_dist else 0.0,
        "score_distribution": score_dist,
        "details": blocked,
    }

def analyze_shadow_trades(shadow: List[Dict]) -> Dict[str, Any]:
    """Analyze shadow trades (counter-intelligence)"""
    if not shadow:
        return {
            "count": 0,
            "details": [],
        }
    
    return {
        "count": len(shadow),
        "details": shadow,
    }

def analyze_gate_events(gates: List[Dict]) -> Dict[str, Any]:
    """Analyze gate blocking events"""
    if not gates:
        return {
            "count": 0,
            "by_decision": {},
            "by_reason": {},
            "by_gate_name": {},
        }
    
    by_decision = defaultdict(int)
    by_reason = defaultdict(int)
    by_gate = defaultdict(int)
    
    for gate in gates:
        decision = gate.get("decision", "unknown")
        reason = gate.get("reason", "unknown")
        gate_name = gate.get("gate_name", "unknown")
        
        by_decision[decision] += 1
        by_reason[reason] += 1
        by_gate[gate_name] += 1
    
    return {
        "count": len(gates),
        "by_decision": dict(by_decision),
        "by_reason": dict(by_reason),
        "by_gate_name": dict(by_gate),
        "details": gates,
    }

def analyze_signals(signals: List[Dict]) -> Dict[str, Any]:
    """Analyze signal generation"""
    if not signals:
        return {
            "count": 0,
            "by_symbol": {},
            "score_distribution": {},
        }
    
    by_symbol = defaultdict(int)
    scores = []
    
    for sig in signals:
        symbol = sig.get("symbol", "UNKNOWN")
        score = sig.get("score", 0.0)
        
        by_symbol[symbol] += 1
        if score:
            scores.append(float(score))
    
    score_dist = {}
    if scores:
        score_dist = {
            "min": min(scores),
            "max": max(scores),
            "avg": sum(scores) / len(scores),
            "median": statistics.median(scores) if len(scores) > 1 else scores[0],
        }
    
    return {
        "count": len(signals),
        "by_symbol": dict(by_symbol),
        "score_distribution": score_dist,
        "details": signals,
    }

def generate_report(target_date: datetime) -> Dict[str, Any]:
    """Generate comprehensive daily trading report"""
    
    print(f"Loading data for {target_date.date()}...", file=sys.stderr)
    
    # Load all data sources
    executed_trades = load_jsonl_file(ATTRIBUTION_LOG, target_date)
    blocked_trades = load_jsonl_file(BLOCKED_TRADES_LOG, target_date)
    exit_events = load_jsonl_file(EXIT_LOG, target_date)
    signals = load_jsonl_file(SIGNALS_LOG, target_date)
    orders = load_jsonl_file(ORDERS_LOG, target_date)
    gate_events = load_jsonl_file(GATE_LOG, target_date)
    uw_attribution = load_jsonl_file(UW_ATTRIBUTION_LOG, target_date)
    shadow_trades = load_jsonl_file(SHADOW_TRADES_LOG, target_date)
    live_orders = load_jsonl_file(LIVE_ORDERS, target_date)
    ops_errors = load_jsonl_file(OPS_ERRORS, target_date)
    
    print(f"  Executed trades: {len(executed_trades)}", file=sys.stderr)
    print(f"  Blocked trades: {len(blocked_trades)}", file=sys.stderr)
    print(f"  Exit events: {len(exit_events)}", file=sys.stderr)
    print(f"  Signals: {len(signals)}", file=sys.stderr)
    print(f"  Orders: {len(orders)}", file=sys.stderr)
    print(f"  Gate events: {len(gate_events)}", file=sys.stderr)
    print(f"  UW attribution: {len(uw_attribution)}", file=sys.stderr)
    print(f"  Shadow trades: {len(shadow_trades)}", file=sys.stderr)
    print(f"  Live orders: {len(live_orders)}", file=sys.stderr)
    print(f"  Ops errors: {len(ops_errors)}", file=sys.stderr)
    
    # Analyze each category
    executed_analysis = analyze_executed_trades(executed_trades)
    blocked_analysis = analyze_blocked_trades(blocked_trades)
    shadow_analysis = analyze_shadow_trades(shadow_trades)
    gate_analysis = analyze_gate_events(gate_events)
    signals_analysis = analyze_signals(signals)
    
    # Calculate execution rate
    total_signals = signals_analysis["count"]
    execution_rate = (executed_analysis["count"] / total_signals * 100) if total_signals > 0 else 0.0
    
    # Counter-intelligence: missed opportunities analysis
    uw_blocked = [r for r in uw_attribution if r.get("decision") == "rejected" or r.get("decision") == "ENTRY_BLOCKED"]
    
    # Calculate opportunity metrics
    missed_opportunities = {
        "blocked_count": blocked_analysis["count"] + len(uw_blocked),
        "executed_count": executed_analysis["count"],
        "execution_rate": execution_rate,
        "block_rate": 100 - execution_rate if total_signals > 0 else 0.0,
    }
    
    # Build comprehensive report
    report = {
        "report_date": target_date.date().isoformat(),
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": {
            "executed_trades": len(executed_trades),
            "blocked_trades": len(blocked_trades),
            "exit_events": len(exit_events),
            "signals": len(signals),
            "orders": len(orders),
            "gate_events": len(gate_events),
            "uw_attribution": len(uw_attribution),
            "shadow_trades": len(shadow_trades),
            "live_orders": len(live_orders),
            "ops_errors": len(ops_errors),
        },
        "executed_trades": executed_analysis,
        "blocked_trades": blocked_analysis,
        "shadow_trades": shadow_analysis,
        "gate_events": gate_analysis,
        "signals": signals_analysis,
        "missed_opportunities": missed_opportunities,
        "uw_blocked": {
            "count": len(uw_blocked),
            "details": uw_blocked,
        },
        "exit_events": {
            "count": len(exit_events),
            "details": exit_events,
        },
        "orders": {
            "count": len(orders),
            "details": orders,
        },
        "ops_errors": {
            "count": len(ops_errors),
            "details": ops_errors,
        },
    }
    
    return report

def format_report_summary(report: Dict[str, Any]) -> str:
    """Format a human-readable summary"""
    lines = []
    lines.append("=" * 80)
    lines.append(f"DAILY TRADING REPORT - {report['report_date']}")
    lines.append("=" * 80)
    lines.append(f"Generated: {report['report_generated_at']}")
    lines.append("")
    
    # Executive Summary
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 80)
    exec_trades = report["executed_trades"]
    blocked = report["blocked_trades"]
    missed = report["missed_opportunities"]
    
    lines.append(f"Executed Trades: {exec_trades['count']}")
    lines.append(f"  Total P&L: ${exec_trades['total_pnl_usd']:.2f} ({exec_trades['total_pnl_pct']:.2f}%)")
    lines.append(f"  Win Rate: {exec_trades['win_rate']:.1f}% ({exec_trades['wins']}W / {exec_trades['losses']}L)")
    lines.append(f"  Avg P&L per Trade: {exec_trades['avg_pnl_pct']:.2f}%")
    if exec_trades['largest_win']:
        lines.append(f"  Largest Win: {exec_trades['largest_win']['symbol']} ({exec_trades['largest_win']['pnl_pct']:.2f}%)")
    if exec_trades['largest_loss']:
        lines.append(f"  Largest Loss: {exec_trades['largest_loss']['symbol']} ({exec_trades['largest_loss']['pnl_pct']:.2f}%)")
    lines.append("")
    
    lines.append(f"Blocked Trades: {blocked['count']}")
    lines.append(f"  Avg Score: {blocked['avg_score']:.2f}")
    if blocked['by_reason']:
        lines.append(f"  Blocked by Reason:")
        for reason, count in sorted(blocked['by_reason'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"    {reason}: {count}")
    lines.append("")
    
    lines.append(f"Signal Execution Rate: {missed['execution_rate']:.1f}%")
    lines.append(f"  Signals Generated: {report['signals']['count']}")
    lines.append(f"  Signals Executed: {exec_trades['count']}")
    lines.append(f"  Signals Blocked: {missed['blocked_count']}")
    lines.append("")
    
    # Counter-Intelligence Analysis
    lines.append("COUNTER-INTELLIGENCE ANALYSIS")
    lines.append("-" * 80)
    lines.append(f"UW Blocked Entries: {report['uw_blocked']['count']}")
    lines.append(f"Shadow Trades: {report['shadow_trades']['count']}")
    lines.append(f"Gate Events: {report['gate_events']['count']}")
    if report['gate_events']['by_decision']:
        lines.append(f"  Gate Decisions:")
        for decision, count in sorted(report['gate_events']['by_decision'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"    {decision}: {count}")
    lines.append("")
    
    # Top Symbols
    if exec_trades['trades_by_symbol']:
        lines.append("TOP TRADED SYMBOLS")
        lines.append("-" * 80)
        for symbol, count in sorted(exec_trades['trades_by_symbol'].items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"  {symbol}: {count} trades")
        lines.append("")
    
    # Recommendations
    lines.append("RECOMMENDATIONS")
    lines.append("-" * 80)
    
    if exec_trades['win_rate'] < 50:
        lines.append(f"⚠️  Low win rate ({exec_trades['win_rate']:.1f}%) - Review entry criteria")
    
    if missed['execution_rate'] < 10:
        lines.append(f"⚠️  Very low execution rate ({missed['execution_rate']:.1f}%) - May be blocking too many opportunities")
    
    if exec_trades['count'] == 0:
        lines.append("⚠️  No trades executed today - Review why no trades were taken")
    
    if report['ops_errors']['count'] > 0:
        lines.append(f"⚠️  {report['ops_errors']['count']} operational errors logged - Review ops_errors for details")
    
    if exec_trades['total_pnl_pct'] < 0:
        lines.append(f"⚠️  Negative total P&L ({exec_trades['total_pnl_pct']:.2f}%) - Review strategy")
    
    if not lines[-1].startswith("⚠️"):
        lines.append("✅ Trading activity within normal parameters")
    
    lines.append("")
    lines.append("=" * 80)
    
    return "\n".join(lines)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate daily trading report")
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    # Parse target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Error: Invalid date format. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
    else:
        target_date = datetime.now(timezone.utc)
    
    # Generate report
    report = generate_report(target_date)
    
    # Output report
    if args.json:
        output = json.dumps(report, indent=2, default=str)
    else:
        output = format_report_summary(report)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        try:
            print(output)
        except UnicodeEncodeError:
            # Fallback for Windows console
            print(output.encode('ascii', 'replace').decode('ascii'))

if __name__ == "__main__":
    main()
