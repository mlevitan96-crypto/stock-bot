#!/usr/bin/env python3
"""
Comprehensive Trading Diagnosis
Identifies why trades aren't happening - checks all failure points
"""

import json
import time
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Color output for readability
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_status(name: str, status: str, details: str = ""):
    if status == "OK":
        symbol = "✓"
        color = Colors.GREEN
    elif status == "WARN":
        symbol = "⚠"
        color = Colors.YELLOW
    else:
        symbol = "✗"
        color = Colors.RED
    print(f"{color}{symbol} {name}{Colors.RESET}: {details}")

def check_bot_running() -> Dict:
    """Check if bot process is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'python.*main.py'], 
                              capture_output=True, timeout=5)
        running = result.returncode == 0
        pid = result.stdout.decode().strip() if running else None
        return {"running": running, "pid": pid}
    except Exception as e:
        return {"running": False, "error": str(e)}

def check_uw_daemon() -> Dict:
    """Check if UW daemon is running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'uw_flow_daemon'], 
                              capture_output=True, timeout=5)
        running = result.returncode == 0
        pid = result.stdout.decode().strip() if running else None
        return {"running": running, "pid": pid}
    except Exception as e:
        return {"running": False, "error": str(e)}

def check_cache() -> Dict:
    """Check UW cache status"""
    cache_file = Path("data/uw_flow_cache.json")
    if not cache_file.exists():
        return {"exists": False, "size": 0, "age_minutes": None, "symbols": 0}
    
    size = cache_file.stat().st_size
    mtime = cache_file.stat().st_mtime
    age_minutes = (time.time() - mtime) / 60
    
    try:
        with cache_file.open() as f:
            cache = json.load(f)
        symbols = [k for k in cache.keys() if k != "_metadata"]
        return {
            "exists": True,
            "size": size,
            "age_minutes": round(age_minutes, 1),
            "symbols": len(symbols),
            "symbol_list": symbols[:10]  # First 10
        }
    except Exception as e:
        return {"exists": True, "size": size, "age_minutes": round(age_minutes, 1), "error": str(e)}

def check_market_hours() -> Dict:
    """Check if market is open"""
    try:
        from datetime import datetime
        import pytz
        
        et = pytz.timezone('US/Eastern')
        now_et = datetime.now(et)
        current_time = now_et.time()
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = datetime.strptime("09:30", "%H:%M").time()
        market_close = datetime.strptime("16:00", "%H:%M").time()
        
        is_open = market_open <= current_time <= market_close
        is_weekend = now_et.weekday() >= 5
        
        return {
            "is_open": is_open and not is_weekend,
            "current_time_et": current_time.strftime("%H:%M:%S"),
            "day_of_week": now_et.strftime("%A"),
            "is_weekend": is_weekend
        }
    except Exception as e:
        return {"error": str(e)}

def check_freeze_state() -> Dict:
    """Check if bot is frozen"""
    freeze_file = Path("state/freeze_flags.json")
    if not freeze_file.exists():
        return {"frozen": False, "flags": {}}
    
    try:
        with freeze_file.open() as f:
            flags = json.load(f)
        active_flags = {k: v for k, v in flags.items() if v.get("active", False)}
        return {
            "frozen": len(active_flags) > 0,
            "flags": active_flags
        }
    except Exception as e:
        return {"error": str(e)}

def check_adaptive_weights() -> Dict:
    """Check adaptive weights initialization"""
    weights_file = Path("state/signal_weights.json")
    if not weights_file.exists():
        return {"initialized": False, "error": "File missing"}
    
    try:
        with weights_file.open() as f:
            state = json.load(f)
        bands = state.get("weight_bands", {})
        return {
            "initialized": len(bands) == 21,
            "component_count": len(bands),
            "expected": 21
        }
    except Exception as e:
        return {"error": str(e)}

def check_self_healing_threshold() -> Dict:
    """Check self-healing threshold status"""
    threshold_file = Path("state/self_healing_threshold.json")
    if not threshold_file.exists():
        return {"exists": False}
    
    try:
        with threshold_file.open() as f:
            state = json.load(f)
        return {
            "exists": True,
            "adjustment": state.get("adjustment", 0.0),
            "activated": state.get("adjustment", 0.0) > 0,
            "consecutive_losses": state.get("consecutive_losses", 0)
        }
    except Exception as e:
        return {"error": str(e)}

def check_recent_signals() -> Dict:
    """Check recent signal generation"""
    attribution_file = Path("data/uw_attribution.jsonl")
    if not attribution_file.exists():
        attribution_file = Path("logs/attribution.jsonl")
    
    if not attribution_file.exists():
        return {"exists": False, "recent_count": 0}
    
    try:
        recent_signals = []
        with attribution_file.open() as f:
            lines = f.readlines()
            # Get last 20 lines
            for line in lines[-20:]:
                try:
                    signal = json.loads(line.strip())
                    if signal.get("type") == "attribution":
                        recent_signals.append(signal)
                except:
                    continue
        
        # Filter signals from last hour
        one_hour_ago = time.time() - 3600
        recent = [s for s in recent_signals if s.get("ts", 0) > one_hour_ago]
        
        # Count by decision
        decisions = {}
        for s in recent:
            decision = s.get("decision", "unknown")
            decisions[decision] = decisions.get(decision, 0) + 1
        
        return {
            "exists": True,
            "recent_count": len(recent),
            "total_last_20": len(recent_signals),
            "decisions": decisions,
            "latest_score": recent_signals[-1].get("score", 0) if recent_signals else None
        }
    except Exception as e:
        return {"error": str(e)}

def check_clusters() -> Dict:
    """Check if clusters are being generated"""
    # Check recent logs for cluster generation
    log_file = Path("logs/bot.log")
    if not log_file.exists():
        return {"log_exists": False}
    
    try:
        # Read last 100 lines
        with log_file.open() as f:
            lines = f.readlines()
        
        recent_lines = lines[-100:] if len(lines) > 100 else lines
        cluster_mentions = [l for l in recent_lines if "cluster" in l.lower() or "composite_score" in l.lower()]
        
        return {
            "log_exists": True,
            "recent_cluster_mentions": len(cluster_mentions),
            "sample_lines": cluster_mentions[-5:] if cluster_mentions else []
        }
    except Exception as e:
        return {"error": str(e)}

def check_positions() -> Dict:
    """Check current positions"""
    try:
        import os
        from dotenv import load_dotenv
        import alpaca_trade_api as tradeapi
        
        load_dotenv()
        api_key = os.getenv("ALPACA_KEY")
        api_secret = os.getenv("ALPACA_SECRET")
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not api_key or not api_secret:
            return {"error": "Missing Alpaca credentials"}
        
        api = tradeapi.REST(api_key, api_secret, base_url)
        positions = api.list_positions()
        
        return {
            "count": len(positions),
            "symbols": [p.symbol for p in positions],
            "max_allowed": 16  # MAX_CONCURRENT_POSITIONS
        }
    except ImportError:
        return {"error": "Alpaca API not available"}
    except Exception as e:
        return {"error": str(e)}

def check_config_thresholds() -> Dict:
    """Check configuration thresholds"""
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        return {
            "MIN_EXEC_SCORE": float(os.getenv("MIN_EXEC_SCORE", "2.0")),
            "MAX_CONCURRENT_POSITIONS": int(os.getenv("MAX_CONCURRENT_POSITIONS", "16")),
            "MAX_NEW_POSITIONS_PER_CYCLE": 6,
            "SIZE_BASE_USD": float(os.getenv("SIZE_BASE_USD", "500")),
            "MIN_NOTIONAL_USD": float(os.getenv("MIN_NOTIONAL_USD", "100"))
        }
    except Exception as e:
        return {"error": str(e)}

def check_readiness_status() -> Dict:
    """Check trading readiness status"""
    readiness_file = Path("state/trading_readiness.json")
    if not readiness_file.exists():
        return {"exists": False}
    
    try:
        with readiness_file.open() as f:
            status = json.load(f)
        return {
            "exists": True,
            "overall_status": status.get("overall_status", "UNKNOWN"),
            "blocked_fps": status.get("blocked_fps", []),
            "warn_fps": status.get("warn_fps", [])
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    print_section("COMPREHENSIVE TRADING DIAGNOSIS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    issues = []
    warnings = []
    
    # 1. Bot Running
    print_section("1. BOT STATUS")
    bot_status = check_bot_running()
    if bot_status.get("running"):
        print_status("Bot Process", "OK", f"Running (PID: {bot_status.get('pid')})")
    else:
        print_status("Bot Process", "ERROR", "NOT RUNNING")
        issues.append("Bot process not running")
    
    # 2. UW Daemon
    daemon_status = check_uw_daemon()
    if daemon_status.get("running"):
        print_status("UW Daemon", "OK", f"Running (PID: {daemon_status.get('pid')})")
    else:
        print_status("UW Daemon", "ERROR", "NOT RUNNING")
        issues.append("UW daemon not running")
    
    # 3. Market Hours
    print_section("2. MARKET STATUS")
    market = check_market_hours()
    if market.get("is_open"):
        print_status("Market", "OK", f"OPEN ({market.get('current_time_et')} ET)")
    elif market.get("is_weekend"):
        print_status("Market", "WARN", f"WEEKEND ({market.get('day_of_week')})")
        warnings.append("Market is closed (weekend)")
    else:
        print_status("Market", "WARN", f"CLOSED ({market.get('current_time_et')} ET)")
        warnings.append("Market is closed")
    
    # 4. Cache Status
    print_section("3. DATA & SIGNALS")
    cache = check_cache()
    if cache.get("exists") and cache.get("size", 0) > 0:
        age = cache.get("age_minutes", 0)
        if age < 10:
            print_status("UW Cache", "OK", f"Fresh ({age} min old, {cache.get('symbols')} symbols)")
        elif age < 30:
            print_status("UW Cache", "WARN", f"Stale ({age} min old, {cache.get('symbols')} symbols)")
            warnings.append(f"Cache is {age} minutes old")
        else:
            print_status("UW Cache", "ERROR", f"Very stale ({age} min old)")
            issues.append(f"Cache is {age} minutes old")
    else:
        print_status("UW Cache", "ERROR", "Missing or empty")
        issues.append("UW cache missing or empty")
    
    # 5. Freeze State
    print_section("4. FREEZE STATE")
    freeze = check_freeze_state()
    if freeze.get("frozen"):
        flags = freeze.get("flags", {})
        print_status("Freeze State", "ERROR", f"FROZEN - {len(flags)} active flags")
        for flag, details in flags.items():
            print(f"  - {flag}: {details.get('reason', 'unknown')}")
        issues.append(f"Bot is frozen ({len(flags)} flags)")
    else:
        print_status("Freeze State", "OK", "Not frozen")
    
    # 6. Adaptive Weights
    print_section("5. ADAPTIVE WEIGHTS")
    weights = check_adaptive_weights()
    if weights.get("initialized"):
        print_status("Adaptive Weights", "OK", f"{weights.get('component_count')} components")
    else:
        print_status("Adaptive Weights", "ERROR", 
                    f"Not initialized ({weights.get('component_count', 0)}/{weights.get('expected', 21)})")
        issues.append("Adaptive weights not initialized")
    
    # 7. Self-Healing Threshold
    threshold = check_self_healing_threshold()
    if threshold.get("activated"):
        adj = threshold.get("adjustment", 0)
        losses = threshold.get("consecutive_losses", 0)
        print_status("Self-Healing Threshold", "WARN", 
                    f"ACTIVATED (+{adj} adjustment, {losses} consecutive losses)")
        warnings.append(f"Threshold raised by {adj} due to {losses} losses")
    else:
        print_status("Self-Healing Threshold", "OK", "Not activated")
    
    # 8. Recent Signals
    print_section("6. SIGNAL GENERATION")
    signals = check_recent_signals()
    if signals.get("exists"):
        recent = signals.get("recent_count", 0)
        decisions = signals.get("decisions", {})
        if recent > 0:
            print_status("Recent Signals", "OK", f"{recent} in last hour")
            print(f"  Decisions: {decisions}")
            if "rejected" in decisions or "blocked" in decisions:
                print(f"  Latest score: {signals.get('latest_score', 'N/A')}")
        else:
            print_status("Recent Signals", "WARN", "No signals in last hour")
            warnings.append("No signals generated in last hour")
    else:
        print_status("Recent Signals", "WARN", "Attribution file not found")
        warnings.append("No attribution file found")
    
    # 9. Clusters
    clusters = check_clusters()
    if clusters.get("log_exists"):
        mentions = clusters.get("recent_cluster_mentions", 0)
        if mentions > 0:
            print_status("Cluster Generation", "OK", f"{mentions} mentions in recent logs")
        else:
            print_status("Cluster Generation", "WARN", "No cluster mentions in recent logs")
            warnings.append("No cluster generation detected")
    
    # 10. Positions
    print_section("7. POSITIONS")
    positions = check_positions()
    if "error" not in positions:
        count = positions.get("count", 0)
        max_allowed = positions.get("max_allowed", 16)
        if count < max_allowed:
            print_status("Positions", "OK", f"{count}/{max_allowed} (room for {max_allowed - count} more)")
        else:
            print_status("Positions", "WARN", f"{count}/{max_allowed} (AT CAPACITY)")
            warnings.append(f"At position capacity ({count}/{max_allowed})")
        if count > 0:
            print(f"  Symbols: {', '.join(positions.get('symbols', [])[:10])}")
    else:
        print_status("Positions", "WARN", f"Could not check: {positions.get('error')}")
    
    # 11. Configuration
    print_section("8. CONFIGURATION")
    config = check_config_thresholds()
    if "error" not in config:
        print(f"MIN_EXEC_SCORE: {config.get('MIN_EXEC_SCORE', 'N/A')}")
        print(f"MAX_CONCURRENT_POSITIONS: {config.get('MAX_CONCURRENT_POSITIONS', 'N/A')}")
        print(f"MAX_NEW_POSITIONS_PER_CYCLE: {config.get('MAX_NEW_POSITIONS_PER_CYCLE', 'N/A')}")
        print(f"SIZE_BASE_USD: ${config.get('SIZE_BASE_USD', 'N/A')}")
        print(f"MIN_NOTIONAL_USD: ${config.get('MIN_NOTIONAL_USD', 'N/A')}")
    else:
        print_status("Configuration", "WARN", f"Could not load: {config.get('error')}")
    
    # 12. Readiness Status
    print_section("9. TRADING READINESS")
    readiness = check_readiness_status()
    if readiness.get("exists"):
        overall = readiness.get("overall_status", "UNKNOWN")
        blocked = readiness.get("blocked_fps", [])
        if overall == "READY":
            print_status("Readiness", "OK", "READY")
        elif overall == "BLOCKED":
            print_status("Readiness", "ERROR", f"BLOCKED ({len(blocked)} failure points)")
            for fp in blocked:
                print(f"  - {fp}")
            issues.append(f"Readiness BLOCKED: {blocked}")
        else:
            print_status("Readiness", "WARN", overall)
    else:
        print_status("Readiness", "WARN", "Status file not found")
    
    # Summary
    print_section("DIAGNOSIS SUMMARY")
    if issues:
        print(f"{Colors.RED}{Colors.BOLD}CRITICAL ISSUES ({len(issues)}):{Colors.RESET}")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print(f"{Colors.GREEN}No critical issues found{Colors.RESET}")
    
    if warnings:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}WARNINGS ({len(warnings)}):{Colors.RESET}")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    
    if not issues and not warnings:
        print(f"{Colors.GREEN}{Colors.BOLD}System appears healthy - trading should be active{Colors.RESET}")
    
    print(f"\n{Colors.BLUE}Next steps:{Colors.RESET}")
    if issues:
        print("  1. Fix critical issues listed above")
        print("  2. Restart bot if needed")
        print("  3. Monitor logs for signal generation")
    else:
        print("  1. Check logs for signal generation details")
        print("  2. Verify signals are reaching threshold")
        print("  3. Check if expectancy gate is blocking trades")

if __name__ == "__main__":
    import os
    main()

