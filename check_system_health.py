#!/usr/bin/env python3
"""
System Health Diagnostic Script
Checks all critical systems to verify trades and monitoring are working properly.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Setup paths
DATA_DIR = Path("data")
STATE_DIR = Path("state")
LOGS_DIR = Path("logs")

def format_time_ago(seconds: float) -> str:
    """Format seconds into human-readable time ago."""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours {int((seconds % 3600) / 60)} minutes"
    else:
        days = int(seconds / 86400)
        hours = int((seconds % 86400) / 3600)
        return f"{days} days {hours} hours"

def check_recent_orders() -> Dict[str, Any]:
    """Check recent order activity."""
    orders_file = DATA_DIR / "live_orders.jsonl"
    result = {
        "status": "unknown",
        "last_order_age_sec": None,
        "last_order": None,
        "recent_orders_1h": 0,
        "recent_orders_3h": 0,
        "recent_orders_24h": 0,
        "file_exists": False
    }
    
    if not orders_file.exists():
        result["status"] = "no_orders_file"
        result["message"] = "Orders file does not exist yet"
        return result
    
    result["file_exists"] = True
    now = time.time()
    cutoff_1h = now - 3600
    cutoff_3h = now - 10800
    cutoff_24h = now - 86400
    
    last_order_ts = 0
    last_order_data = None
    
    try:
        with orders_file.open("r") as f:
            lines = f.readlines()
            for line in lines[-500:]:  # Check last 500 lines
                try:
                    event = json.loads(line.strip())
                    event_ts = event.get("_ts", 0)
                    event_type = event.get("event", "")
                    
                    if event_ts > last_order_ts:
                        last_order_ts = event_ts
                        last_order_data = event
                    
                    if event_ts > cutoff_1h and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:
                        result["recent_orders_1h"] += 1
                    if event_ts > cutoff_3h and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:
                        result["recent_orders_3h"] += 1
                    if event_ts > cutoff_24h and event_type in ["MARKET_FILLED", "LIMIT_FILLED", "ORDER_SUBMITTED"]:
                        result["recent_orders_24h"] += 1
                except:
                    pass
        
        if last_order_ts > 0:
            age_sec = now - last_order_ts
            result["last_order_age_sec"] = age_sec
            result["last_order"] = {
                "timestamp": last_order_ts,
                "datetime": datetime.fromtimestamp(last_order_ts, tz=timezone.utc).isoformat(),
                "event": last_order_data.get("event", "unknown"),
                "symbol": last_order_data.get("symbol", "unknown"),
                "side": last_order_data.get("side", "unknown"),
                "qty": last_order_data.get("qty", 0)
            }
            
            if age_sec < 3600:
                result["status"] = "healthy"
            elif age_sec < 10800:
                result["status"] = "warning"
                result["message"] = f"Last order was {format_time_ago(age_sec)} ago"
            else:
                result["status"] = "stale"
                result["message"] = f"Last order was {format_time_ago(age_sec)} ago"
        else:
            result["status"] = "no_orders"
            result["message"] = "No orders found in file"
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def check_heartbeat() -> Dict[str, Any]:
    """Check heartbeat/Doctor status."""
    # Check multiple possible locations - including doctor_state.json which appears to be the "Doctor" indicator
    heartbeat_files = [
        STATE_DIR / "doctor_state.json",  # This is likely the "Doctor" indicator
        STATE_DIR / "heartbeat.json",
        STATE_DIR / "system_heartbeat.json",
        STATE_DIR / "bot_heartbeat.json",
        STATE_DIR / "heartbeats" / "system_heartbeat.json",
        Path("state/doctor_state.json"),
        Path("state/heartbeat.json"),
        Path("state/system_heartbeat.json"),
        Path("state/bot_heartbeat.json"),
        Path("state/heartbeats/system_heartbeat.json")
    ]
    
    # Also search for any .json files in state/heartbeats directory
    heartbeats_dir = STATE_DIR / "heartbeats"
    if heartbeats_dir.exists():
        for hb_file in heartbeats_dir.glob("*.json"):
            if hb_file not in heartbeat_files:
                heartbeat_files.append(hb_file)
    
    result = {
        "status": "unknown",
        "last_heartbeat_age_sec": None,
        "heartbeat_data": None,
        "file_exists": False,
        "file_location": None
    }
    
    heartbeat_file = None
    for hf in heartbeat_files:
        if hf.exists():
            heartbeat_file = hf
            result["file_location"] = str(hf)
            break
    
    if not heartbeat_file:
        result["status"] = "no_heartbeat_file"
        result["message"] = f"Heartbeat file not found in any of: {[str(hf) for hf in heartbeat_files]}"
        return result
    
    result["file_exists"] = True
    now = time.time()
    
    try:
        data = json.loads(heartbeat_file.read_text())
        result["heartbeat_data"] = data
        
        # Try different possible timestamp fields
        # doctor_state.json might have different field names
        heartbeat_ts = (data.get("timestamp") or data.get("_ts") or 
                       data.get("last_heartbeat") or data.get("last_update") or
                       data.get("updated_at") or data.get("time"))
        
        # If still no timestamp, try to get file modification time as fallback
        if not heartbeat_ts and heartbeat_file.exists():
            try:
                file_mtime = heartbeat_file.stat().st_mtime
                heartbeat_ts = file_mtime
                result["note"] = "Using file modification time as timestamp"
            except:
                pass
        
        if heartbeat_ts:
            age_sec = now - float(heartbeat_ts)
            result["last_heartbeat_age_sec"] = age_sec
            
            if age_sec < 300:  # 5 minutes
                result["status"] = "healthy"
            elif age_sec < 1800:  # 30 minutes
                result["status"] = "warning"
                result["message"] = f"Last heartbeat was {format_time_ago(age_sec)} ago"
            else:
                result["status"] = "stale"
                result["message"] = f"Last heartbeat was {format_time_ago(age_sec)} ago"
        else:
            result["status"] = "no_timestamp"
            result["message"] = "No timestamp found in heartbeat file"
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def check_alpaca_connectivity() -> Dict[str, Any]:
    """Check Alpaca API connectivity and account status."""
    result = {
        "status": "unknown",
        "connected": False,
        "account_status": None,
        "equity": None,
        "positions_count": 0
    }
    
    try:
        # Try to import - if it fails, suggest venv activation
        try:
            import alpaca_trade_api as tradeapi
        except ImportError:
            result["status"] = "module_missing"
            result["message"] = "alpaca_trade_api module not found. Try: source venv/bin/activate (if using venv) or pip3 install alpaca-trade-api"
            return result
        
        api_key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
        api_secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET")
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not api_key or not api_secret:
            result["status"] = "no_credentials"
            result["message"] = "Alpaca credentials not found in environment"
            return result
        
        api = tradeapi.REST(api_key, api_secret, base_url)
        account = api.get_account()
        positions = api.list_positions()
        
        result["connected"] = True
        result["account_status"] = getattr(account, "status", "unknown")
        result["equity"] = float(getattr(account, "equity", 0))
        result["positions_count"] = len(positions)
        result["buying_power"] = float(getattr(account, "buying_power", 0))
        result["portfolio_value"] = float(getattr(account, "portfolio_value", 0))
        
        if result["account_status"] == "ACTIVE":
            result["status"] = "healthy"
        else:
            result["status"] = "warning"
            result["message"] = f"Account status: {result['account_status']}"
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        result["message"] = f"Failed to connect to Alpaca: {str(e)}"
    
    return result

def check_uw_cache() -> Dict[str, Any]:
    """Check UW flow cache freshness."""
    cache_file = DATA_DIR / "uw_flow_cache.json"
    result = {
        "status": "unknown",
        "file_exists": False,
        "cache_age_sec": None,
        "symbol_count": 0
    }
    
    if not cache_file.exists():
        result["status"] = "no_cache_file"
        result["message"] = "UW cache file does not exist"
        return result
    
    result["file_exists"] = True
    now = time.time()
    
    try:
        file_mtime = cache_file.stat().st_mtime
        age_sec = now - file_mtime
        result["cache_age_sec"] = age_sec
        
        cache = json.loads(cache_file.read_text())
        symbol_count = len([k for k in cache.keys() if not k.startswith("_")])
        result["symbol_count"] = symbol_count
        
        if age_sec < 600:  # 10 minutes
            result["status"] = "healthy"
        elif age_sec < 1800:  # 30 minutes
            result["status"] = "warning"
            result["message"] = f"Cache is {format_time_ago(age_sec)} old"
        else:
            result["status"] = "stale"
            result["message"] = f"Cache is {format_time_ago(age_sec)} old"
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def check_recent_trades() -> Dict[str, Any]:
    """Check recent trade activity from Alpaca."""
    result = {
        "status": "unknown",
        "recent_orders": [],
        "orders_24h": 0,
        "orders_3h": 0
    }
    
    try:
        # Try to import - if it fails, suggest venv activation
        try:
            import alpaca_trade_api as tradeapi
        except ImportError:
            result["status"] = "module_missing"
            result["message"] = "alpaca_trade_api module not found. Try: source venv/bin/activate (if using venv) or pip3 install alpaca-trade-api"
            return result
        
        api_key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
        api_secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET")
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not api_key or not api_secret:
            result["status"] = "no_credentials"
            return result
        
        api = tradeapi.REST(api_key, api_secret, base_url)
        
        # Get recent filled orders
        now = datetime.now(timezone.utc)
        cutoff_24h = now.timestamp() - 86400
        cutoff_3h = now.timestamp() - 10800
        
        orders = api.list_orders(status="filled", limit=100, direction="desc")
        
        recent_orders = []
        for order in orders:
            filled_at = getattr(order, "filled_at", None)
            if filled_at:
                try:
                    filled_dt = datetime.fromisoformat(filled_at.replace('Z', '+00:00'))
                    filled_ts = filled_dt.timestamp()
                    
                    if filled_ts > cutoff_24h:
                        result["orders_24h"] += 1
                    if filled_ts > cutoff_3h:
                        result["orders_3h"] += 1
                    
                    if filled_ts > cutoff_3h:
                        recent_orders.append({
                            "symbol": getattr(order, "symbol", "unknown"),
                            "side": getattr(order, "side", "unknown"),
                            "qty": float(getattr(order, "qty", 0)),
                            "filled_at": filled_at,
                            "filled_price": float(getattr(order, "filled_avg_price", 0)),
                            "age_sec": now.timestamp() - filled_ts
                        })
                except:
                    pass
        
        result["recent_orders"] = recent_orders[:10]  # Last 10
        
        if result["orders_3h"] > 0:
            result["status"] = "healthy"
        elif result["orders_24h"] > 0:
            result["status"] = "warning"
            result["message"] = "No trades in last 3 hours, but trades in last 24 hours"
        else:
            result["status"] = "no_recent_trades"
            result["message"] = "No trades in last 24 hours"
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def check_health_supervisor() -> Dict[str, Any]:
    """Check health supervisor status."""
    result = {
        "status": "unknown",
        "checks": []
    }
    
    try:
        from health_supervisor import get_supervisor
        supervisor = get_supervisor()
        status = supervisor.get_status()
        
        result["overall_healthy"] = status.get("overall_healthy", False)
        result["checks"] = status.get("checks", [])
        
        if result["overall_healthy"]:
            result["status"] = "healthy"
        else:
            result["status"] = "issues_found"
            unhealthy = [c for c in result["checks"] if c.get("status") in ["UNHEALTHY", "ERROR"]]
            result["unhealthy_checks"] = unhealthy
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def main():
    """Run all health checks and print results."""
    print("=" * 80)
    print("TRADING BOT SYSTEM HEALTH CHECK")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n")
    
    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    STATE_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    checks = {
        "Alpaca Connectivity": check_alpaca_connectivity,
        "Recent Orders (File)": check_recent_orders,
        "Recent Trades (Alpaca)": check_recent_trades,
        "Heartbeat/Doctor": check_heartbeat,
        "UW Cache": check_uw_cache,
        "Health Supervisor": check_health_supervisor
    }
    
    results = {}
    for name, check_fn in checks.items():
        print(f"\n{'=' * 80}")
        print(f"CHECKING: {name}")
        print('=' * 80)
        try:
            result = check_fn()
            results[name] = result
            
            # Print status
            status_icon = {
                "healthy": "[OK]",
                "warning": "[WARN]",
                "stale": "[STALE]",
                "error": "[ERROR]",
                "no_orders": "[NONE]",
                "no_heartbeat_file": "[NONE]",
                "no_cache_file": "[NONE]",
                "no_credentials": "[ERROR]"
            }.get(result.get("status", "unknown"), "[?]")
            
            print(f"Status: {status_icon} {result.get('status', 'unknown').upper()}")
            
            # Print key information
            if "last_order_age_sec" in result and result["last_order_age_sec"] is not None:
                print(f"Last Order: {format_time_ago(result['last_order_age_sec'])} ago")
                if result.get("last_order"):
                    lo = result["last_order"]
                    print(f"  - Symbol: {lo.get('symbol')}, Side: {lo.get('side')}, Qty: {lo.get('qty')}")
                    print(f"  - Event: {lo.get('event')}")
                    print(f"  - Time: {lo.get('datetime')}")
            
            if "last_heartbeat_age_sec" in result and result["last_heartbeat_age_sec"] is not None:
                print(f"Last Heartbeat: {format_time_ago(result['last_heartbeat_age_sec'])} ago")
            
            if "recent_orders_3h" in result:
                print(f"Recent Orders: {result.get('recent_orders_3h')} in last 3h, {result.get('recent_orders_24h')} in last 24h")
            
            if "orders_3h" in result:
                print(f"Recent Trades (Alpaca): {result.get('orders_3h')} in last 3h, {result.get('orders_24h')} in last 24h")
                if result.get("recent_orders"):
                    print("  Recent trades:")
                    for order in result["recent_orders"][:5]:
                        print(f"    - {order.get('symbol')} {order.get('side')} {order.get('qty')} @ {order.get('filled_price')} ({format_time_ago(order.get('age_sec', 0))} ago)")
            
            if "connected" in result and result.get("connected"):
                print(f"Account Status: {result.get('account_status')}")
                print(f"Equity: ${result.get('equity', 0):,.2f}")
                print(f"Positions: {result.get('positions_count', 0)}")
                print(f"Buying Power: ${result.get('buying_power', 0):,.2f}")
            
            if "cache_age_sec" in result and result["cache_age_sec"] is not None:
                print(f"Cache Age: {format_time_ago(result['cache_age_sec'])}")
                print(f"Symbols Cached: {result.get('symbol_count', 0)}")
            
            if "overall_healthy" in result:
                print(f"Overall Health: {'[OK] Healthy' if result.get('overall_healthy') else '[ISSUES] Issues Found'}")
                unhealthy = result.get("unhealthy_checks", [])
                if unhealthy:
                    print("  Unhealthy Checks:")
                    for check in unhealthy:
                        print(f"    - {check.get('name')}: {check.get('status')} (severity: {check.get('severity')})")
            
            if "message" in result:
                print(f"Message: {result['message']}")
            
            if "error" in result:
                print(f"Error: {result['error']}")
                
        except Exception as e:
            print(f"ERROR: {str(e)}")
            results[name] = {"status": "error", "error": str(e)}
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    healthy_count = sum(1 for r in results.values() if r.get("status") == "healthy")
    warning_count = sum(1 for r in results.values() if r.get("status") == "warning")
    error_count = sum(1 for r in results.values() if r.get("status") in ["error", "stale"])
    
    print(f"Healthy: {healthy_count}/{len(results)}")
    print(f"Warnings: {warning_count}/{len(results)}")
    print(f"Errors/Issues: {error_count}/{len(results)}")
    
    if warning_count > 0 or error_count > 0:
        print("\n[WARNING] Some issues detected. Review the details above.")
    else:
        print("\n[OK] All systems appear healthy!")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
