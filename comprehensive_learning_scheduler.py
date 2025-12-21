#!/usr/bin/env python3
"""
Comprehensive Learning Scheduler - Multi-Timeframe Learning Automation

Implements automated learning cycles for:
- Daily: After market close (already implemented)
- Weekly: Every Friday after market close
- Bi-Weekly: Every other Friday after market close
- Monthly: First trading day of month after market close

All cycles focus on long-term profitability improvement.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from comprehensive_learning_orchestrator_v2 import (
    run_comprehensive_learning,
    run_historical_backfill
)
from profitability_tracker import (
    update_daily_performance,
    update_weekly_performance,
    update_monthly_performance,
    get_performance_trends
)

STATE_DIR = Path("state")
SCHEDULER_STATE_FILE = STATE_DIR / "learning_scheduler_state.json"

def load_scheduler_state() -> Dict:
    """Load scheduler state"""
    if SCHEDULER_STATE_FILE.exists():
        try:
            with open(SCHEDULER_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "last_daily_run": None,
        "last_weekly_run": None,
        "last_biweekly_run": None,
        "last_monthly_run": None,
        "last_biweekly_week": None  # Track which week (odd/even)
    }

def save_scheduler_state(state: Dict):
    """Save scheduler state"""
    SCHEDULER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULER_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

def is_after_market_close() -> bool:
    """Check if market is closed (after 4:00 PM ET / 9:00 PM UTC)"""
    now = datetime.now(timezone.utc)
    # Market closes at 4:00 PM ET = 9:00 PM UTC (or 8:00 PM UTC during DST)
    # Use 8:00 PM UTC as safe threshold (20:00)
    return now.hour >= 20

def is_friday() -> bool:
    """Check if today is Friday"""
    return datetime.now(timezone.utc).weekday() == 4  # Monday=0, Friday=4

def is_first_trading_day_of_month() -> bool:
    """Check if today is first trading day of month"""
    now = datetime.now(timezone.utc)
    # First trading day is usually 1st, 2nd, or 3rd (if 1st is weekend)
    return now.day <= 3

def get_week_number() -> int:
    """Get ISO week number (1-53)"""
    return datetime.now(timezone.utc).isocalendar()[1]

def is_odd_week() -> bool:
    """Check if current week is odd (for bi-weekly)"""
    return get_week_number() % 2 == 1

def run_weekly_learning_cycle() -> Dict[str, Any]:
    """
    Run comprehensive weekly learning cycle.
    
    Focus: Weekly pattern analysis, trend detection, weight optimization.
    """
    try:
        from main import log_event
        log_event("learning_scheduler", "weekly_cycle_started")
    except:
        pass
    
    results = {
        "cycle_type": "weekly",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "learning_results": {},
        "profitability_results": {},
        "trends": {}
    }
    
    # 1. Run comprehensive learning (processes all new data)
    try:
        learning_results = run_comprehensive_learning(process_all_historical=False)
        results["learning_results"] = learning_results
    except Exception as e:
        results["learning_error"] = str(e)
    
    # 2. Update weekly profitability tracking
    try:
        update_weekly_performance()
        results["profitability_updated"] = True
    except Exception as e:
        results["profitability_error"] = str(e)
    
    # 3. Get performance trends
    try:
        trends = get_performance_trends()
        results["trends"] = trends
    except Exception as e:
        results["trends_error"] = str(e)
    
    # 4. Log results
    try:
        from main import log_event
        log_event("learning_scheduler", "weekly_cycle_complete",
                 trades_processed=results.get("learning_results", {}).get("attribution", 0),
                 weights_updated=results.get("learning_results", {}).get("weights_updated", 0),
                 trends=results.get("trends", {}))
    except:
        pass
    
    return results

def run_biweekly_learning_cycle() -> Dict[str, Any]:
    """
    Run comprehensive bi-weekly learning cycle.
    
    Focus: Deeper pattern analysis, regime detection, structural changes.
    """
    try:
        from main import log_event
        log_event("learning_scheduler", "biweekly_cycle_started")
    except:
        pass
    
    results = {
        "cycle_type": "biweekly",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "learning_results": {},
        "profitability_results": {},
        "trends": {},
        "regime_analysis": {}
    }
    
    # 1. Run comprehensive learning (processes all new data)
    try:
        learning_results = run_comprehensive_learning(process_all_historical=False)
        results["learning_results"] = learning_results
    except Exception as e:
        results["learning_error"] = str(e)
    
    # 2. Update weekly profitability tracking
    try:
        update_weekly_performance()
        results["profitability_updated"] = True
    except Exception as e:
        results["profitability_error"] = str(e)
    
    # 3. Get performance trends (deeper analysis)
    try:
        trends = get_performance_trends()
        results["trends"] = trends
        
        # Bi-weekly specific: Analyze regime changes
        # Check if performance shifted significantly
        recent_win_rate = trends.get("recent_win_rate", 0.5)
        older_win_rate = trends.get("older_win_rate", 0.5)
        win_rate_change = recent_win_rate - older_win_rate
        
        results["regime_analysis"] = {
            "win_rate_change": round(win_rate_change, 3),
            "regime_shift": "improving" if win_rate_change > 0.05 else "declining" if win_rate_change < -0.05 else "stable"
        }
    except Exception as e:
        results["trends_error"] = str(e)
    
    # 4. Log results
    try:
        from main import log_event
        log_event("learning_scheduler", "biweekly_cycle_complete",
                 trades_processed=results.get("learning_results", {}).get("attribution", 0),
                 weights_updated=results.get("learning_results", {}).get("weights_updated", 0),
                 regime_shift=results.get("regime_analysis", {}).get("regime_shift", "unknown"))
    except:
        pass
    
    return results

def run_monthly_learning_cycle() -> Dict[str, Any]:
    """
    Run comprehensive monthly learning cycle.
    
    Focus: Long-term profitability, structural optimization, major adjustments.
    """
    try:
        from main import log_event
        log_event("learning_scheduler", "monthly_cycle_started")
    except:
        pass
    
    results = {
        "cycle_type": "monthly",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "learning_results": {},
        "profitability_results": {},
        "trends": {},
        "long_term_analysis": {}
    }
    
    # 1. Run comprehensive learning (processes all new data)
    try:
        learning_results = run_comprehensive_learning(process_all_historical=False)
        results["learning_results"] = learning_results
    except Exception as e:
        results["learning_error"] = str(e)
    
    # 2. Update monthly profitability tracking
    try:
        update_monthly_performance()
        results["profitability_updated"] = True
    except Exception as e:
        results["profitability_error"] = str(e)
    
    # 3. Get performance trends (long-term analysis)
    try:
        trends = get_performance_trends()
        results["trends"] = trends
        
        # Monthly specific: Long-term profitability analysis
        monthly_data = trends.get("monthly", {})
        win_rate = monthly_data.get("win_rate", 0.5)
        total_pnl_pct = monthly_data.get("total_pnl_pct", 0.0)
        expectancy = monthly_data.get("expectancy", 0.0)
        
        results["long_term_analysis"] = {
            "monthly_win_rate": round(win_rate, 3),
            "monthly_pnl_pct": round(total_pnl_pct, 3),
            "monthly_expectancy": round(expectancy, 4),
            "profitability_status": "profitable" if total_pnl_pct > 0 and win_rate > 0.5 else "needs_improvement",
            "on_track_for_goal": win_rate >= 0.6  # 60% win rate goal
        }
    except Exception as e:
        results["trends_error"] = str(e)
    
    # 4. Log results
    try:
        from main import log_event
        log_event("learning_scheduler", "monthly_cycle_complete",
                 trades_processed=results.get("learning_results", {}).get("attribution", 0),
                 weights_updated=results.get("learning_results", {}).get("weights_updated", 0),
                 monthly_win_rate=results.get("long_term_analysis", {}).get("monthly_win_rate", 0),
                 profitability_status=results.get("long_term_analysis", {}).get("profitability_status", "unknown"))
    except:
        pass
    
    return results

def check_and_run_scheduled_cycles():
    """
    Check if any scheduled cycles should run and execute them.
    
    This is called periodically (e.g., every hour) to check for scheduled runs.
    """
    state = load_scheduler_state()
    now = datetime.now(timezone.utc)
    today = now.date()
    
    # Check if market is closed
    if not is_after_market_close():
        return None
    
    results = {}
    
    # DAILY: Already handled by main.py's daily_and_weekly_tasks_if_needed()
    # But we can track it here too
    last_daily = state.get("last_daily_run")
    if last_daily != str(today):
        # Daily cycle runs in main.py, just track here
        state["last_daily_run"] = str(today)
        save_scheduler_state(state)
    
    # WEEKLY: Every Friday after market close
    if is_friday():
        last_weekly = state.get("last_weekly_run")
        if last_weekly != str(today):
            results["weekly"] = run_weekly_learning_cycle()
            state["last_weekly_run"] = str(today)
            save_scheduler_state(state)
    
    # BI-WEEKLY: Every other Friday (odd weeks)
    if is_friday() and is_odd_week():
        last_biweekly = state.get("last_biweekly_run")
        last_biweekly_week = state.get("last_biweekly_week")
        current_week = get_week_number()
        
        if last_biweekly != str(today) and last_biweekly_week != current_week:
            results["biweekly"] = run_biweekly_learning_cycle()
            state["last_biweekly_run"] = str(today)
            state["last_biweekly_week"] = current_week
            save_scheduler_state(state)
    
    # MONTHLY: First trading day of month after market close
    if is_first_trading_day_of_month():
        last_monthly = state.get("last_monthly_run")
        current_month = now.strftime("%Y-%m")
        
        if last_monthly != current_month:
            results["monthly"] = run_monthly_learning_cycle()
            state["last_monthly_run"] = current_month
            save_scheduler_state(state)
    
    return results if results else None

if __name__ == "__main__":
    # Manual trigger for testing
    print("=" * 80)
    print("COMPREHENSIVE LEARNING SCHEDULER - MANUAL TRIGGER")
    print("=" * 80)
    print()
    
    results = check_and_run_scheduled_cycles()
    
    if results:
        print("Scheduled cycles executed:")
        for cycle_type, result in results.items():
            print(f"  {cycle_type}: {result.get('timestamp', 'unknown')}")
    else:
        print("No scheduled cycles to run at this time.")
        print()
        print("Current status:")
        state = load_scheduler_state()
        print(f"  Last daily run: {state.get('last_daily_run', 'never')}")
        print(f"  Last weekly run: {state.get('last_weekly_run', 'never')}")
        print(f"  Last biweekly run: {state.get('last_biweekly_run', 'never')}")
        print(f"  Last monthly run: {state.get('last_monthly_run', 'never')}")
