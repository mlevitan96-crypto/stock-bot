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
# Check both possible locations
ATTRIBUTION_FILE = LOGS_DIR / "attribution.jsonl"
# Fallback: also check if it's in a different location
if not ATTRIBUTION_FILE.exists():
    # Try alternative location
    alt_path = Path("logs/attribution.jsonl")
    if alt_path.exists():
        ATTRIBUTION_FILE = alt_path
COMPREHENSIVE_LEARNING_FILE = DATA_DIR / "comprehensive_learning.jsonl"
COUNTERFACTUAL_RESULTS = DATA_DIR / "counterfactual_results.jsonl"
WEIGHTS_STATE_FILE = STATE_DIR / "signal_weights.json"


def get_all_trades(lookback_days: int = 30) -> List[Dict[str, Any]]:
    """Get all trades from attribution log."""
    trades = []
    
    # Try multiple possible locations
    attribution_files = [
        ATTRIBUTION_FILE,
        Path("logs/attribution.jsonl"),
        Path("data/attribution.jsonl"),
        LOGS_DIR / "attribution.jsonl"
    ]
    
    attribution_file = None
    for path in attribution_files:
        if path.exists():
            attribution_file = path
            break
    
    if not attribution_file:
        return trades
    
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    
    try:
        with attribution_file.open("r") as f:
            lines = f.readlines()
        
        for line in lines:
            try:
                trade = json.loads(line.strip())
                if trade.get("type") != "attribution":
                    continue
                
                # CRITICAL FIX: Only include CLOSED trades (exclude "open_" trade_id entries)
                # Open trades have pnl_usd=0.0 and no close_reason, which pollutes the dashboard
                trade_id = trade.get("trade_id", "")
                if trade_id and trade_id.startswith("open_"):
                    continue  # Skip open trades - only show closed trades
                
                # Also filter trades that have no P&L and no close_reason (likely incomplete)
                context = trade.get("context", {})
                pnl_usd = float(trade.get("pnl_usd", 0.0))
                close_reason = context.get("close_reason", "") or trade.get("close_reason", "")
                if pnl_usd == 0.0 and (not close_reason or close_reason == "unknown" or close_reason == "N/A"):
                    # This looks like an open trade or incomplete record - skip it
                    continue
                
                ts_str = trade.get("ts", "")
                if not ts_str:
                    continue
                
                # Handle both ISO format and timestamp
                try:
                    if isinstance(ts_str, (int, float)):
                        trade_time = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                    else:
                        trade_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if trade_time.tzinfo is None:
                            trade_time = trade_time.replace(tzinfo=timezone.utc)
                except:
                    continue
                
                if trade_time < cutoff_time:
                    continue
                
                trades.append(trade)
            except Exception as e:
                continue
        
        # Sort by timestamp (newest first)
        trades.sort(key=lambda x: x.get("ts", ""), reverse=True)
        
    except Exception as e:
        print(f"Error reading trades from {attribution_file}: {e}")
    
    return trades


def calculate_pnl_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate P&L metrics for different time periods."""
    # Filter out open trades (only count closed trades)
    closed_trades = [
        t for t in trades 
        if not (t.get("trade_id", "").startswith("open_"))
        and (float(t.get("pnl_usd", 0.0)) != 0.0 or t.get("context", {}).get("close_reason"))
    ]
    
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
    # Filter out open trades
    closed_trades = [
        t for t in trades 
        if not (t.get("trade_id", "").startswith("open_"))
        and (float(t.get("pnl_usd", 0.0)) != 0.0 or t.get("context", {}).get("close_reason"))
    ]
    
    signal_pnl = defaultdict(lambda: {"total_pnl": 0.0, "count": 0, "wins": 0, "losses": 0})
    
    for trade in closed_trades:
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
    
    # SHADOW TRACKING ANALYSIS: Analyze missed opportunities from rejected signals
    shadow_analysis = analyze_shadow_performance()
    
    return {
        "top_signals": top_signals,
        "bottom_signals": bottom_signals,
        "all_signals": signal_analysis,
        "shadow_analysis": shadow_analysis
    }

def analyze_shadow_performance() -> Dict[str, Any]:
    """Analyze shadow positions to identify missed profit opportunities."""
    try:
        from shadow_tracker import get_shadow_tracker
        from signal_history_storage import get_signal_history
        
        shadow_tracker = get_shadow_tracker()
        shadow_positions = shadow_tracker.get_all_positions()
        
        # Also get closed shadow positions from signal history
        signals = get_signal_history(limit=200)
        shadow_signals = [s for s in signals if s.get("shadow_created")]
        
        total_missed_profit = 0.0
        total_missed_loss = 0.0
        profitable_rejections = 0
        unprofitable_rejections = 0
        shadow_count = 0
        
        # Analyze active shadow positions
        for symbol, shadow_pos in shadow_positions.items():
            shadow_count += 1
            max_profit = shadow_pos.max_profit_pct
            max_loss = shadow_pos.max_loss_pct
            
            if max_profit > 0:
                total_missed_profit += max_profit
                profitable_rejections += 1
            if max_loss < 0:
                total_missed_loss += max_loss
                unprofitable_rejections += 1
        
        # Analyze closed shadow positions from signal history
        for signal in shadow_signals:
            virtual_pnl = signal.get("virtual_pnl")
            if virtual_pnl is not None:
                shadow_count += 1
                if virtual_pnl > 0:
                    total_missed_profit += virtual_pnl
                    profitable_rejections += 1
                elif virtual_pnl < 0:
                    total_missed_loss += virtual_pnl
                    unprofitable_rejections += 1
        
        # Calculate statistics
        avg_missed_profit = total_missed_profit / profitable_rejections if profitable_rejections > 0 else 0.0
        avg_missed_loss = total_missed_loss / unprofitable_rejections if unprofitable_rejections > 0 else 0.0
        rejection_accuracy = (unprofitable_rejections / shadow_count * 100) if shadow_count > 0 else 0.0
        
        return {
            "total_shadow_positions": shadow_count,
            "profitable_rejections": profitable_rejections,
            "unprofitable_rejections": unprofitable_rejections,
            "total_missed_profit_pct": round(total_missed_profit, 2),
            "total_missed_loss_pct": round(total_missed_loss, 2),
            "avg_missed_profit_pct": round(avg_missed_profit, 2),
            "avg_missed_loss_pct": round(avg_missed_loss, 2),
            "rejection_accuracy_pct": round(rejection_accuracy, 1),
            "net_missed_opportunity_pct": round(total_missed_profit + total_missed_loss, 2)
        }
    except ImportError:
        return {
            "error": "shadow_tracker module not available",
            "total_shadow_positions": 0
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_shadow_positions": 0
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
    # Filter out open trades (only count closed trades)
    closed_trades = [
        t for t in trades 
        if not (t.get("trade_id", "").startswith("open_"))
        and (float(t.get("pnl_usd", 0.0)) != 0.0 or t.get("context", {}).get("close_reason"))
    ]
    
    summary_parts = []
    
    # Performance summary
    total_trades = len(closed_trades)
    total_pnl = sum(float(t.get("pnl_usd", 0.0)) for t in closed_trades)
    wins = sum(1 for t in closed_trades if float(t.get("pnl_usd", 0.0)) > 0)
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
    
    # Format trades for display (last 50 CLOSED trades only)
    # Filter out open trades first
    closed_trades_for_display = [
        t for t in trades 
        if not (t.get("trade_id", "").startswith("open_"))
        and (float(t.get("pnl_usd", 0.0)) != 0.0 or t.get("context", {}).get("close_reason"))
    ]
    
    formatted_trades = []
    for trade in closed_trades_for_display[:50]:
        try:
            context = trade.get("context", {})
            # Extract close_reason - handle both direct and nested
            close_reason = context.get("close_reason", "")
            if not close_reason or close_reason == "unknown":
                # Try to get from trade root level
                close_reason = trade.get("close_reason", "")
            
            # If still no close_reason, check if this is an open trade (should be filtered earlier, but double-check)
            if not close_reason or close_reason == "unknown":
                # Check trade_id to see if it's an open trade
                trade_id = trade.get("trade_id", "")
                if trade_id and trade_id.startswith("open_"):
                    close_reason = "N/A"  # Open trade, hasn't closed yet
            
            # Extract hold_minutes - ensure it's calculated if missing
            hold_minutes = context.get("hold_minutes", 0.0)
            if hold_minutes == 0.0:
                # Try to calculate from timestamps
                try:
                    ts_str = trade.get("ts", "")
                    if ts_str:
                        if isinstance(ts_str, (int, float)):
                            exit_time = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                        else:
                            exit_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            if exit_time.tzinfo is None:
                                exit_time = exit_time.replace(tzinfo=timezone.utc)
                        
                        entry_ts_str = context.get("entry_ts") or metadata.get("entry_ts", "")
                        if entry_ts_str:
                            if isinstance(entry_ts_str, (int, float)):
                                entry_time = datetime.fromtimestamp(entry_ts_str, tz=timezone.utc)
                            else:
                                entry_time = datetime.fromisoformat(str(entry_ts_str).replace("Z", "+00:00"))
                                if entry_time.tzinfo is None:
                                    entry_time = entry_time.replace(tzinfo=timezone.utc)
                            
                            hold_minutes = (exit_time - entry_time).total_seconds() / 60.0
                except:
                    pass
            
            # Extract entry_score - ensure it's captured
            entry_score = context.get("entry_score", 0.0)
            if entry_score == 0.0:
                entry_score = trade.get("entry_score", 0.0)
            
            # Only include trades that have actually closed (have P&L or close_reason)
            # Skip trades that are still open (pnl_usd=0 and no close_reason)
            pnl_usd = round(float(trade.get("pnl_usd", 0.0)), 2)
            has_close_reason = close_reason and close_reason != "unknown" and close_reason != "N/A"
            
            # Include if it has P&L OR has a close reason (indicates it closed)
            if pnl_usd != 0.0 or has_close_reason:
                formatted_trades.append({
                    "timestamp": trade.get("ts", ""),
                    "symbol": trade.get("symbol", ""),
                    "pnl_usd": pnl_usd,
                    "pnl_pct": round(float(context.get("pnl_pct", 0.0)), 2),
                    "hold_minutes": round(float(hold_minutes), 1),
                    "entry_score": round(float(entry_score), 2),
                    "close_reason": close_reason if close_reason and close_reason != "unknown" else "N/A"
                })
        except Exception:
            continue  # Skip malformed trades
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trades": formatted_trades,
        "total_trades": len(closed_trades_for_display),
        "pnl_metrics": pnl_metrics,
        "signal_analysis": signal_analysis,
        "learning_insights": learning_insights,
        "written_summary": written_summary
    }


if __name__ == "__main__":
    summary = generate_executive_summary()
    print(json.dumps(summary, indent=2, default=str))



