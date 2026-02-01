#!/usr/bin/env python3
"""
Comprehensive Daily Trading Analysis
====================================
Complete analysis of today's trading activity including:
- Executed trades (wins, losses, P&L)
- Blocked trades (all reasons)
- Missed opportunities (counter-intelligence)
- UW blocked entries
- Signal analysis (generated vs executed)
- Gate effectiveness
- Performance improvement recommendations
- All new analysis and signals tracking

Output:
- Detailed markdown report (for GitHub)
- Summary markdown report (for GitHub)
- JSON data file (for programmatic analysis)

All reports saved to reports/ directory and committed to Git.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics

# Use config registry for file paths
try:
    from config.registry import LogFiles, StateFiles, CacheFiles, Directories
    ATTRIBUTION_LOG = LogFiles.ATTRIBUTION
    SIGNALS_LOG = Directories.LOGS / "signals.jsonl"
    GATE_LOG = Directories.LOGS / "gate.jsonl"
    EXITS_LOG = Directories.LOGS / "exits.jsonl"
    ORDERS_LOG = LogFiles.ORDERS
    BLOCKED_TRADES_LOG = Directories.STATE / "blocked_trades.jsonl"
    UW_ATTRIBUTION_LOG = CacheFiles.UW_ATTRIBUTION
except ImportError:
    # Fallback if registry not available
    ATTRIBUTION_LOG = Path("logs/attribution.jsonl")
    SIGNALS_LOG = Path("logs/signals.jsonl")
    GATE_LOG = Path("logs/gate.jsonl")
    EXITS_LOG = Path("logs/exits.jsonl")
    ORDERS_LOG = Path("logs/orders.jsonl")
    BLOCKED_TRADES_LOG = Path("state/blocked_trades.jsonl")
    UW_ATTRIBUTION_LOG = CacheFiles.UW_ATTRIBUTION

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

def parse_timestamp(ts_str):
    """Parse various timestamp formats"""
    if not ts_str:
        return None
    try:
        if isinstance(ts_str, (int, float)):
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        if isinstance(ts_str, str):
            ts_str = ts_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    except:
        pass
    return None

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
        print(f"[WARN] Failed to load {file_path}: {e}", file=sys.stderr)
    return records

def get_today_records(records: List[Dict], date_field: str = "ts") -> List[Dict]:
    """Filter records to today only"""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_records = []
    
    for record in records:
        ts_val = record.get(date_field) or record.get("timestamp") or record.get("_ts")
        if not ts_val:
            continue
        
        try:
            record_time = parse_timestamp(ts_val)
            if record_time and record_time >= today_start:
                today_records.append(record)
        except:
            continue
    
    return today_records

def analyze_executed_trades() -> Dict:
    """Analyze executed trades from attribution log"""
    all_trades = load_jsonl(ATTRIBUTION_LOG)
    today_trades = []
    
    for record in all_trades:
        if record.get("type") != "attribution":
            continue
        
        trade_id = record.get("trade_id", "")
        if trade_id and trade_id.startswith("open_"):
            continue
        
        ts_val = record.get("ts") or record.get("timestamp")
        if not ts_val:
            continue
        
        record_time = parse_timestamp(ts_val)
        if record_time and record_time.date() == datetime.now(timezone.utc).date():
            today_trades.append(record)
    
    if not today_trades:
        return {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_pnl_usd": 0.0,
            "total_pnl_pct": 0.0,
            "avg_pnl_usd": 0.0,
            "avg_pnl_pct": 0.0,
            "details": []
        }
    
    total_pnl_usd = sum(float(t.get("pnl_usd", 0)) for t in today_trades)
    total_pnl_pct = sum(float(t.get("pnl_pct", t.get("exit_pnl", 0))) for t in today_trades)
    wins = sum(1 for t in today_trades if float(t.get("pnl_usd", 0)) > 0)
    losses = sum(1 for t in today_trades if float(t.get("pnl_usd", 0)) < 0)
    total = len(today_trades)
    
    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "win_rate": (wins / total * 100) if total > 0 else 0.0,
        "total_pnl_usd": total_pnl_usd,
        "total_pnl_pct": total_pnl_pct,
        "avg_pnl_usd": total_pnl_usd / total if total > 0 else 0.0,
        "avg_pnl_pct": total_pnl_pct / total if total > 0 else 0.0,
        "details": today_trades
    }

def analyze_blocked_trades() -> Dict:
    """Analyze blocked trades"""
    all_blocked = load_jsonl(BLOCKED_TRADES_LOG)
    today_blocked = get_today_records(all_blocked, "ts")
    
    if not today_blocked:
        return {
            "total": 0,
            "by_reason": {},
            "by_score_range": {},
            "details": []
        }
    
    by_reason = defaultdict(int)
    by_score_range = defaultdict(int)
    
    for blocked in today_blocked:
        reason = blocked.get("reason") or blocked.get("block_reason", "unknown")
        by_reason[reason] += 1
        
        score = blocked.get("score", 0.0)
        if score < 2.0:
            by_score_range["<2.0"] += 1
        elif score < 2.5:
            by_score_range["2.0-2.5"] += 1
        elif score < 3.5:
            by_score_range["2.5-3.5"] += 1
        elif score < 4.5:
            by_score_range["3.5-4.5"] += 1
        else:
            by_score_range["4.5+"] += 1
    
    return {
        "total": len(today_blocked),
        "by_reason": dict(by_reason),
        "by_score_range": dict(by_score_range),
        "details": today_blocked
    }

def analyze_uw_blocked_entries() -> Dict:
    """Analyze UW blocked entries"""
    all_uw = load_jsonl(UW_ATTRIBUTION_LOG)
    today_uw_blocked = []
    
    for record in all_uw:
        if record.get("decision") != "rejected":
            continue
        
        ts_val = record.get("ts") or record.get("timestamp")
        if not ts_val:
            continue
        
        record_time = parse_timestamp(ts_val)
        if record_time and record_time.date() == datetime.now(timezone.utc).date():
            today_uw_blocked.append(record)
    
    if not today_uw_blocked:
        return {
            "total": 0,
            "by_score_range": {},
            "by_toxicity": {},
            "by_freshness": {},
            "details": []
        }
    
    by_score_range = defaultdict(int)
    by_toxicity = defaultdict(int)
    by_freshness = defaultdict(int)
    
    for uw in today_uw_blocked:
        score = uw.get("score", 0.0)
        if score < 2.5:
            by_score_range["<2.5"] += 1
        elif score < 3.5:
            by_score_range["2.5-3.5"] += 1
        elif score < 4.5:
            by_score_range["3.5-4.5"] += 1
        else:
            by_score_range["4.5+"] += 1
        
        toxicity = uw.get("toxicity", 0.0)
        if toxicity > 0.9:
            by_toxicity[">0.9"] += 1
        elif toxicity > 0.7:
            by_toxicity["0.7-0.9"] += 1
        else:
            by_toxicity["<0.7"] += 1
        
        freshness = uw.get("freshness", 1.0)
        if freshness < 0.3:
            by_freshness["<0.3"] += 1
        elif freshness < 0.7:
            by_freshness["0.3-0.7"] += 1
        else:
            by_freshness[">0.7"] += 1
    
    return {
        "total": len(today_uw_blocked),
        "by_score_range": dict(by_score_range),
        "by_toxicity": dict(by_toxicity),
        "by_freshness": dict(by_freshness),
        "details": today_uw_blocked
    }

def analyze_signals() -> Dict:
    """Analyze signals generated vs executed"""
    all_signals = load_jsonl(SIGNALS_LOG)
    today_signals = get_today_records(all_signals, "ts")
    
    executed_trades = analyze_executed_trades()
    executed_symbols = set()
    for trade in executed_trades.get("details", []):
        symbol = trade.get("symbol", "")
        if symbol:
            executed_symbols.add(symbol)
    
    signal_symbols = set()
    signal_scores = []
    for signal in today_signals:
        cluster = signal.get("cluster", {})
        symbol = cluster.get("ticker") or cluster.get("symbol") or signal.get("symbol", "")
        if symbol:
            signal_symbols.add(symbol)
        score = cluster.get("composite_score") or cluster.get("score") or signal.get("score", 0.0)
        if score:
            signal_scores.append(float(score))
    
    return {
        "total_generated": len(today_signals),
        "unique_symbols": len(signal_symbols),
        "executed_symbols": len(executed_symbols),
        "execution_rate": (len(executed_symbols) / len(signal_symbols) * 100) if signal_symbols else 0.0,
        "avg_score": statistics.mean(signal_scores) if signal_scores else 0.0,
        "median_score": statistics.median(signal_scores) if signal_scores else 0.0,
        "min_score": min(signal_scores) if signal_scores else 0.0,
        "max_score": max(signal_scores) if signal_scores else 0.0,
        "details": today_signals[:100]  # Limit details to first 100
    }

def analyze_gate_events() -> Dict:
    """Analyze gate blocking events"""
    all_gates = load_jsonl(GATE_LOG)
    today_gates = get_today_records(all_gates, "ts")
    
    if not today_gates:
        return {
            "total": 0,
            "by_gate_type": {},
            "details": []
        }
    
    by_gate_type = defaultdict(int)
    for gate in today_gates:
        gate_type = gate.get("gate_type") or gate.get("type") or "unknown"
        by_gate_type[gate_type] += 1
    
    return {
        "total": len(today_gates),
        "by_gate_type": dict(by_gate_type),
        "details": today_gates
    }

def generate_performance_recommendations(analysis: Dict) -> List[str]:
    """Generate performance improvement recommendations"""
    recommendations = []
    
    executed = analysis.get("executed_trades", {})
    blocked = analysis.get("blocked_trades", {})
    signals = analysis.get("signals", {})
    uw_blocked = analysis.get("uw_blocked_entries", {})
    
    # Win rate recommendations
    win_rate = executed.get("win_rate", 0.0)
    if win_rate < 50.0:
        recommendations.append(f"⚠️ Win rate is {win_rate:.1f}% - below 50% target. Review losing trades for patterns.")
    elif win_rate < 60.0:
        recommendations.append(f"📊 Win rate is {win_rate:.1f}% - approaching target of 60%. Continue monitoring.")
    else:
        recommendations.append(f"✅ Win rate is {win_rate:.1f}% - meeting target. Maintain current strategy.")
    
    # Execution rate recommendations
    exec_rate = signals.get("execution_rate", 0.0)
    if exec_rate < 5.0:
        recommendations.append(f"⚠️ Execution rate is {exec_rate:.1f}% - very low. May be blocking too many trades.")
    elif exec_rate > 50.0:
        recommendations.append(f"⚠️ Execution rate is {exec_rate:.1f}% - very high. May need stricter gates.")
    
    # Blocked trades analysis
    blocked_total = blocked.get("total", 0)
    blocked_reasons = blocked.get("by_reason", {})
    if blocked_total > 0:
        top_reason = max(blocked_reasons.items(), key=lambda x: x[1], default=(None, 0))
        if top_reason[0]:
            recommendations.append(f"📋 Most common block reason: {top_reason[0]} ({top_reason[1]} blocks). Review if this gate is too strict.")
    
    # Score distribution recommendations
    avg_score = signals.get("avg_score", 0.0)
    if avg_score < 2.0:
        recommendations.append(f"⚠️ Average signal score is {avg_score:.2f} - low. Review signal generation quality.")
    
    # UW blocked entries
    uw_total = uw_blocked.get("total", 0)
    if uw_total > 0:
        uw_toxicity = uw_blocked.get("by_toxicity", {})
        high_tox = uw_toxicity.get(">0.9", 0)
        if high_tox > 0:
            recommendations.append(f"🔒 {high_tox} signals blocked due to high toxicity (>0.9). Toxicity filter is working correctly.")
    
    return recommendations

def generate_summary_report(analysis: Dict) -> str:
    """Generate markdown summary report"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    executed = analysis.get("executed_trades", {})
    blocked = analysis.get("blocked_trades", {})
    signals = analysis.get("signals", {})
    uw_blocked = analysis.get("uw_blocked_entries", {})
    gates = analysis.get("gate_events", {})
    recommendations = analysis.get("recommendations", [])
    
    lines = [
        f"# Daily Trading Analysis Summary - {today}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total Trades Executed:** {executed.get('total', 0)}",
        f"- **Win Rate:** {executed.get('win_rate', 0.0):.1f}% ({executed.get('wins', 0)}W / {executed.get('losses', 0)}L)",
        f"- **Total P&L:** ${executed.get('total_pnl_usd', 0.0):.2f} ({executed.get('total_pnl_pct', 0.0):.2f}%)",
        f"- **Average P&L per Trade:** ${executed.get('avg_pnl_usd', 0.0):.2f} ({executed.get('avg_pnl_pct', 0.0):.2f}%)",
        f"- **Signals Generated:** {signals.get('total_generated', 0)}",
        f"- **Execution Rate:** {signals.get('execution_rate', 0.0):.1f}%",
        f"- **Trades Blocked:** {blocked.get('total', 0)}",
        f"- **UW Entries Blocked:** {uw_blocked.get('total', 0)}",
        "",
        "---",
        "",
        "## Executed Trades",
        "",
        f"**Total:** {executed.get('total', 0)} trades",
        f"**Wins:** {executed.get('wins', 0)}",
        f"**Losses:** {executed.get('losses', 0)}",
        f"**Win Rate:** {executed.get('win_rate', 0.0):.1f}%",
        f"**Total P&L:** ${executed.get('total_pnl_usd', 0.0):.2f}",
        f"**Average P&L:** ${executed.get('avg_pnl_usd', 0.0):.2f} per trade",
        "",
        "---",
        "",
        "## Blocked Trades",
        "",
        f"**Total Blocked:** {blocked.get('total', 0)}",
        "",
        "### Blocked by Reason:",
    ]
    
    for reason, count in sorted(blocked.get("by_reason", {}).items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {reason}: {count}")
    
    lines.extend([
        "",
        "### Blocked by Score Range:",
    ])
    
    for score_range, count in sorted(blocked.get("by_score_range", {}).items()):
        lines.append(f"- {score_range}: {count}")
    
    lines.extend([
        "",
        "---",
        "",
        "## UW Blocked Entries",
        "",
        f"**Total:** {uw_blocked.get('total', 0)}",
        "",
        "### By Score Range:",
    ])
    
    for score_range, count in sorted(uw_blocked.get("by_score_range", {}).items()):
        lines.append(f"- {score_range}: {count}")
    
    lines.extend([
        "",
        "---",
        "",
        "## Signal Analysis",
        "",
        f"**Signals Generated:** {signals.get('total_generated', 0)}",
        f"**Unique Symbols:** {signals.get('unique_symbols', 0)}",
        f"**Execution Rate:** {signals.get('execution_rate', 0.0):.1f}%",
        f"**Average Score:** {signals.get('avg_score', 0.0):.2f}",
        f"**Score Range:** {signals.get('min_score', 0.0):.2f} - {signals.get('max_score', 0.0):.2f}",
        "",
        "---",
        "",
        "## Gate Events",
        "",
        f"**Total Gate Events:** {gates.get('total', 0)}",
        "",
    ])
    
    for gate_type, count in sorted(gates.get("by_gate_type", {}).items(), key=lambda x: x[1], reverse=True):
        lines.append(f"- {gate_type}: {count}")
    
    lines.extend([
        "",
        "---",
        "",
        "## Performance Recommendations",
        "",
    ])
    
    for rec in recommendations:
        lines.append(f"- {rec}")
    
    lines.extend([
        "",
        "---",
        "",
        f"*Report generated at {datetime.now(timezone.utc).isoformat()}*",
    ])
    
    return "\n".join(lines)

def generate_detailed_report(analysis: Dict) -> str:
    """Generate detailed markdown report"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    lines = [
        f"# Daily Trading Analysis - Detailed Report - {today}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "",
    ]
    
    # Add summary section
    summary = generate_summary_report(analysis)
    lines.append("## Summary")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>Click to expand summary</summary>")
    lines.append("")
    lines.append(summary.split("---")[0])  # Just the executive summary part
    lines.append("")
    lines.append("</details>")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Executed trades details
    executed = analysis.get("executed_trades", {})
    lines.append("## Executed Trades - Details")
    lines.append("")
    
    for trade in executed.get("details", [])[:50]:  # Limit to 50 most recent
        context = trade.get("context", {})
        symbol = trade.get("symbol", "N/A")
        pnl_usd = trade.get("pnl_usd", 0.0)
        pnl_pct = trade.get("pnl_pct", trade.get("exit_pnl", 0.0))
        entry_score = context.get("entry_score") or trade.get("entry_score", 0.0)
        close_reason = context.get("close_reason", "N/A")
        
        lines.append(f"### {symbol}")
        lines.append(f"- **P&L:** ${pnl_usd:.2f} ({pnl_pct:.2f}%)")
        lines.append(f"- **Entry Score:** {entry_score:.2f}")
        lines.append(f"- **Close Reason:** {close_reason}")
        lines.append("")
    
    # Blocked trades details
    blocked = analysis.get("blocked_trades", {})
    lines.append("---")
    lines.append("")
    lines.append("## Blocked Trades - Details")
    lines.append("")
    
    for blocked_trade in blocked.get("details", [])[:50]:  # Limit to 50
        symbol = blocked_trade.get("symbol", "N/A")
        score = blocked_trade.get("score", 0.0)
        reason = blocked_trade.get("reason") or blocked_trade.get("block_reason", "unknown")
        threshold = blocked_trade.get("threshold", "N/A")
        
        lines.append(f"### {symbol}")
        lines.append(f"- **Score:** {score:.2f}")
        lines.append(f"- **Threshold:** {threshold}")
        lines.append(f"- **Reason:** {reason}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append(f"*Detailed report generated at {datetime.now(timezone.utc).isoformat()}*")
    
    return "\n".join(lines)

def main():
    """Generate comprehensive daily analysis"""
    print("=" * 80)
    print("COMPREHENSIVE DAILY TRADING ANALYSIS")
    print("=" * 80)
    print()
    
    print("Analyzing executed trades...")
    executed_trades = analyze_executed_trades()
    
    print("Analyzing blocked trades...")
    blocked_trades = analyze_blocked_trades()
    
    print("Analyzing UW blocked entries...")
    uw_blocked_entries = analyze_uw_blocked_entries()
    
    print("Analyzing signals...")
    signals = analyze_signals()
    
    print("Analyzing gate events...")
    gate_events = analyze_gate_events()
    
    print("Generating recommendations...")
    analysis = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "executed_trades": executed_trades,
        "blocked_trades": blocked_trades,
        "uw_blocked_entries": uw_blocked_entries,
        "signals": signals,
        "gate_events": gate_events,
    }
    
    recommendations = generate_performance_recommendations(analysis)
    analysis["recommendations"] = recommendations
    
    print("Generating reports...")
    summary_report = generate_summary_report(analysis)
    detailed_report = generate_detailed_report(analysis)
    
    # Save reports
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary_file = REPORTS_DIR / f"daily_analysis_summary_{today}.md"
    detailed_file = REPORTS_DIR / f"daily_analysis_detailed_{today}.md"
    json_file = REPORTS_DIR / f"daily_analysis_{today}.json"
    
    summary_file.write_text(summary_report, encoding='utf-8')
    detailed_file.write_text(detailed_report, encoding='utf-8')
    json_file.write_text(json.dumps(analysis, indent=2, default=str), encoding='utf-8')
    
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Summary: {summary_file}")
    print(f"Detailed: {detailed_file}")
    print(f"JSON: {json_file}")
    print()
    
    # Print summary to console
    print(summary_report)
    print()
    
    # Commit to Git
    try:
        import subprocess
        subprocess.run(["git", "add", str(summary_file), str(detailed_file), str(json_file)], 
                      check=False, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Daily trading analysis for {today}"], 
                      check=False, capture_output=True)
        subprocess.run(["git", "push", "origin", "main"], 
                      check=False, capture_output=True)
        print("=" * 80)
        print("REPORTS COMMITTED TO GIT")
        print("=" * 80)
        print(f"Files committed and pushed to origin/main")
        print(f"You can now download from Git repository")
    except Exception as e:
        print(f"[WARN] Failed to commit to Git: {e}")
        print("Reports saved locally - commit manually if needed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
