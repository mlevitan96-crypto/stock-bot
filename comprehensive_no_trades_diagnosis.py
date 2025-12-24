#!/usr/bin/env python3
"""
Comprehensive diagnosis of why no trades are executing.
This works even if investigate_no_trades.py has issues.
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

LOGS_DIR = Path("logs")
DATA_DIR = Path("data")
STATE_DIR = Path("state")

def read_jsonl(path: Path, limit: int = None) -> List[Dict]:
    """Read JSONL file."""
    if not path.exists():
        return []
    results = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if limit:
                lines = lines[-limit:]
            for line in lines:
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except:
                        pass
    except:
        pass
    return results

def check_market_hours() -> Dict:
    """Check if market is open."""
    now = datetime.now(timezone.utc)
    hour = now.hour
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    is_weekend = weekday >= 5
    is_market_hours = not is_weekend and 13 <= hour < 20  # 9 AM - 4 PM EST
    
    return {
        "is_market_hours": is_market_hours,
        "is_weekend": is_weekend,
        "current_time": now.isoformat(),
        "hour_utc": hour,
        "weekday": weekday
    }

def check_services() -> Dict:
    """Check if services are running."""
    import subprocess
    services = {}
    
    for svc in ["deploy_supervisor", "main.py", "dashboard.py", "uw_flow_daemon"]:
        try:
            result = subprocess.run(["pgrep", "-f", svc], capture_output=True, timeout=2)
            services[svc] = result.returncode == 0
        except:
            services[svc] = False
    
    return {
        "services": services,
        "all_running": all(services.values())
    }

def check_execution_cycles() -> Dict:
    """Check recent execution cycles."""
    run_file = LOGS_DIR / "trading.jsonl"
    if not run_file.exists():
        return {"error": "No trading log found"}
    
    cycles = read_jsonl(run_file, limit=100)
    if not cycles:
        return {"error": "No execution cycles found in log"}
    
    # Find cycles that indicate execution
    execution_cycles = [c for c in cycles if c.get("event") in ["run_once", "cycle", "execution"]]
    
    if not execution_cycles:
        return {"error": "No execution cycles found", "total_log_entries": len(cycles)}
    
    last_cycle = execution_cycles[-1]
    last_ts = last_cycle.get("_ts", last_cycle.get("timestamp", 0))
    if isinstance(last_ts, str):
        try:
            last_ts = datetime.fromisoformat(last_ts.replace('Z', '+00:00')).timestamp()
        except:
            last_ts = 0
    
    now = time.time()
    minutes_ago = (now - last_ts) / 60 if last_ts > 0 else 999
    
    clusters = last_cycle.get("clusters", 0)
    orders = last_cycle.get("orders", 0)
    
    return {
        "minutes_since_last_cycle": minutes_ago,
        "last_cycle_clusters": clusters,
        "last_cycle_orders": orders,
        "total_execution_cycles": len(execution_cycles)
    }

def check_positions() -> Dict:
    """Check current positions."""
    try:
        from config.registry import StateFiles
        pos_file = StateFiles.POSITIONS
    except:
        pos_file = STATE_DIR / "internal_positions.json"
    
    if not pos_file.exists():
        return {"count": 0, "positions": []}
    
    try:
        with open(pos_file) as f:
            data = json.load(f)
            positions = data.get("positions", []) if isinstance(data, dict) else []
            return {"count": len(positions), "positions": positions[:10]}
    except:
        return {"count": 0, "positions": []}

def check_blocked_trades() -> Dict:
    """Check why trades are blocked."""
    blocked_file = STATE_DIR / "blocked_trades.jsonl"
    if not blocked_file.exists():
        return {"recent_blocks_count": 0, "block_reasons": {}}
    
    blocks = read_jsonl(blocked_file, limit=100)
    if not blocks:
        return {"recent_blocks_count": 0, "block_reasons": {}}
    
    # Filter recent (last hour)
    now = time.time()
    recent_blocks = [b for b in blocks if b.get("_ts", 0) > (now - 3600)]
    
    # Count by reason
    reasons = {}
    for block in recent_blocks:
        reason = block.get("reason", "unknown")
        reasons[reason] = reasons.get(reason, 0) + 1
    
    return {
        "recent_blocks_count": len(recent_blocks),
        "total_blocks": len(blocks),
        "block_reasons": reasons
    }

def check_uw_cache() -> Dict:
    """Check UW cache status."""
    cache_file = DATA_DIR / "uw_flow_cache.json"
    if not cache_file.exists():
        return {"exists": False, "error": "Cache file does not exist"}
    
    cache_age = time.time() - cache_file.stat().st_mtime
    cache_age_min = cache_age / 60
    
    try:
        with open(cache_file) as f:
            cache = json.load(f)
            tickers = [k for k in cache.keys() if not k.startswith("_")]
            tickers_with_data = [t for t in tickers if cache.get(t, {}).get("flow_trades")]
            return {
                "exists": True,
                "age_minutes": cache_age_min,
                "tickers_in_cache": len(tickers),
                "tickers_with_data": len(tickers_with_data),
                "is_fresh": cache_age_min < 10
            }
    except Exception as e:
        return {"exists": True, "error": str(e), "age_minutes": cache_age_min}

def main():
    """Run comprehensive diagnosis."""
    print("Running comprehensive diagnosis...")
    
    diagnosis = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }
    
    # Run all checks
    diagnosis["checks"]["market_hours"] = check_market_hours()
    diagnosis["checks"]["services"] = check_services()
    diagnosis["checks"]["execution_cycles"] = check_execution_cycles()
    diagnosis["checks"]["positions"] = check_positions()
    diagnosis["checks"]["blocked_trades"] = check_blocked_trades()
    diagnosis["checks"]["uw_cache"] = check_uw_cache()
    
    # Generate summary
    issues = []
    recommendations = []
    
    if not diagnosis["checks"]["market_hours"]["is_market_hours"]:
        issues.append("Market is not open")
    
    if not diagnosis["checks"]["services"]["all_running"]:
        missing = [k for k, v in diagnosis["checks"]["services"]["services"].items() if not v]
        issues.append(f"Services not running: {', '.join(missing)}")
        recommendations.append("Restart missing services")
    
    cycles = diagnosis["checks"]["execution_cycles"]
    if "error" in cycles:
        issues.append(f"Execution cycles: {cycles['error']}")
    elif cycles.get("minutes_since_last_cycle", 999) > 10:
        issues.append(f"No execution cycles in {cycles.get('minutes_since_last_cycle', 0):.1f} minutes")
        recommendations.append("Check if main.py worker thread is running")
    
    pos_count = diagnosis["checks"]["positions"]["count"]
    if pos_count >= 16:
        issues.append(f"At max positions ({pos_count}/16)")
        recommendations.append("Wait for exits or check displacement logic")
    
    blocks = diagnosis["checks"]["blocked_trades"]
    if blocks.get("recent_blocks_count", 0) > 0:
        top_reason = max(blocks.get("block_reasons", {}).items(), key=lambda x: x[1], default=(None, 0))
        if top_reason[0]:
            issues.append(f"Trades blocked: {top_reason[0]} ({top_reason[1]} times)")
            recommendations.append(f"Investigate why {top_reason[0]} is blocking trades")
    
    cache = diagnosis["checks"]["uw_cache"]
    if not cache.get("exists"):
        issues.append("UW cache does not exist")
        recommendations.append("Check if UW daemon is running")
    elif not cache.get("is_fresh"):
        issues.append(f"UW cache is stale ({cache.get('age_minutes', 0):.1f} min old)")
        recommendations.append("Check UW daemon and API connectivity")
    elif cache.get("tickers_with_data", 0) == 0:
        issues.append("UW cache exists but has no flow trades data")
        recommendations.append("Check UW API connectivity and rate limits")
    
    diagnosis["summary"] = {
        "issues": issues,
        "recommendations": recommendations,
        "status": "critical" if issues else "healthy"
    }
    
    # Save results
    output_file = Path("investigate_no_trades.json")
    with open(output_file, 'w') as f:
        json.dump(diagnosis, f, indent=2, default=str)
    
    print("Diagnosis complete. Results saved to investigate_no_trades.json")
    return diagnosis

if __name__ == "__main__":
    main()
