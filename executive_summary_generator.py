#!/usr/bin/env python3
"""
Executive Summary Generator
===========================
Generates comprehensive executive summary with trades, P&L, and learning analysis.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict

DATA_DIR = Path("data")
STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

# Attribution file is written to logs/ by main.py jsonl_write function
ATTRIBUTION_FILE = LOGS_DIR / "attribution.jsonl"
COMPREHENSIVE_LEARNING_FILE = DATA_DIR / "comprehensive_learning.jsonl"
COUNTERFACTUAL_RESULTS = DATA_DIR / "counterfactual_results.jsonl"
WEIGHTS_STATE_FILE = STATE_DIR / "signal_weights.json"


def get_all_trades(lookback_days: int = 30) -> List[Dict[str, Any]]:
    """Get all trades from attribution log."""
    trades = []
    if not ATTRIBUTION_FILE.exists():
        return trades
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    
    try:
        with ATTRIBUTION_FILE.open("r") as f:
            lines = f.readlines()
        
        for line in lines:
            try:
                trade = json.loads(line.strip())
                if trade.get("type") != "attribution":
                    continue
                
                ts_str = trade.get("ts", "")
                if not ts_str:
                    continue
                
                trade_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if trade_time < cutoff_time:
                    continue
                
                trades.append(trade)
            except Exception:
                continue
        
        # Sort by timestamp (newest first)
        trades.sort(key=lambda x: x.get("ts", ""), reverse=True)
        
    except Exception as e:
        print(f"Error reading trades: {e}")
    
    return trades


def calculate_pnl_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate P&L metrics for different time periods."""
    now = datetime.now(timezone.utc)
    two_days_ago = now - timedelta(days=2)
    five_days_ago = now - timedelta(days=5)
    
    pnl_2d = 0.0
    pnl_5d = 0.0
    trades_2d = 0
    trades_5d = 0
    wins_2d = 0
    wins_5d = 0
    
    for trade in trades:
        ts_str = trade.get("ts", "")
        if not ts_str:
            continue
        
        try:
            trade_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            pnl = float(trade.get("pnl_usd", 0.0))
            
            if trade_time >= two_days_ago:
                pnl_2d += pnl
                trades_2d += 1
                if pnl > 0:
                    wins_2d += 1
            
            if trade_time >= five_days_ago:
                pnl_5d += pnl
                trades_5d += 1
                if pnl > 0:
                    wins_5d += 1
        except Exception:
            continue
    
    return {
        "pnl_2d": round(pnl_2d, 2),
        "pnl_5d": round(pnl_5d, 2),
        "trades_2d": trades_2d,
        "trades_5d": trades_5d,
        "win_rate_2d": round(wins_2d / trades_2d * 100, 1) if trades_2d > 0 else 0.0,
        "win_rate_5d": round(wins_5d / trades_5d * 100, 1) if trades_5d > 0 else 0.0
    }


def analyze_signal_performance(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze which signals provided most/least value."""
    signal_pnl = defaultdict(lambda: {"total_pnl": 0.0, "count": 0, "wins": 0, "losses": 0})
    
    for trade in trades:
        context = trade.get("context", {})
        components = context.get("components", {})
        pnl = float(trade.get("pnl_usd", 0.0))
        
        for signal, value in components.items():
            if isinstance(value, (int, float)) and value != 0:
                signal_pnl[signal]["total_pnl"] += pnl * abs(value)  # Weight by signal strength
                signal_pnl[signal]["count"] += 1
                if pnl > 0:
                    signal_pnl[signal]["wins"] += 1
                else:
                    signal_pnl[signal]["losses"] += 1
    
    # Calculate average P&L per signal
    signal_analysis = {}
    for signal, data in signal_pnl.items():
        if data["count"] > 0:
            signal_analysis[signal] = {
                "total_pnl": round(data["total_pnl"], 2),
                "avg_pnl": round(data["total_pnl"] / data["count"], 2),
                "count": data["count"],
                "win_rate": round(data["wins"] / data["count"] * 100, 1) if data["count"] > 0 else 0.0
            }
    
    # Sort by total P&L
    sorted_signals = sorted(signal_analysis.items(), key=lambda x: x[1]["total_pnl"], reverse=True)
    
    top_signals = dict(sorted_signals[:5])  # Top 5
    bottom_signals = dict(sorted_signals[-5:])  # Bottom 5
    
    return {
        "top_signals": top_signals,
        "bottom_signals": bottom_signals,
        "all_signals": signal_analysis
    }


def get_learning_insights() -> Dict[str, Any]:
    """Get learning insights from comprehensive learning system."""
    insights = {
        "daily_learnings": [],
        "weekly_learnings": [],
        "weight_adjustments": {},
        "counterfactual_insights": {}
    }
    
    # Read comprehensive learning results
    if COMPREHENSIVE_LEARNING_FILE.exists():
        try:
            with COMPREHENSIVE_LEARNING_FILE.open("r") as f:
                lines = f.readlines()
            
            now = datetime.now(timezone.utc)
            one_day_ago = now - timedelta(days=1)
            seven_days_ago = now - timedelta(days=7)
            
            for line in lines[-100:]:  # Last 100 learning cycles
                try:
                    learning = json.loads(line.strip())
                    ts_str = learning.get("timestamp", "")
                    if not ts_str:
                        continue
                    
                    learning_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    
                    # Daily learnings
                    if learning_time >= one_day_ago:
                        if learning.get("weight_variations", {}).get("best_variations"):
                            insights["daily_learnings"].append({
                                "type": "weight_optimization",
                                "data": learning["weight_variations"]["best_variations"]
                            })
                    
                    # Weekly learnings
                    if learning_time >= seven_days_ago:
                        if learning.get("timing", {}).get("best_scenario"):
                            insights["weekly_learnings"].append({
                                "type": "timing_optimization",
                                "data": learning["timing"]
                            })
                        if learning.get("sizing", {}).get("best_scenario"):
                            insights["weekly_learnings"].append({
                                "type": "sizing_optimization",
                                "data": learning["sizing"]
                            })
                
                except Exception:
                    continue
        except Exception:
            pass
    
    # Get weight adjustments from state
    if WEIGHTS_STATE_FILE.exists():
        try:
            weights_data = json.loads(WEIGHTS_STATE_FILE.read_text())
            if "entry_weights" in weights_data:
                entry_weights = weights_data["entry_weights"]
                if "weight_bands" in entry_weights:
                    adjustments = {}
                    for component, band in entry_weights["weight_bands"].items():
                        if band.get("current", 1.0) != 1.0:
                            adjustments[component] = {
                                "current_multiplier": band.get("current", 1.0),
                                "sample_count": band.get("sample_count", 0),
                                "win_rate": round(band.get("wins", 0) / max(band.get("sample_count", 1), 1) * 100, 1)
                            }
                    insights["weight_adjustments"] = adjustments
        except Exception:
            pass
    
    # Get counterfactual insights
    if COUNTERFACTUAL_RESULTS.exists():
        try:
            with COUNTERFACTUAL_RESULTS.open("r") as f:
                lines = f.readlines()
            
            missed_opps = 0
            avoided_losses = 0
            theoretical_pnl = 0.0
            
            for line in lines[-50:]:  # Last 50 counterfactuals
                try:
                    cf = json.loads(line.strip())
                    outcome = cf.get("theoretical_outcome", {})
                    pnl = outcome.get("theoretical_pnl_usd", 0.0)
                    theoretical_pnl += pnl
                    
                    if pnl > 0:
                        missed_opps += 1
                    else:
                        avoided_losses += 1
                except Exception:
                    continue
            
            insights["counterfactual_insights"] = {
                "missed_opportunities": missed_opps,
                "avoided_losses": avoided_losses,
                "theoretical_pnl": round(theoretical_pnl, 2)
            }
        except Exception:
            pass
    
    return insights


def generate_written_summary(trades: List[Dict[str, Any]], pnl_metrics: Dict[str, Any], 
                             signal_analysis: Dict[str, Any], learning_insights: Dict[str, Any]) -> str:
    """Generate written executive summary."""
    summary_parts = []
    
    # Performance summary
    total_trades = len(trades)
    total_pnl = sum(float(t.get("pnl_usd", 0.0)) for t in trades)
    wins = sum(1 for t in trades if float(t.get("pnl_usd", 0.0)) > 0)
    win_rate = round(wins / total_trades * 100, 1) if total_trades > 0 else 0.0
    
    summary_parts.append(f"## Performance Summary")
    summary_parts.append(f"Total trades executed: {total_trades}")
    summary_parts.append(f"Total P&L: ${total_pnl:,.2f}")
    summary_parts.append(f"Win rate: {win_rate}%")
    summary_parts.append(f"2-day P&L: ${pnl_metrics['pnl_2d']:,.2f} ({pnl_metrics['trades_2d']} trades, {pnl_metrics['win_rate_2d']}% win rate)")
    summary_parts.append(f"5-day P&L: ${pnl_metrics['pnl_5d']:,.2f} ({pnl_metrics['trades_5d']} trades, {pnl_metrics['win_rate_5d']}% win rate)")
    summary_parts.append("")
    
    # Signal performance
    if signal_analysis.get("top_signals"):
        summary_parts.append(f"## Top Performing Signals")
        for signal, data in list(signal_analysis["top_signals"].items())[:3]:
            summary_parts.append(f"- **{signal}**: ${data['total_pnl']:,.2f} total P&L, {data['win_rate']}% win rate ({data['count']} trades)")
        summary_parts.append("")
    
    if signal_analysis.get("bottom_signals"):
        summary_parts.append(f"## Underperforming Signals")
        for signal, data in list(signal_analysis["bottom_signals"].items())[:3]:
            summary_parts.append(f"- **{signal}**: ${data['total_pnl']:,.2f} total P&L, {data['win_rate']}% win rate ({data['count']} trades)")
        summary_parts.append("")
    
    # Learning insights
    if learning_insights.get("weight_adjustments"):
        summary_parts.append(f"## Recent Weight Adjustments")
        for component, adj in list(learning_insights["weight_adjustments"].items())[:5]:
            mult = adj["current_multiplier"]
            direction = "increased" if mult > 1.0 else "decreased"
            summary_parts.append(f"- **{component}**: {direction} to {mult:.2f}x (based on {adj['sample_count']} samples, {adj['win_rate']}% win rate)")
        summary_parts.append("")
    
    if learning_insights.get("counterfactual_insights"):
        cf = learning_insights["counterfactual_insights"]
        summary_parts.append(f"## Counterfactual Analysis")
        summary_parts.append(f"Missed opportunities: {cf.get('missed_opportunities', 0)} trades")
        summary_parts.append(f"Avoided losses: {cf.get('avoided_losses', 0)} trades")
        summary_parts.append(f"Theoretical P&L from blocked trades: ${cf.get('theoretical_pnl', 0.0):,.2f}")
        summary_parts.append("")
    
    if learning_insights.get("daily_learnings"):
        summary_parts.append(f"## Today's Learnings")
        for learning in learning_insights["daily_learnings"][:3]:
            if learning["type"] == "weight_optimization":
                summary_parts.append(f"- Weight optimization identified {len(learning['data'])} signal improvements")
        summary_parts.append("")
    
    if learning_insights.get("weekly_learnings"):
        summary_parts.append(f"## This Week's Learnings")
        for learning in learning_insights["weekly_learnings"][:3]:
            if learning["type"] == "timing_optimization":
                summary_parts.append(f"- Timing optimization: Best scenario is {learning['data'].get('best_scenario', 'N/A')}")
            elif learning["type"] == "sizing_optimization":
                summary_parts.append(f"- Sizing optimization: Best scenario is {learning['data'].get('best_scenario', 'N/A')}")
        summary_parts.append("")
    
    return "\n".join(summary_parts)


def generate_executive_summary() -> Dict[str, Any]:
    """Generate complete executive summary."""
    # Get all trades
    trades = get_all_trades(lookback_days=30)
    
    # Calculate P&L metrics
    pnl_metrics = calculate_pnl_metrics(trades)
    
    # Analyze signal performance
    signal_analysis = analyze_signal_performance(trades)
    
    # Get learning insights
    learning_insights = get_learning_insights()
    
    # Generate written summary
    written_summary = generate_written_summary(trades, pnl_metrics, signal_analysis, learning_insights)
    
    # Format trades for display (last 50)
    formatted_trades = []
    for trade in trades[:50]:
        try:
            context = trade.get("context", {})
            formatted_trades.append({
                "timestamp": trade.get("ts", ""),
                "symbol": trade.get("symbol", ""),
                "pnl_usd": round(float(trade.get("pnl_usd", 0.0)), 2),
                "pnl_pct": round(float(context.get("pnl_pct", 0.0)), 2),
                "hold_minutes": round(float(context.get("hold_minutes", 0.0)), 1),
                "entry_score": round(float(context.get("entry_score", 0.0)), 2),
                "close_reason": context.get("close_reason", "unknown")
            })
        except Exception:
            continue  # Skip malformed trades
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trades": formatted_trades,
        "total_trades": len(trades),
        "pnl_metrics": pnl_metrics,
        "signal_analysis": signal_analysis,
        "learning_insights": learning_insights,
        "written_summary": written_summary
    }


if __name__ == "__main__":
    summary = generate_executive_summary()
    print(json.dumps(summary, indent=2, default=str))
