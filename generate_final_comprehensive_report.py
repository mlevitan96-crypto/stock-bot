#!/usr/bin/env python3
"""
Generate Final Comprehensive Trading Report from Real Droplet Data
This script uses the fetched data to create a detailed external review report.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any
from collections import defaultdict
import statistics

LOCAL_DATA_DIR = Path("droplet_data")

def load_all_trades_for_date(target_date: datetime) -> List[Dict]:
    """Load all trades for target date from fetched attribution file"""
    trades = []
    attr_file = LOCAL_DATA_DIR / "attribution.jsonl"
    
    if not attr_file.exists():
        return trades
    
    target_date_str = target_date.date().isoformat()
    
    with attr_file.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                trade = json.loads(line)
                ts_str = trade.get("ts") or trade.get("timestamp")
                if ts_str and target_date_str in str(ts_str):
                    trades.append(trade)
            except:
                continue
    
    return trades

def analyze_trades_deep(trades: List[Dict]) -> Dict[str, Any]:
    """Deep analysis of executed trades"""
    if not trades:
        return {}
    
    wins = []
    losses = []
    total_pnl_usd = 0.0
    total_pnl_pct = 0.0
    
    by_symbol = defaultdict(list)
    by_exit_reason = defaultdict(list)
    by_entry_score = defaultdict(list)
    
    for trade in trades:
        pnl_usd = float(trade.get("pnl_usd", 0) or 0)
        pnl_pct = float(trade.get("pnl_pct", 0) or 0)
        symbol = trade.get("symbol", "UNKNOWN")
        
        total_pnl_usd += pnl_usd
        total_pnl_pct += pnl_pct
        
        if pnl_usd > 0 or pnl_pct > 0:
            wins.append(trade)
        elif pnl_usd < 0 or pnl_pct < 0:
            losses.append(trade)
        
        by_symbol[symbol].append(trade)
        
        context = trade.get("context", {})
        exit_reason = context.get("close_reason", "unknown")
        by_exit_reason[exit_reason].append(trade)
        
        entry_score = trade.get("entry_score") or context.get("entry_score") or 0.0
        if entry_score:
            score_bucket = f"{int(entry_score)}-{int(entry_score)+1}"
            by_entry_score[score_bucket].append(trade)
    
    # Find best and worst
    best_trade = max(trades, key=lambda t: float(t.get("pnl_pct", 0) or 0)) if trades else None
    worst_trade = min(trades, key=lambda t: float(t.get("pnl_pct", 0) or 0)) if trades else None
    
    return {
        "total": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": (len(wins) / len(trades) * 100) if trades else 0.0,
        "total_pnl_usd": total_pnl_usd,
        "total_pnl_pct": total_pnl_pct,
        "avg_pnl_pct": total_pnl_pct / len(trades) if trades else 0.0,
        "best_trade": {
            "symbol": best_trade.get("symbol"),
            "pnl_usd": best_trade.get("pnl_usd"),
            "pnl_pct": best_trade.get("pnl_pct"),
        } if best_trade else None,
        "worst_trade": {
            "symbol": worst_trade.get("symbol"),
            "pnl_usd": worst_trade.get("pnl_usd"),
            "pnl_pct": worst_trade.get("pnl_pct"),
        } if worst_trade else None,
        "by_symbol": {k: {"count": len(v), "pnl": sum(float(t.get("pnl_usd", 0) or 0) for t in v)} for k, v in by_symbol.items()},
        "by_exit_reason": {k: len(v) for k, v in by_exit_reason.items()},
        "by_entry_score": {k: len(v) for k, v in by_entry_score.items()},
        "trades": trades,
    }

def generate_comprehensive_report(target_date: datetime) -> str:
    """Generate comprehensive markdown report"""
    
    # Load JSON report
    json_file = Path("REAL_COMPREHENSIVE_REVIEW_2026-01-08.json")
    if not json_file.exists():
        return "ERROR: JSON report not found. Run fetch_droplet_data_and_generate_report.py first."
    
    with json_file.open("r") as f:
        report_data = json.load(f)
    
    # Deep analysis of trades
    all_trades = load_all_trades_for_date(target_date)
    trade_analysis = analyze_trades_deep(all_trades)
    
    lines = []
    lines.append("# COMPREHENSIVE TRADING REVIEW - January 8, 2026")
    lines.append("")
    lines.append(f"**Report Generated:** {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"**Data Source:** Droplet Production Server (Real Trading Data)")
    lines.append(f"**Review Date:** {target_date.date().isoformat()}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Executive Summary
    lines.append("## EXECUTIVE SUMMARY")
    lines.append("")
    exec_trades = report_data["executed_trades"]
    lines.append(f"- **Total Trades Executed:** {exec_trades['count']}")
    lines.append(f"- **Win Rate:** {exec_trades['win_rate']:.1f}% ({exec_trades['wins']}W / {exec_trades['losses']}L)")
    lines.append(f"- **Total P&L:** ${exec_trades['total_pnl_usd']:.2f} ({exec_trades['total_pnl_pct']:.2f}%)")
    lines.append(f"- **Average P&L per Trade:** {exec_trades['avg_pnl_pct']:.2f}%")
    
    if trade_analysis.get("best_trade"):
        bt = trade_analysis["best_trade"]
        lines.append(f"- **Best Trade:** {bt['symbol']} (${bt['pnl_usd']:.2f}, {bt['pnl_pct']:.2f}%)")
    
    if trade_analysis.get("worst_trade"):
        wt = trade_analysis["worst_trade"]
        lines.append(f"- **Worst Trade:** {wt['symbol']} (${wt['pnl_usd']:.2f}, {wt['pnl_pct']:.2f}%)")
    
    lines.append("")
    
    # Executed Trades Details
    lines.append("## EXECUTED TRADES - DETAILED ANALYSIS")
    lines.append("")
    lines.append(f"**Total Executed:** {exec_trades['count']} trades")
    lines.append("")
    
    if trade_analysis.get("by_symbol"):
        lines.append("### Performance by Symbol")
        lines.append("")
        lines.append("| Symbol | Trades | Total P&L |")
        lines.append("|--------|--------|-----------|")
        for symbol, data in sorted(trade_analysis["by_symbol"].items(), key=lambda x: x[1]["pnl"], reverse=True)[:20]:
            lines.append(f"| {symbol} | {data['count']} | ${data['pnl']:.2f} |")
        lines.append("")
    
    if trade_analysis.get("by_exit_reason"):
        lines.append("### Exits by Reason")
        lines.append("")
        for reason, count in sorted(trade_analysis["by_exit_reason"].items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"- **{reason}:** {count} trades")
        lines.append("")
    
    # Blocked Trades
    blocked = report_data["blocked_trades"]
    lines.append("## BLOCKED TRADES ANALYSIS")
    lines.append("")
    lines.append(f"**Total Blocked:** {blocked['count']} trades")
    lines.append("")
    if blocked.get("by_reason"):
        lines.append("### Blocked by Reason")
        lines.append("")
        for reason, count in sorted(blocked["by_reason"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{reason}:** {count} blocks")
        lines.append("")
    
    # Gate Events
    gates = report_data["gate_events"]
    lines.append("## GATE EVENTS ANALYSIS")
    lines.append("")
    lines.append(f"**Total Gate Events:** {gates['count']}")
    lines.append("")
    if gates.get("by_type"):
        lines.append("### Gate Events by Type")
        lines.append("")
        for gate_type, count in sorted(gates["by_type"].items(), key=lambda x: x[1], reverse=True)[:10]:
            lines.append(f"- **{gate_type}:** {count} events")
        lines.append("")
    
    # Signals
    signals = report_data["signals"]
    lines.append("## SIGNAL GENERATION ANALYSIS")
    lines.append("")
    lines.append(f"**Signals Generated:** {signals['count']}")
    lines.append(f"**Trades Executed:** {exec_trades['count']}")
    execution_rate = (exec_trades['count'] / signals['count'] * 100) if signals['count'] > 0 else 0.0
    lines.append(f"**Execution Rate:** {execution_rate:.1f}%")
    lines.append("")
    
    # UW Attribution
    uw = report_data["uw_attribution"]
    lines.append("## UW ATTRIBUTION ANALYSIS")
    lines.append("")
    lines.append(f"**Total UW Attribution Records:** {uw['count']}")
    lines.append(f"**Blocked Entries:** {uw['blocked']}")
    lines.append(f"**Approved Entries:** {uw['count'] - uw['blocked']}")
    lines.append("")
    
    # Orders
    orders = report_data["orders"]
    lines.append("## ORDER EXECUTION ANALYSIS")
    lines.append("")
    lines.append(f"**Total Orders:** {orders['count']}")
    lines.append("")
    
    # Critical Issues
    lines.append("## CRITICAL ISSUES & RECOMMENDATIONS")
    lines.append("")
    
    if exec_trades['win_rate'] < 50:
        lines.append(f"### 🔴 CRITICAL: Low Win Rate ({exec_trades['win_rate']:.1f}%)")
        lines.append("")
        lines.append("- Win rate is significantly below 50% target")
        lines.append("- Immediate review of entry criteria required")
        lines.append("- Analyze losing trades for common patterns")
        lines.append("")
    
    if exec_trades['total_pnl_pct'] < 0:
        lines.append(f"### 🔴 CRITICAL: Negative Total P&L ({exec_trades['total_pnl_pct']:.2f}%)")
        lines.append("")
        lines.append("- Strategy is losing money")
        lines.append("- Review exit timing and risk management")
        lines.append("- Consider tighter stop losses")
        lines.append("")
    
    if execution_rate > 100:
        lines.append(f"### ⚠️ WARNING: Execution Rate > 100% ({execution_rate:.1f}%)")
        lines.append("")
        lines.append("- More trades than signals suggests data timing issues")
        lines.append("- Verify signal counting logic")
        lines.append("")
    
    if gates.get("by_type", {}).get("unknown", 0) > 0:
        lines.append("### ⚠️ WARNING: Gate Events Not Categorized")
        lines.append("")
        lines.append(f"- {gates['by_type'].get('unknown', 0)} gate events with 'unknown' type")
        lines.append("- Gate event logging needs improvement")
        lines.append("- Cannot analyze gate effectiveness without proper categorization")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("**End of Report**")
    
    return "\n".join(lines)

def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default="2026-01-08")
    parser.add_argument("--output", type=str, default="FINAL_REAL_COMPREHENSIVE_REVIEW_2026-01-08.md")
    
    args = parser.parse_args()
    
    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except:
        target_date = datetime.now(timezone.utc)
    
    report = generate_comprehensive_report(target_date)
    
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Comprehensive report written to {args.output}", file=sys.stderr)

if __name__ == "__main__":
    main()
