#!/usr/bin/env python3
"""
Read investigation results from git and provide analysis.
This allows Cursor to read results without manual copy/paste.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def pull_latest():
    """Pull latest from git to get investigation results"""
    try:
        subprocess.run(["git", "pull", "origin", "main", "--no-rebase"], 
                      check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def read_investigation_results():
    """Read and analyze investigation results"""
    results_file = Path("investigate_no_trades.json")
    
    # Pull latest first
    print("Pulling latest results from git...")
    pull_latest()
    
    if not results_file.exists():
        return None, "No investigation results found. Run trigger_investigation.py first."
    
    try:
        with open(results_file) as f:
            results = json.load(f)
        return results, None
    except Exception as e:
        return None, f"Error reading results: {e}"

def analyze_results(results):
    """Analyze investigation results and provide summary"""
    if not results:
        return "No results to analyze"
    
    summary = []
    summary.append("=" * 80)
    summary.append("INVESTIGATION ANALYSIS: Why No Trades Today")
    summary.append("=" * 80)
    summary.append("")
    
    checks = results.get("checks", {})
    issues = results.get("summary", {}).get("issues", [])
    
    # Market Hours
    market = checks.get("market_hours", {})
    if not market.get("is_market_hours"):
        summary.append(f"⏰ MARKET STATUS: Market is {'closed' if market.get('is_weekend') else 'outside trading hours'}")
        summary.append(f"   Current time: {market.get('current_time', 'unknown')}")
    else:
        summary.append("✅ Market is open")
    summary.append("")
    
    # Services
    services = checks.get("services", {})
    svc_status = services.get("services", {})
    all_running = services.get("all_running", False)
    if not all_running:
        summary.append("❌ SERVICES: Not all services are running")
        for svc, running in svc_status.items():
            status = "✅" if running else "❌"
            summary.append(f"   {status} {svc}: {'Running' if running else 'NOT RUNNING'}")
    else:
        summary.append("✅ All services are running")
    summary.append("")
    
    # Execution Cycles
    cycles = checks.get("execution_cycles", {})
    if "error" in cycles:
        summary.append(f"⚠️  EXECUTION CYCLES: {cycles.get('error')}")
    elif cycles.get("minutes_since_last_cycle", 999) > 10:
        summary.append(f"❌ EXECUTION CYCLES: Last cycle was {cycles.get('minutes_since_last_cycle')} minutes ago")
        summary.append(f"   This means the bot is not executing trading logic")
    else:
        summary.append(f"✅ Execution cycles running (last: {cycles.get('minutes_since_last_cycle', 0)} min ago)")
    summary.append("")
    
    # Positions
    positions = checks.get("positions", {})
    pos_count = positions.get("count", 0)
    max_pos = positions.get("max_positions", 16)
    if pos_count >= max_pos:
        summary.append(f"⚠️  POSITIONS: At maximum ({pos_count}/{max_pos})")
        summary.append("   Bot may be waiting for exits before new entries")
    else:
        summary.append(f"✅ Positions: {pos_count}/{max_pos} (room for more)")
    summary.append("")
    
    # Blocked Trades
    blocks = checks.get("blocked_trades", {})
    block_count = blocks.get("recent_blocks_count", 0)
    if block_count > 0:
        summary.append(f"⚠️  BLOCKED TRADES: {block_count} trades blocked recently")
        reasons = blocks.get("reasons", {})
        if reasons:
            summary.append("   Block reasons:")
            for reason, count in reasons.items():
                summary.append(f"     - {reason}: {count} times")
    else:
        summary.append("✅ No recent blocked trades")
    summary.append("")
    
    # Signals
    signals = checks.get("signals", {})
    tickers_with_trades = signals.get("tickers_with_trades", 0)
    tickers_with_clusters = signals.get("tickers_with_clusters", 0)
    if tickers_with_trades == 0:
        summary.append("❌ SIGNALS: No tickers have flow trades in cache")
        summary.append("   This means UW daemon may not be fetching data")
    elif tickers_with_clusters == 0:
        summary.append("⚠️  SIGNALS: Trades in cache but no clusters generated")
        summary.append("   Bot may not be processing signals")
    else:
        summary.append(f"✅ Signals: {tickers_with_trades} tickers with trades, {tickers_with_clusters} with clusters")
    summary.append("")
    
    # Orders
    orders = checks.get("orders", {})
    today_orders = orders.get("today_orders_count", 0)
    if today_orders == 0:
        summary.append("❌ ORDERS: No orders submitted today")
    else:
        summary.append(f"✅ Orders: {today_orders} submitted today")
    summary.append("")
    
    # UW Daemon
    daemon = checks.get("uw_daemon", {})
    cache_age = daemon.get("cache_age_minutes", 0)
    if cache_age > 60:
        summary.append(f"⚠️  UW DAEMON: Cache is {cache_age} minutes old")
        summary.append("   Daemon may not be running or updating")
    else:
        summary.append(f"✅ UW Daemon: Cache is fresh ({cache_age} min old)")
    summary.append("")
    
    # Summary of issues
    if issues:
        summary.append("=" * 80)
        summary.append("ISSUES FOUND:")
        summary.append("=" * 80)
        for issue in issues:
            summary.append(f"  {issue}")
    else:
        summary.append("=" * 80)
        summary.append("NO OBVIOUS ISSUES FOUND")
        summary.append("=" * 80)
        summary.append("Further investigation may be needed")
    
    summary.append("")
    summary.append("=" * 80)
    
    return "\n".join(summary)

def main():
    """Main function"""
    results, error = read_investigation_results()
    
    if error:
        print(error)
        return 1
    
    if not results:
        print("No investigation results found.")
        print("Run: python trigger_investigation.py")
        return 1
    
    analysis = analyze_results(results)
    print(analysis)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

