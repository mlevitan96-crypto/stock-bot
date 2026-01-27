#!/usr/bin/env python3
"""
Comprehensive Trading Bot Audit - Runs on Droplet
==================================================
This script runs directly on the droplet to audit the entire trading system.
It checks:
- Running processes
- Recent log activity
- Signal capture and processing
- Exit criteria execution
- Trade execution
- Logging systems
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def run_command(cmd: str) -> tuple:
    """Run shell command and return (stdout, stderr, exit_code)"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", -1
    except Exception as e:
        return "", str(e), -1

def check_process_running(process_name: str) -> Dict[str, Any]:
    """Check if a process is running"""
    stdout, stderr, code = run_command(f"pgrep -f '{process_name}'")
    pids = [p.strip() for p in stdout.strip().split('\n') if p.strip()]
    return {
        "running": len(pids) > 0,
        "pids": pids,
        "count": len(pids)
    }

def check_file_recent(path: Path, max_age_minutes: int = 60) -> Dict[str, Any]:
    """Check if file exists and is recent"""
    if not path.exists():
        return {"exists": False, "recent": False, "age_minutes": None}
    
    try:
        mtime = path.stat().st_mtime
        age_minutes = (time.time() - mtime) / 60.0
        return {
            "exists": True,
            "recent": age_minutes <= max_age_minutes,
            "age_minutes": round(age_minutes, 2),
            "size": path.stat().st_size
        }
    except Exception as e:
        return {"exists": True, "recent": False, "age_minutes": None, "error": str(e)}

def count_jsonl_entries(path: Path, max_age_minutes: int = 60) -> Dict[str, Any]:
    """Count entries in JSONL file and check for recent entries"""
    if not path.exists():
        return {"exists": False, "total": 0, "recent": 0}
    
    try:
        import time
        now = time.time()
        total = 0
        recent = 0
        
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total += 1
                try:
                    entry = json.loads(line)
                    ts_str = entry.get("ts") or entry.get("_ts") or entry.get("timestamp")
                    if ts_str:
                        if isinstance(ts_str, (int, float)):
                            entry_time = ts_str
                        else:
                            from datetime import datetime
                            entry_time = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00")).timestamp()
                        
                        age_minutes = (now - entry_time) / 60.0
                        if age_minutes <= max_age_minutes:
                            recent += 1
                except:
                    pass
        
        return {"exists": True, "total": total, "recent": recent}
    except Exception as e:
        return {"exists": True, "total": 0, "recent": 0, "error": str(e)}

def audit_system() -> Dict[str, Any]:
    """Run comprehensive system audit"""
    print("=" * 80)
    print("COMPREHENSIVE TRADING BOT AUDIT")
    print("=" * 80)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}\n")
    
    audit_results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processes": {},
        "files": {},
        "logs": {},
        "cache": {},
        "state": {},
        "issues": []
    }
    
    # 1. Check Running Processes
    print("1. CHECKING RUNNING PROCESSES...")
    print("-" * 80)
    
    processes_to_check = [
        "deploy_supervisor.py",
        "uw_flow_daemon.py",
        "main.py",
        "dashboard.py",
        "heartbeat_keeper.py"
    ]
    
    for proc_name in processes_to_check:
        status = check_process_running(proc_name)
        audit_results["processes"][proc_name] = status
        status_str = "RUNNING" if status["running"] else "NOT RUNNING"
        print(f"  {proc_name}: {status_str} (PIDs: {status['pids']})")
        if not status["running"]:
            audit_results["issues"].append(f"Process not running: {proc_name}")
    
    print()
    
    # 2. Check Critical Files
    print("2. CHECKING CRITICAL FILES...")
    print("-" * 80)
    
    import time
    files_to_check = {
        "uw_cache": Path("data/uw_flow_cache.json"),
        "position_metadata": Path("state/position_metadata.json"),
        "bot_heartbeat": Path("state/bot_heartbeat.json"),
        "signal_weights": Path("state/signal_weights.json"),
    }
    
    for name, path in files_to_check.items():
        status = check_file_recent(path, max_age_minutes=60)
        audit_results["files"][name] = status
        if status["exists"]:
            age_str = f"{status['age_minutes']:.1f} min ago" if status.get("age_minutes") else "unknown"
            size_str = f"{status.get('size', 0)} bytes"
            recent_str = "RECENT" if status["recent"] else "STALE"
            print(f"  {name}: EXISTS ({recent_str}, {age_str}, {size_str})")
            if not status["recent"]:
                audit_results["issues"].append(f"File is stale: {name} ({age_str})")
        else:
            print(f"  {name}: MISSING")
            audit_results["issues"].append(f"File missing: {name}")
    
    print()
    
    # 3. Check Log Files
    print("3. CHECKING LOG FILES...")
    print("-" * 80)
    
    log_files = {
        "attribution": Path("logs/attribution.jsonl"),
        "run": Path("logs/run.jsonl"),
        "orders": Path("logs/orders.jsonl"),
        "exit": Path("logs/exit.jsonl"),
        "gate": Path("logs/gate.jsonl"),
        "system": Path("logs/system.jsonl"),
        "signal_history": Path("state/signal_history.jsonl"),
    }
    
    for name, path in log_files.items():
        status = count_jsonl_entries(path, max_age_minutes=60)
        audit_results["logs"][name] = status
        if status["exists"]:
            print(f"  {name}: {status['total']} total, {status['recent']} recent (last 60min)")
            if status["recent"] == 0 and status["total"] > 0:
                audit_results["issues"].append(f"Log has no recent entries: {name}")
        else:
            print(f"  {name}: FILE MISSING")
            audit_results["issues"].append(f"Log file missing: {name}")
    
    print()
    
    # 4. Check Cache Data
    print("4. CHECKING CACHE DATA...")
    print("-" * 80)
    
    cache_path = Path("data/uw_flow_cache.json")
    if cache_path.exists():
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            symbol_keys = [k for k in cache_data.keys() if not k.startswith("_")]
            metadata = cache_data.get("_metadata", {})
            last_update = metadata.get("last_update")
            
            audit_results["cache"] = {
                "exists": True,
                "symbol_count": len(symbol_keys),
                "symbols": symbol_keys[:10],  # First 10
                "last_update": last_update
            }
            
            print(f"  Cache has {len(symbol_keys)} symbols")
            if len(symbol_keys) > 0:
                print(f"  Sample symbols: {', '.join(symbol_keys[:5])}")
            else:
                audit_results["issues"].append("Cache has no symbol data")
            
            if last_update:
                try:
                    if isinstance(last_update, (int, float)):
                        update_time = datetime.fromtimestamp(last_update, tz=timezone.utc)
                    else:
                        update_time = datetime.fromisoformat(str(last_update).replace("Z", "+00:00"))
                    age_minutes = (datetime.now(timezone.utc) - update_time).total_seconds() / 60.0
                    print(f"  Last update: {age_minutes:.1f} minutes ago")
                    if age_minutes > 10:
                        audit_results["issues"].append(f"Cache is stale: {age_minutes:.1f} minutes old")
                except:
                    pass
        except Exception as e:
            audit_results["cache"] = {"exists": True, "error": str(e)}
            audit_results["issues"].append(f"Error reading cache: {e}")
    else:
        audit_results["cache"] = {"exists": False}
        audit_results["issues"].append("Cache file missing")
        print("  Cache file missing")
    
    print()
    
    # 5. Check Recent Activity
    print("5. CHECKING RECENT ACTIVITY...")
    print("-" * 80)
    
    # Check worker debug log
    worker_log = Path("logs/worker_debug.log")
    if worker_log.exists():
        try:
            with open(worker_log, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    print(f"  Last worker activity: {last_line[:100]}")
                    # Check if recent
                    if "run_once()" in last_line or "Worker loop" in last_line:
                        audit_results["state"]["worker_active"] = True
                    else:
                        audit_results["state"]["worker_active"] = False
        except:
            pass
    
    # Check recent attribution entries
    attr_log = Path("logs/attribution.jsonl")
    if attr_log.exists():
        try:
            with open(attr_log, 'r') as f:
                lines = f.readlines()
                recent_trades = []
                now = time.time()
                for line in lines[-20:]:  # Check last 20
                    try:
                        entry = json.loads(line.strip())
                        ts_str = entry.get("ts")
                        if ts_str:
                            if isinstance(ts_str, str):
                                entry_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
                            else:
                                entry_time = ts_str
                            age_minutes = (now - entry_time) / 60.0
                            if age_minutes <= 120:  # Last 2 hours
                                recent_trades.append({
                                    "symbol": entry.get("symbol"),
                                    "age_minutes": round(age_minutes, 1),
                                    "pnl_pct": entry.get("pnl_pct")
                                })
                    except:
                        pass
                
                if recent_trades:
                    print(f"  Recent trades (last 2h): {len(recent_trades)}")
                    for trade in recent_trades[:5]:
                        print(f"    {trade['symbol']}: {trade['age_minutes']:.1f} min ago, P&L: {trade.get('pnl_pct', 'N/A')}%")
                    audit_results["state"]["recent_trades"] = recent_trades
                else:
                    print("  No recent trades in last 2 hours")
                    audit_results["issues"].append("No recent trades in attribution log")
        except Exception as e:
            print(f"  Error checking attribution: {e}")
    
    print()
    
    # 6. Check System Health
    print("6. CHECKING SYSTEM HEALTH...")
    print("-" * 80)
    
    # Check disk space
    stdout, _, _ = run_command("df -h /root/stock-bot | tail -1")
    if stdout:
        print(f"  Disk space: {stdout.strip()}")
    
    # Check memory
    stdout, _, _ = run_command("free -h | grep Mem")
    if stdout:
        print(f"  Memory: {stdout.strip()}")
    
    print()
    
    # Summary
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total Issues Found: {len(audit_results['issues'])}")
    if audit_results["issues"]:
        print("\nIssues:")
        for i, issue in enumerate(audit_results["issues"], 1):
            print(f"  {i}. {issue}")
    else:
        print("\n✓ No issues found - system appears healthy")
    
    return audit_results

def main():
    """Main entry point"""
    try:
        results = audit_system()
        
        # Save results
        output_path = Path("reports/droplet_audit_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")
        return 0 if len(results["issues"]) == 0 else 1
    except Exception as e:
        print(f"\nERROR: Audit failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
