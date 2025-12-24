#!/usr/bin/env python3
"""
Comprehensive investigation: Why no trades today?
This script checks all possible reasons trades might not be executing.
Results are saved to git so Cursor can see them.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config.registry import read_json, CacheFiles, StateFiles, LogFiles
except ImportError:
    print("Warning: Could not import config.registry, using fallback paths")
    def read_json(path):
        try:
            with open(path) as f:
                return json.load(f)
        except:
            return {}

def read_jsonl(path: str, limit: int = None) -> List[Dict]:
    """Read JSONL file, return list of dicts"""
    results = []
    if not os.path.exists(path):
        return results
    try:
        with open(path) as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except:
                        pass
    except Exception as e:
        print(f"Error reading {path}: {e}")
    return results

def check_market_hours() -> Dict:
    """Check if market is/was open"""
    now = datetime.now()
    # Simple check - market is 9:30 AM - 4:00 PM ET
    # This is approximate, should use proper market calendar
    hour = now.hour
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    is_weekend = weekday >= 5
    is_market_hours = 9 <= hour < 16 and not is_weekend
    
    return {
        "current_time": now.isoformat(),
        "is_weekend": is_weekend,
        "is_market_hours": is_market_hours,
        "hour": hour,
        "weekday": weekday,
        "note": "Market hours: 9:30 AM - 4:00 PM ET, Mon-Fri"
    }

def check_services_running() -> Dict:
    """Check if trading bot services are running"""
    import subprocess
    
    services = {
        "deploy_supervisor": False,
        "main.py": False,
        "dashboard.py": False,
        "uw_flow_daemon": False
    }
    
    pids = {}
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout
        
        for service, pattern in [
            ("deploy_supervisor", "deploy_supervisor"),
            ("main.py", "python.*main.py"),
            ("dashboard.py", "python.*dashboard.py"),
            ("uw_flow_daemon", "uw_flow_daemon")
        ]:
            if pattern in output:
                services[service] = True
                # Try to get PID
                for line in output.split('\n'):
                    if pattern in line and 'grep' not in line:
                        parts = line.split()
                        if len(parts) > 1:
                            pids[service] = parts[1]
                            break
    except Exception as e:
        return {"error": str(e), "services": services}
    
    return {
        "services": services,
        "pids": pids,
        "all_running": all(services.values())
    }

def check_recent_execution_cycles() -> Dict:
    """Check if execution cycles are running"""
    run_log = LogFiles.RUN_LOG
    if not os.path.exists(run_log):
        return {"error": f"Run log not found: {run_log}", "recent_cycles": []}
    
    cycles = read_jsonl(run_log, limit=50)
    
    if not cycles:
        return {"error": "No cycles found in run log", "recent_cycles": []}
    
    # Get most recent cycles
    recent = cycles[-10:] if len(cycles) >= 10 else cycles
    
    # Check timestamps
    now = datetime.now()
    latest_cycle = None
    if recent:
        try:
            latest_ts = recent[-1].get("ts") or recent[-1].get("timestamp")
            if latest_ts:
                if isinstance(latest_ts, str):
                    latest_cycle = datetime.fromisoformat(latest_ts.replace('Z', '+00:00'))
                elif isinstance(latest_ts, (int, float)):
                    latest_cycle = datetime.fromtimestamp(latest_ts)
        except:
            pass
    
    minutes_ago = None
    if latest_cycle:
        delta = now - latest_cycle.replace(tzinfo=None) if latest_cycle.tzinfo else now - latest_cycle
        minutes_ago = int(delta.total_seconds() / 60)
    
    return {
        "total_cycles": len(cycles),
        "recent_cycles_count": len(recent),
        "latest_cycle": latest_cycle.isoformat() if latest_cycle else None,
        "minutes_since_last_cycle": minutes_ago,
        "sample_cycles": recent[-3:] if recent else []
    }

def check_positions() -> Dict:
    """Check current positions"""
    positions_file = StateFiles.POSITIONS
    if not os.path.exists(positions_file):
        return {"error": f"Positions file not found: {positions_file}", "count": 0, "positions": []}
    
    try:
        positions = read_json(positions_file)
        if isinstance(positions, dict):
            # Check if it's a dict of positions
            pos_list = [v for v in positions.values() if isinstance(v, dict)]
            count = len(pos_list)
        elif isinstance(positions, list):
            pos_list = positions
            count = len(pos_list)
        else:
            pos_list = []
            count = 0
    except Exception as e:
        return {"error": str(e), "count": 0, "positions": []}
    
    return {
        "count": count,
        "positions": pos_list[:10],  # First 10
        "max_positions": 16  # Typical max
    }

def check_blocked_trades() -> Dict:
    """Check why trades are being blocked"""
    blocked_file = StateFiles.BLOCKED_TRADES
    if not os.path.exists(blocked_file):
        return {"error": f"Blocked trades file not found: {blocked_file}", "recent_blocks": []}
    
    blocks = read_jsonl(blocked_file, limit=100)
    
    if not blocks:
        return {"total_blocks": 0, "recent_blocks": [], "reasons": {}}
    
    # Get recent blocks (last 24 hours)
    now = datetime.now()
    recent_blocks = []
    reasons = {}
    
    for block in blocks[-50:]:  # Last 50
        try:
            ts = block.get("ts") or block.get("timestamp")
            if ts:
                if isinstance(ts, str):
                    block_time = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                elif isinstance(ts, (int, float)):
                    block_time = datetime.fromtimestamp(ts)
                else:
                    continue
                
                delta = now - block_time.replace(tzinfo=None) if block_time.tzinfo else now - block_time
                if delta.total_seconds() < 86400:  # Last 24 hours
                    recent_blocks.append(block)
                    reason = block.get("reason") or block.get("gate_reason") or "unknown"
                    reasons[reason] = reasons.get(reason, 0) + 1
        except:
            pass
    
    return {
        "total_blocks": len(blocks),
        "recent_blocks_count": len(recent_blocks),
        "recent_blocks": recent_blocks[-10:],
        "reasons": reasons
    }

def check_signals_and_clusters() -> Dict:
    """Check if signals/clusters are being generated"""
    cache_file = CacheFiles.UW_FLOW_CACHE
    if not os.path.exists(cache_file):
        return {"error": f"Cache file not found: {cache_file}", "tickers_with_data": 0}
    
    try:
        cache = read_json(cache_file)
        if not isinstance(cache, dict):
            return {"error": "Cache is not a dict", "tickers_with_data": 0}
        
        tickers_with_trades = []
        tickers_with_clusters = []
        
        for ticker, data in cache.items():
            if isinstance(data, dict):
                # Check for flow_trades
                trades = data.get("flow_trades", [])
                if trades and len(trades) > 0:
                    tickers_with_trades.append(ticker)
                
                # Check for clusters
                clusters = data.get("clusters", [])
                if clusters and len(clusters) > 0:
                    tickers_with_clusters.append(ticker)
        
        return {
            "total_tickers": len(cache),
            "tickers_with_trades": len(tickers_with_trades),
            "tickers_with_clusters": len(tickers_with_clusters),
            "sample_tickers_with_trades": tickers_with_trades[:10],
            "sample_tickers_with_clusters": tickers_with_clusters[:10]
        }
    except Exception as e:
        return {"error": str(e), "tickers_with_data": 0}

def check_recent_orders() -> Dict:
    """Check recent order submissions"""
    order_log = LogFiles.ORDER_LOG
    if not os.path.exists(order_log):
        return {"error": f"Order log not found: {order_log}", "recent_orders": []}
    
    orders = read_jsonl(order_log, limit=50)
    
    if not orders:
        return {"total_orders": 0, "recent_orders": [], "today_orders": 0}
    
    # Filter today's orders
    now = datetime.now()
    today_orders = []
    
    for order in orders:
        try:
            ts = order.get("ts") or order.get("timestamp")
            if ts:
                if isinstance(ts, str):
                    order_time = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                elif isinstance(ts, (int, float)):
                    order_time = datetime.fromtimestamp(ts)
                else:
                    continue
                
                delta = now - order_time.replace(tzinfo=None) if order_time.tzinfo else now - order_time
                if delta.total_seconds() < 86400:  # Last 24 hours
                    today_orders.append(order)
        except:
            pass
    
    return {
        "total_orders": len(orders),
        "today_orders_count": len(today_orders),
        "recent_orders": today_orders[-10:] if today_orders else orders[-10:]
    }

def check_uw_daemon_status() -> Dict:
    """Check UW daemon status and cache freshness"""
    cache_file = CacheFiles.UW_FLOW_CACHE
    daemon_log = "logs/uw-daemon-pc.log"
    
    status = {
        "cache_exists": os.path.exists(cache_file),
        "daemon_log_exists": os.path.exists(daemon_log),
        "cache_age_seconds": None,
        "recent_daemon_activity": []
    }
    
    # Check cache age
    if status["cache_exists"]:
        try:
            mtime = os.path.getmtime(cache_file)
            age = datetime.now().timestamp() - mtime
            status["cache_age_seconds"] = int(age)
            status["cache_age_minutes"] = int(age / 60)
        except:
            pass
    
    # Check daemon log
    if status["daemon_log_exists"]:
        try:
            lines = read_jsonl(daemon_log, limit=20)
            status["recent_daemon_activity"] = lines[-5:] if lines else []
        except:
            pass
    
    return status

def check_api_health() -> Dict:
    """Check API connectivity and health"""
    health_endpoints = [
        "http://localhost:8080/health",
        "http://localhost:5000/api/sre/health"
    ]
    
    results = {}
    for endpoint in health_endpoints:
        try:
            import requests
            resp = requests.get(endpoint, timeout=5)
            results[endpoint] = {
                "status_code": resp.status_code,
                "response": resp.json() if resp.status_code == 200 else None
            }
        except Exception as e:
            results[endpoint] = {"error": str(e)}
    
    return results

def main():
    """Run comprehensive investigation"""
    print("=" * 80)
    print("COMPREHENSIVE INVESTIGATION: Why No Trades Today?")
    print("=" * 80)
    print()
    
    investigation = {
        "timestamp": datetime.now().isoformat(),
        "investigation_date": datetime.now().strftime("%Y-%m-%d"),
        "checks": {}
    }
    
    print("1. Checking market hours...")
    investigation["checks"]["market_hours"] = check_market_hours()
    print(f"   Market hours: {investigation['checks']['market_hours']['is_market_hours']}")
    
    print("\n2. Checking services running...")
    investigation["checks"]["services"] = check_services_running()
    print(f"   All services running: {investigation['checks']['services'].get('all_running', False)}")
    
    print("\n3. Checking execution cycles...")
    investigation["checks"]["execution_cycles"] = check_recent_execution_cycles()
    cycles = investigation["checks"]["execution_cycles"]
    print(f"   Recent cycles: {cycles.get('recent_cycles_count', 0)}")
    if cycles.get("minutes_since_last_cycle"):
        print(f"   Last cycle: {cycles['minutes_since_last_cycle']} minutes ago")
    
    print("\n4. Checking positions...")
    investigation["checks"]["positions"] = check_positions()
    print(f"   Current positions: {investigation['checks']['positions'].get('count', 0)}")
    
    print("\n5. Checking blocked trades...")
    investigation["checks"]["blocked_trades"] = check_blocked_trades()
    blocks = investigation["checks"]["blocked_trades"]
    print(f"   Recent blocks: {blocks.get('recent_blocks_count', 0)}")
    if blocks.get("reasons"):
        print(f"   Block reasons: {blocks['reasons']}")
    
    print("\n6. Checking signals/clusters...")
    investigation["checks"]["signals"] = check_signals_and_clusters()
    signals = investigation["checks"]["signals"]
    print(f"   Tickers with trades: {signals.get('tickers_with_trades', 0)}")
    print(f"   Tickers with clusters: {signals.get('tickers_with_clusters', 0)}")
    
    print("\n7. Checking recent orders...")
    investigation["checks"]["orders"] = check_recent_orders()
    orders = investigation["checks"]["orders"]
    print(f"   Orders today: {orders.get('today_orders_count', 0)}")
    
    print("\n8. Checking UW daemon...")
    investigation["checks"]["uw_daemon"] = check_uw_daemon_status()
    daemon = investigation["checks"]["uw_daemon"]
    if daemon.get("cache_age_minutes"):
        print(f"   Cache age: {daemon['cache_age_minutes']} minutes")
    
    print("\n9. Checking API health...")
    investigation["checks"]["api_health"] = check_api_health()
    
    # Generate summary
    print("\n" + "=" * 80)
    print("INVESTIGATION SUMMARY")
    print("=" * 80)
    
    issues = []
    
    if not investigation["checks"]["services"].get("all_running"):
        issues.append("❌ Not all services are running")
    
    cycles = investigation["checks"]["execution_cycles"]
    if cycles.get("minutes_since_last_cycle", 999) > 10:
        issues.append(f"⚠️  Last execution cycle was {cycles.get('minutes_since_last_cycle')} minutes ago")
    
    positions = investigation["checks"]["positions"]
    if positions.get("count", 0) >= positions.get("max_positions", 16):
        issues.append(f"⚠️  At max positions ({positions.get('count')}/{positions.get('max_positions')})")
    
    blocks = investigation["checks"]["blocked_trades"]
    if blocks.get("recent_blocks_count", 0) > 0:
        issues.append(f"⚠️  {blocks.get('recent_blocks_count')} trades blocked recently")
        if blocks.get("reasons"):
            issues.append(f"   Block reasons: {blocks['reasons']}")
    
    signals = investigation["checks"]["signals"]
    if signals.get("tickers_with_trades", 0) == 0:
        issues.append("❌ No tickers have flow trades in cache")
    
    if signals.get("tickers_with_clusters", 0) == 0:
        issues.append("❌ No tickers have clusters generated")
    
    orders = investigation["checks"]["orders"]
    if orders.get("today_orders_count", 0) == 0:
        issues.append("❌ No orders submitted today")
    
    daemon = investigation["checks"]["uw_daemon"]
    if daemon.get("cache_age_minutes", 0) > 60:
        issues.append(f"⚠️  Cache is {daemon.get('cache_age_minutes')} minutes old")
    
    investigation["summary"] = {
        "issues_found": len(issues),
        "issues": issues,
        "status": "CRITICAL" if any("❌" in i for i in issues) else "WARNING" if issues else "OK"
    }
    
    for issue in issues:
        print(f"  {issue}")
    
    if not issues:
        print("  ✅ No obvious issues found - investigation needed")
    
    # Save to file
    output_file = "investigation_no_trades.json"
    with open(output_file, 'w') as f:
        json.dump(investigation, f, indent=2)
    
    print(f"\n✅ Investigation saved to: {output_file}")
    print(f"   Run: git add {output_file} && git commit -m 'Investigation: No trades today' && git push origin main")
    
    return investigation

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result["summary"]["status"] != "CRITICAL" else 1)
    except Exception as e:
        print(f"\n❌ Error during investigation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

