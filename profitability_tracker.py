#!/usr/bin/env python3
"""
Profitability Tracker - Track performance improvements over time

Tracks:
- Daily/Weekly/Monthly win rates
- P&L trends
- Component performance improvements
- Learning effectiveness (are we getting better?)
- Goal: Make every trade a winner
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

LOG_DIR = Path("logs")
DATA_DIR = Path("data")
STATE_DIR = Path("state")
PERFORMANCE_TRACK_FILE = STATE_DIR / "profitability_tracking.json"

def load_performance_tracking() -> Dict:
    """Load historical performance tracking"""
    if PERFORMANCE_TRACK_FILE.exists():
        try:
            with open(PERFORMANCE_TRACK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "daily": {},
        "weekly": {},
        "monthly": {},
        "component_trends": {},
        "last_update": None
    }

def save_performance_tracking(data: Dict):
    """Save performance tracking data"""
    PERFORMANCE_TRACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PERFORMANCE_TRACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def analyze_trades_period(start_date: datetime, end_date: datetime) -> Dict:
    """Analyze trades in a given time period"""
    attr_log = LOG_DIR / "attribution.jsonl"
    if not attr_log.exists():
        return {"trades": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "total_pnl_usd": 0.0, "total_pnl_pct": 0.0, "avg_pnl_pct": 0.0}
    
    trades = []
    wins = 0
    losses = 0
    total_pnl_usd = 0.0
    total_pnl_pct = 0.0
    
    with open(attr_log, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                if rec.get("type") != "attribution":
                    continue
                
                ts_str = rec.get("ts", "")
                if not ts_str:
                    continue
                
                # Parse timestamp
                try:
                    if 'T' in ts_str:
                        rec_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    else:
                        rec_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                        rec_dt = rec_dt.replace(tzinfo=timezone.utc)
                except:
                    continue
                
                if start_date <= rec_dt <= end_date:
                    pnl_usd = float(rec.get("pnl_usd", 0))
                    pnl_pct = float(rec.get("pnl_pct", 0))
                    
                    trades.append({
                        "symbol": rec.get("symbol"),
                        "pnl_usd": pnl_usd,
                        "pnl_pct": pnl_pct,
                        "ts": ts_str
                    })
                    
                    if pnl_usd > 0:
                        wins += 1
                    elif pnl_usd < 0:
                        losses += 1
                    
                    total_pnl_usd += pnl_usd
                    total_pnl_pct += pnl_pct
            except:
                continue
    
    total_trades = len(trades)
    win_rate = (wins / total_trades) if total_trades > 0 else 0.0
    avg_pnl_pct = (total_pnl_pct / total_trades) if total_trades > 0 else 0.0
    
    return {
        "trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 4),
        "total_pnl_usd": round(total_pnl_usd, 2),
        "total_pnl_pct": round(total_pnl_pct, 4),
        "avg_pnl_pct": round(avg_pnl_pct, 4),
        "expectancy": round(avg_pnl_pct * win_rate - abs(avg_pnl_pct) * (1 - win_rate), 4)
    }

def update_daily_performance():
    """Update daily performance metrics"""
    tracking = load_performance_tracking()
    
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    daily_stats = analyze_trades_period(today_start, today_end)
    daily_stats["date"] = str(today)
    daily_stats["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    tracking["daily"][str(today)] = daily_stats
    tracking["last_update"] = datetime.now(timezone.utc).isoformat()
    
    save_performance_tracking(tracking)
    return daily_stats

def update_weekly_performance():
    """Update weekly performance metrics"""
    tracking = load_performance_tracking()
    
    today = datetime.now(timezone.utc).date()
    # Get Monday of this week
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    week_start_dt = datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc)
    week_end_dt = datetime.combine(week_end, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    weekly_stats = analyze_trades_period(week_start_dt, week_end_dt)
    weekly_stats["week_start"] = str(week_start)
    weekly_stats["week_end"] = str(week_end)
    weekly_stats["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    week_key = f"{week_start}"
    tracking["weekly"][week_key] = weekly_stats
    tracking["last_update"] = datetime.now(timezone.utc).isoformat()
    
    save_performance_tracking(tracking)
    return weekly_stats

def update_monthly_performance():
    """Update monthly performance metrics"""
    tracking = load_performance_tracking()
    
    today = datetime.now(timezone.utc).date()
    month_start = today.replace(day=1)
    # Get last day of month
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
    
    month_start_dt = datetime.combine(month_start, datetime.min.time()).replace(tzinfo=timezone.utc)
    month_end_dt = datetime.combine(month_end, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    monthly_stats = analyze_trades_period(month_start_dt, month_end_dt)
    monthly_stats["month"] = f"{month_start.year}-{month_start.month:02d}"
    monthly_stats["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    month_key = f"{month_start.year}-{month_start.month:02d}"
    tracking["monthly"][month_key] = monthly_stats
    tracking["last_update"] = datetime.now(timezone.utc).isoformat()
    
    save_performance_tracking(tracking)
    return monthly_stats

def get_performance_trends(days: int = 30) -> Dict:
    """Get performance trends over the last N days"""
    tracking = load_performance_tracking()
    
    cutoff_date = datetime.now(timezone.utc).date() - timedelta(days=days)
    
    daily_data = []
    for date_str, stats in sorted(tracking["daily"].items()):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if date_obj >= cutoff_date:
                daily_data.append({
                    "date": date_str,
                    "win_rate": stats.get("win_rate", 0.0),
                    "total_pnl_usd": stats.get("total_pnl_usd", 0.0),
                    "total_pnl_pct": stats.get("total_pnl_pct", 0.0),
                    "trades": stats.get("trades", 0),
                    "expectancy": stats.get("expectancy", 0.0)
                })
        except:
            continue
    
    if not daily_data:
        return {"trend": "insufficient_data", "days": 0}
    
    # Calculate trends
    recent_win_rate = sum(d["win_rate"] for d in daily_data[-7:]) / len(daily_data[-7:]) if len(daily_data) >= 7 else 0.0
    older_win_rate = sum(d["win_rate"] for d in daily_data[:-7]) / len(daily_data[:-7]) if len(daily_data) > 7 else recent_win_rate
    
    recent_pnl = sum(d["total_pnl_pct"] for d in daily_data[-7:])
    older_pnl = sum(d["total_pnl_pct"] for d in daily_data[:-7]) if len(daily_data) > 7 else recent_pnl
    
    win_rate_improving = recent_win_rate > older_win_rate
    pnl_improving = recent_pnl > older_pnl
    
    return {
        "days_analyzed": len(daily_data),
        "recent_7d_win_rate": round(recent_win_rate, 4),
        "older_win_rate": round(older_win_rate, 4),
        "win_rate_improving": win_rate_improving,
        "win_rate_change": round(recent_win_rate - older_win_rate, 4),
        "recent_7d_pnl_pct": round(recent_pnl, 4),
        "older_pnl_pct": round(older_pnl, 4),
        "pnl_improving": pnl_improving,
        "pnl_change": round(recent_pnl - older_pnl, 4),
        "trend": "improving" if (win_rate_improving and pnl_improving) else "declining" if (not win_rate_improving and not pnl_improving) else "mixed"
    }

def generate_profitability_report() -> Dict:
    """Generate comprehensive profitability report"""
    tracking = load_performance_tracking()
    
    # Update all metrics
    daily = update_daily_performance()
    weekly = update_weekly_performance()
    monthly = update_monthly_performance()
    trends = get_performance_trends(30)
    
    # Get component performance from learning system
    component_perf = {}
    try:
        from adaptive_signal_optimizer import get_optimizer
        optimizer = get_optimizer()
        if optimizer and hasattr(optimizer, 'learning_orchestrator'):
            lo = optimizer.learning_orchestrator
            if hasattr(lo, 'component_performance'):
                for comp, perf in lo.component_performance.items():
                    wins = perf.get("wins", 0)
                    losses = perf.get("losses", 0)
                    total = wins + losses
                    if total > 0:
                        component_perf[comp] = {
                            "win_rate": round(wins / total, 4),
                            "total_trades": total,
                            "ewma_win_rate": round(perf.get("ewma_win_rate", 0.0), 4),
                            "ewma_pnl": round(perf.get("ewma_pnl", 0.0), 4)
                        }
    except:
        pass
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "trends_30d": trends,
        "component_performance": component_perf,
        "goal_status": {
            "target_win_rate": 0.60,  # 60% win rate target
            "current_daily_win_rate": daily.get("win_rate", 0.0),
            "on_track": daily.get("win_rate", 0.0) >= 0.60,
            "needs_improvement": daily.get("win_rate", 0.0) < 0.50
        }
    }
    
    return report

def print_profitability_report():
    """Print formatted profitability report"""
    report = generate_profitability_report()
    
    print("=" * 80)
    print("PROFITABILITY TRACKING REPORT")
    print("=" * 80)
    print()
    
    print("DAILY PERFORMANCE (Today)")
    print("-" * 80)
    daily = report["daily"]
    print(f"  Trades: {daily.get('trades', 0)}")
    print(f"  Wins: {daily.get('wins', 0)} | Losses: {daily.get('losses', 0)}")
    print(f"  Win Rate: {daily.get('win_rate', 0.0):.2%}")
    print(f"  Total P&L: ${daily.get('total_pnl_usd', 0.0):.2f} ({daily.get('total_pnl_pct', 0.0):.2f}%)")
    print(f"  Avg P&L per Trade: {daily.get('avg_pnl_pct', 0.0):.2f}%")
    print(f"  Expectancy: {daily.get('expectancy', 0.0):.4f}")
    print()
    
    print("WEEKLY PERFORMANCE (This Week)")
    print("-" * 80)
    weekly = report["weekly"]
    print(f"  Trades: {weekly.get('trades', 0)}")
    print(f"  Win Rate: {weekly.get('win_rate', 0.0):.2%}")
    print(f"  Total P&L: ${weekly.get('total_pnl_usd', 0.0):.2f} ({weekly.get('total_pnl_pct', 0.0):.2f}%)")
    print()
    
    print("MONTHLY PERFORMANCE (This Month)")
    print("-" * 80)
    monthly = report["monthly"]
    print(f"  Trades: {monthly.get('trades', 0)}")
    print(f"  Win Rate: {monthly.get('win_rate', 0.0):.2%}")
    print(f"  Total P&L: ${monthly.get('total_pnl_usd', 0.0):.2f} ({monthly.get('total_pnl_pct', 0.0):.2f}%)")
    print()
    
    print("30-DAY TRENDS")
    print("-" * 80)
    trends = report["trends_30d"]
    if trends.get("trend") == "insufficient_data":
        print("  Insufficient data for trend analysis")
    else:
        print(f"  Recent 7d Win Rate: {trends.get('recent_7d_win_rate', 0.0):.2%}")
        print(f"  Older Win Rate: {trends.get('older_win_rate', 0.0):.2%}")
        print(f"  Win Rate Change: {trends.get('win_rate_change', 0.0):+.4f} ({'↑' if trends.get('win_rate_improving') else '↓'})")
        print(f"  Recent 7d P&L: {trends.get('recent_7d_pnl_pct', 0.0):.2f}%")
        print(f"  Older P&L: {trends.get('older_pnl_pct', 0.0):.2f}%")
        print(f"  P&L Change: {trends.get('pnl_change', 0.0):+.4f}% ({'↑' if trends.get('pnl_improving') else '↓'})")
        print(f"  Overall Trend: {trends.get('trend', 'unknown').upper()}")
    print()
    
    print("GOAL STATUS")
    print("-" * 80)
    goal = report["goal_status"]
    print(f"  Target Win Rate: {goal.get('target_win_rate', 0.0):.0%}")
    print(f"  Current Win Rate: {goal.get('current_daily_win_rate', 0.0):.2%}")
    print(f"  On Track: {'✅ YES' if goal.get('on_track') else '❌ NO'}")
    if goal.get('needs_improvement'):
        print(f"  ⚠️  NEEDS IMPROVEMENT - Win rate below 50%")
    print()
    
    if report.get("component_performance"):
        print("TOP COMPONENTS BY PERFORMANCE")
        print("-" * 80)
        comps = sorted(report["component_performance"].items(), 
                      key=lambda x: x[1].get("ewma_win_rate", 0.0), reverse=True)
        for comp, perf in comps[:10]:
            print(f"  {comp:20s} WR: {perf.get('ewma_win_rate', 0.0):.2%} | Trades: {perf.get('total_trades', 0)}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    print_profitability_report()
