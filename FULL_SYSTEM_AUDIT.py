#!/usr/bin/env python3
"""
Full System Audit - Comprehensive Health Check
Checks all aspects of the trading bot to ensure everything is working.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

DATA_DIR = Path("data")
LOGS_DIR = Path("logs")
STATE_DIR = Path("state")

def audit_system():
    """Run comprehensive system audit."""
    print("=" * 80)
    print("FULL SYSTEM AUDIT")
    print("=" * 80)
    print()
    
    issues = []
    warnings = []
    
    # 1. Check if bot process is running
    print("1. PROCESS STATUS")
    print("-" * 80)
    import subprocess
    result = subprocess.run(["pgrep", "-f", "main.py"], capture_output=True, text=True)
    if result.returncode == 0:
        pids = result.stdout.strip().split("\n")
        print(f"✅ Bot process running (PIDs: {', '.join(pids)})")
    else:
        issues.append("Bot process not running")
        print("❌ Bot process NOT running")
    print()
    
    # 2. Check cache freshness
    print("2. CACHE FRESHNESS")
    print("-" * 80)
    cache_file = DATA_DIR / "uw_flow_cache.json"
    if cache_file.exists():
        cache_age = time.time() - cache_file.stat().st_mtime
        cache_age_min = cache_age / 60
        if cache_age < 300:
            print(f"✅ Cache fresh ({cache_age_min:.1f} minutes old)")
        elif cache_age < 600:
            warnings.append(f"Cache moderately stale ({cache_age_min:.1f} minutes)")
            print(f"⚠️  Cache moderately stale ({cache_age_min:.1f} minutes old)")
        else:
            issues.append(f"Cache stale ({cache_age_min:.1f} minutes)")
            print(f"❌ Cache stale ({cache_age_min:.1f} minutes old)")
    else:
        issues.append("Cache file does not exist")
        print("❌ Cache file does not exist")
    print()
    
    # 3. Check recent orders
    print("3. ORDER ACTIVITY")
    print("-" * 80)
    orders_file = DATA_DIR / "live_orders.jsonl"
    if orders_file.exists():
        now = time.time()
        cutoff_1h = now - 3600
        cutoff_3h = now - 10800
        
        orders_1h = []
        orders_3h = []
        
        for line in orders_file.read_text().splitlines()[-100:]:
            try:
                event = json.loads(line.strip())
                event_ts = event.get("_ts", 0)
                if event_ts > cutoff_1h:
                    orders_1h.append(event)
                if event_ts > cutoff_3h:
                    orders_3h.append(event)
            except:
                pass
        
        print(f"Orders in last hour: {len(orders_1h)}")
        print(f"Orders in last 3 hours: {len(orders_3h)}")
        
        if len(orders_1h) == 0:
            warnings.append("No orders in last hour")
            print("⚠️  No orders in last hour")
        if len(orders_3h) == 0:
            issues.append("No orders in last 3 hours")
            print("❌ No orders in last 3 hours")
        
        # Check last order
        if orders_3h:
            last_order = max(orders_3h, key=lambda x: x.get("_ts", 0))
            last_order_age = (now - last_order.get("_ts", 0)) / 3600
            print(f"Last order: {last_order_age:.1f} hours ago")
            print(f"  Type: {last_order.get('event', 'unknown')}")
            print(f"  Symbol: {last_order.get('symbol', 'unknown')}")
    else:
        issues.append("Orders file does not exist")
        print("❌ Orders file does not exist")
    print()
    
    # 4. Check current positions
    print("4. CURRENT POSITIONS")
    print("-" * 80)
    try:
        import alpaca_trade_api as tradeapi
        key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
        secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if key and secret:
            api = tradeapi.REST(key, secret, base_url)
            positions = api.list_positions()
            print(f"Open positions: {len(positions)}")
            
            if len(positions) >= 16:
                warnings.append(f"At max positions ({len(positions)}) - may block new trades")
                print(f"⚠️  At max positions ({len(positions)}) - may block new trades")
            
            for pos in positions[:5]:  # Show first 5
                symbol = getattr(pos, "symbol", "")
                qty = int(float(getattr(pos, "qty", 0)))
                entry = float(getattr(pos, "avg_entry_price", 0))
                current = float(getattr(pos, "current_price", entry))
                pnl = float(getattr(pos, "unrealized_pl", 0))
                print(f"  {symbol}: {qty} @ ${entry:.2f} (current: ${current:.2f}, P&L: ${pnl:.2f})")
        else:
            warnings.append("Alpaca credentials not available for position check")
            print("⚠️  Alpaca credentials not available")
    except Exception as e:
        warnings.append(f"Could not check positions: {e}")
        print(f"⚠️  Could not check positions: {e}")
    print()
    
    # 5. Check recent clusters/signals
    print("5. SIGNAL GENERATION")
    print("-" * 80)
    signals_file = LOGS_DIR / "signals.jsonl"
    if signals_file.exists():
        now = time.time()
        cutoff_1h = now - 3600
        
        signals_1h = []
        for line in signals_file.read_text().splitlines()[-100:]:
            try:
                event = json.loads(line.strip())
                if event.get("_ts", 0) > cutoff_1h:
                    signals_1h.append(event)
            except:
                pass
        
        print(f"Signals generated in last hour: {len(signals_1h)}")
        if len(signals_1h) == 0:
            warnings.append("No signals generated in last hour")
            print("⚠️  No signals generated in last hour")
    else:
        warnings.append("Signals file does not exist")
        print("⚠️  Signals file does not exist")
    print()
    
    # 6. Check run logs
    print("6. BOT EXECUTION CYCLES")
    print("-" * 80)
    run_file = LOGS_DIR / "run.jsonl"
    if run_file.exists():
        now = time.time()
        cutoff_1h = now - 3600
        
        runs_1h = []
        for line in run_file.read_text().splitlines()[-20:]:
            try:
                event = json.loads(line.strip())
                if event.get("_ts", 0) > cutoff_1h:
                    runs_1h.append(event)
            except:
                pass
        
        print(f"Execution cycles in last hour: {len(runs_1h)}")
        if runs_1h:
            last_run = runs_1h[-1]
            clusters = last_run.get("clusters", 0)
            orders = last_run.get("orders", 0)
            print(f"Last cycle: {clusters} clusters, {orders} orders")
            if clusters > 0 and orders == 0:
                warnings.append(f"{clusters} clusters generated but 0 orders placed")
                print(f"⚠️  {clusters} clusters generated but 0 orders placed")
    else:
        warnings.append("Run log file does not exist")
        print("⚠️  Run log file does not exist")
    print()
    
    # 7. Check blocked trades
    print("7. BLOCKED TRADES")
    print("-" * 80)
    blocked_file = STATE_DIR / "blocked_trades.jsonl"
    if blocked_file.exists():
        now = time.time()
        cutoff_1h = now - 3600
        
        blocked_1h = []
        reasons = {}
        for line in blocked_file.read_text().splitlines()[-50:]:
            try:
                event = json.loads(line.strip())
                if event.get("_ts", 0) > cutoff_1h:
                    blocked_1h.append(event)
                    reason = event.get("reason", "unknown")
                    reasons[reason] = reasons.get(reason, 0) + 1
            except:
                pass
        
        print(f"Trades blocked in last hour: {len(blocked_1h)}")
        if reasons:
            print("Block reasons:")
            for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"  {reason}: {count}")
                if reason == "max_positions_reached":
                    issues.append(f"{count} trades blocked by max positions")
                elif reason.startswith("expectancy_blocked"):
                    warnings.append(f"{count} trades blocked by expectancy gate")
    else:
        print("No blocked trades file (may be normal)")
    print()
    
    # 8. Check risk management
    print("8. RISK MANAGEMENT")
    print("-" * 80)
    freeze_file = DATA_DIR / "governor_freezes.json"
    if freeze_file.exists():
        try:
            freezes = json.loads(freeze_file.read_text())
            if freezes:
                print("Active freezes:")
                for freeze_type, freeze_data in freezes.items():
                    print(f"  {freeze_type}: {freeze_data}")
                    issues.append(f"Risk freeze active: {freeze_type}")
            else:
                print("✅ No active risk freezes")
        except:
            print("⚠️  Could not read freeze file")
    else:
        print("✅ No freeze file (no freezes)")
    print()
    
    # 9. Check market status
    print("9. MARKET STATUS")
    print("-" * 80)
    try:
        from sre_monitoring import SREMonitoringEngine
        engine = SREMonitoringEngine()
        market_open, market_status = engine.is_market_open()
        print(f"Market: {market_status}")
        if not market_open:
            warnings.append(f"Market closed: {market_status}")
            print(f"⚠️  Market is closed ({market_status})")
        else:
            print("✅ Market is open")
    except Exception as e:
        warnings.append(f"Could not check market status: {e}")
        print(f"⚠️  Could not check market status: {e}")
    print()
    
    # Summary
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    
    if issues:
        print(f"\n❌ CRITICAL ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not issues and not warnings:
        print("\n✅ All systems operational")
    
    print()
    return {"issues": issues, "warnings": warnings}

if __name__ == "__main__":
    audit_system()
