#!/usr/bin/env python3
"""
API-based Trade and System Health Checker
Queries the running system via HTTP endpoints to check trade activity and health.
"""

import json
import time
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
try:
    import requests
except ImportError:
    print("ERROR: requests module not installed. Install with: pip install requests")
    sys.exit(1)

def format_time_ago(seconds: float) -> str:
    """Format seconds into human-readable time ago."""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        mins = int((seconds % 3600) / 60)
        return f"{hours} hours {mins} minutes"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days} days {hours} hours"

def check_endpoint(base_url: str, endpoint: str, description: str) -> Optional[Dict[str, Any]]:
    """Check an API endpoint."""
    try:
        url = f"{base_url}{endpoint}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  [ERROR] {description}: HTTP {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"  [ERROR] {description}: Connection refused (service may not be running)")
        return None
    except requests.exceptions.Timeout:
        print(f"  [ERROR] {description}: Request timeout")
        return None
    except Exception as e:
        print(f"  [ERROR] {description}: {str(e)}")
        return None

def check_health_endpoint(base_url: str) -> Dict[str, Any]:
    """Check the /health endpoint."""
    print("\n" + "=" * 80)
    print("CHECKING: Health Endpoint")
    print("=" * 80)
    
    data = check_endpoint(base_url, "/health", "Health endpoint")
    if not data:
        return {"status": "error", "message": "Could not connect to health endpoint"}
    
    print(f"Status: {data.get('status', 'unknown')}")
    
    if "last_heartbeat_age_sec" in data:
        age = data["last_heartbeat_age_sec"]
        print(f"Last Heartbeat (Doctor): {format_time_ago(age)} ago")
        if age > 300:
            print(f"  [WARNING] Heartbeat is stale (>5 minutes)")
        elif age > 1800:
            print(f"  [CRITICAL] Heartbeat is very stale (>30 minutes)")
    
    if "health_checks" in data:
        hc = data["health_checks"]
        print(f"Overall Health: {'[OK]' if hc.get('overall_healthy') else '[ISSUES]'}")
        checks = hc.get("checks", [])
        if checks:
            print("  Health Checks:")
            for check in checks:
                status = check.get("status", "UNKNOWN")
                name = check.get("name", "unknown")
                severity = check.get("severity", "INFO")
                icon = "[OK]" if status == "HEALTHY" else "[WARN]" if status == "UNHEALTHY" else "[ERROR]"
                print(f"    {icon} {name}: {status} (severity: {severity})")
    
    return {"status": "ok", "data": data}

def check_recent_orders_from_api(base_url: str) -> Dict[str, Any]:
    """Check recent orders from API logs endpoint."""
    print("\n" + "=" * 80)
    print("CHECKING: Recent Orders (from API)")
    print("=" * 80)
    
    data = check_endpoint(base_url, "/api/logs", "Logs endpoint")
    if not data:
        return {"status": "error", "message": "Could not connect to logs endpoint"}
    
    orders = data.get("orders", [])
    if not orders:
        print("[INFO] No orders found in logs")
        return {"status": "no_orders", "orders": []}
    
    now = time.time()
    cutoff_1h = now - 3600
    cutoff_3h = now - 10800
    cutoff_24h = now - 86400
    
    recent_1h = []
    recent_3h = []
    recent_24h = []
    
    for order in orders[-100:]:  # Check last 100 orders
        order_ts = order.get("_ts", 0)
        if order_ts > cutoff_1h:
            recent_1h.append(order)
        if order_ts > cutoff_3h:
            recent_3h.append(order)
        if order_ts > cutoff_24h:
            recent_24h.append(order)
    
    print(f"Orders in last 1 hour: {len(recent_1h)}")
    print(f"Orders in last 3 hours: {len(recent_3h)}")
    print(f"Orders in last 24 hours: {len(recent_24h)}")
    
    if recent_3h:
        last_order = recent_3h[-1]
        last_ts = last_order.get("_ts", 0)
        age = now - last_ts
        print(f"\nLast Order: {format_time_ago(age)} ago")
        print(f"  - Event: {last_order.get('event', 'unknown')}")
        print(f"  - Symbol: {last_order.get('symbol', 'unknown')}")
        print(f"  - Side: {last_order.get('side', 'unknown')}")
        print(f"  - Qty: {last_order.get('qty', 0)}")
        if age > 10800:
            print(f"  [WARNING] Last order is >3 hours old")
    else:
        if orders:
            last_order = orders[-1]
            last_ts = last_order.get("_ts", 0)
            age = now - last_ts
            print(f"\nLast Order: {format_time_ago(age)} ago (outside 3h window)")
            print(f"  [WARNING] No orders in last 3 hours")
        else:
            print("\n[WARNING] No recent orders found")
    
    return {
        "status": "ok" if recent_3h else "warning",
        "orders_1h": len(recent_1h),
        "orders_3h": len(recent_3h),
        "orders_24h": len(recent_24h),
        "last_order_age": now - orders[-1].get("_ts", 0) if orders else None
    }

def check_positions(base_url: str) -> Dict[str, Any]:
    """Check current positions."""
    print("\n" + "=" * 80)
    print("CHECKING: Current Positions")
    print("=" * 80)
    
    data = check_endpoint(base_url, "/api/positions", "Positions endpoint")
    if not data:
        return {"status": "error"}
    
    positions = data.get("positions", [])
    print(f"Open Positions: {len(positions)}")
    
    if positions:
        total_value = sum(p.get("market_value", 0) for p in positions)
        total_pnl = sum(p.get("unrealized_pl", 0) for p in positions)
        print(f"Total Market Value: ${total_value:,.2f}")
        print(f"Total Unrealized P&L: ${total_pnl:,.2f}")
        print("\nPositions:")
        for pos in positions[:10]:  # Show first 10
            pnl = pos.get("unrealized_pl", 0)
            pnl_sign = "+" if pnl >= 0 else ""
            print(f"  - {pos.get('symbol')}: {pos.get('qty')} @ ${pos.get('avg_entry_price', 0):.2f} | P&L: {pnl_sign}${pnl:.2f}")
    else:
        print("[INFO] No open positions")
    
    return {"status": "ok", "positions": positions}

def check_account(base_url: str) -> Dict[str, Any]:
    """Check account status."""
    print("\n" + "=" * 80)
    print("CHECKING: Account Status")
    print("=" * 80)
    
    data = check_endpoint(base_url, "/api/account", "Account endpoint")
    if not data:
        return {"status": "error"}
    
    if "error" in data:
        print(f"[ERROR] {data['error']}")
        return {"status": "error", "error": data["error"]}
    
    print(f"Account Status: {data.get('status', 'unknown')}")
    print(f"Equity: ${data.get('equity', 0):,.2f}")
    print(f"Cash: ${data.get('cash', 0):,.2f}")
    print(f"Buying Power: ${data.get('buying_power', 0):,.2f}")
    print(f"Portfolio Value: ${data.get('portfolio_value', 0):,.2f}")
    
    if data.get("trading_blocked"):
        print("[WARNING] Trading is blocked!")
    if data.get("account_blocked"):
        print("[CRITICAL] Account is blocked!")
    
    return {"status": "ok", "data": data}

def main():
    """Run all API-based checks."""
    print("=" * 80)
    print("TRADING BOT API HEALTH CHECK")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
    
    # Try different possible base URLs
    base_urls = [
        "http://localhost:8081",  # Main trading bot (from process-compose.yaml)
        "http://localhost:5000",  # Dashboard
        "http://127.0.0.1:8081",
        "http://127.0.0.1:5000"
    ]
    
    base_url = None
    for url in base_urls:
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                base_url = url
                print(f"Found running service at: {url}\n")
                break
        except:
            continue
    
    if not base_url:
        print("[ERROR] Could not find running service on any of:")
        for url in base_urls:
            print(f"  - {url}")
        print("\nMake sure the trading bot is running (check with: process-compose ps)")
        return
    
    # Run checks
    results = {}
    results["health"] = check_health_endpoint(base_url)
    results["orders"] = check_recent_orders_from_api(base_url)
    results["positions"] = check_positions(base_url)
    results["account"] = check_account(base_url)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    issues = []
    if results.get("health", {}).get("data", {}).get("last_heartbeat_age_sec", 0) > 300:
        issues.append("Heartbeat (Doctor) is stale")
    
    if results.get("orders", {}).get("orders_3h", 0) == 0:
        issues.append("No orders in last 3 hours")
    
    if results.get("account", {}).get("data", {}).get("trading_blocked"):
        issues.append("Trading is blocked")
    
    if issues:
        print("[WARNING] Issues detected:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("[OK] All checks passed!")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
