#!/usr/bin/env python3
"""
Comprehensive Trading Bot Diagnostic
=====================================
Runs a full diagnostic of the stock-bot to verify all trading activity is working correctly:
- Signal capture and processing
- Exit criteria evaluation
- Logging systems
- Trade execution flow

Outputs a checklist format with issues and proposed fixes.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_check(description: str, status: bool, details: str = ""):
    """Print a check result with color coding."""
    try:
        status_str = f"{Colors.GREEN}[PASS]{Colors.RESET}" if status else f"{Colors.RED}[FAIL]{Colors.RESET}"
        print(f"  {status_str} {description}")
        if details:
            print(f"      {Colors.BLUE}-> {details}{Colors.RESET}")
    except UnicodeEncodeError:
        # Fallback for Windows console
        status_str = "[PASS]" if status else "[FAIL]"
        print(f"  {status_str} {description}")
        if details:
            print(f"      -> {details}")

def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def check_file_exists(path: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists and is readable."""
    if not path.exists():
        return False, f"File not found: {path}"
    if not path.is_file():
        return False, f"Path exists but is not a file: {path}"
    try:
        with open(path, 'r') as f:
            f.read(1)
        return True, f"File exists and readable: {path}"
    except Exception as e:
        return False, f"File exists but not readable: {e}"

def check_json_file(path: Path, description: str) -> Tuple[bool, str, Any]:
    """Check if a JSON file exists and is valid."""
    exists, msg = check_file_exists(path, description)
    if not exists:
        return False, msg, None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return True, f"Valid JSON file: {path}", data
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}", None
    except Exception as e:
        return False, f"Error reading JSON: {e}", None

def check_jsonl_file(path: Path, description: str, min_entries: int = 0) -> Tuple[bool, str, List[Dict]]:
    """Check if a JSONL file exists and has entries."""
    exists, msg = check_file_exists(path, description)
    if not exists:
        return False, msg, []
    try:
        entries = []
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        if min_entries > 0 and len(entries) < min_entries:
            return False, f"File has {len(entries)} entries, expected at least {min_entries}", entries
        return True, f"Valid JSONL file with {len(entries)} entries", entries
    except Exception as e:
        return False, f"Error reading JSONL: {e}", []

def check_recent_entries(entries: List[Dict], max_age_minutes: int = 60) -> Tuple[bool, str]:
    """Check if entries are recent."""
    if not entries:
        return False, "No entries found"
    
    now = datetime.now(timezone.utc)
    recent_count = 0
    
    for entry in entries[-10:]:  # Check last 10 entries
        ts_str = entry.get("ts") or entry.get("_ts") or entry.get("timestamp")
        if not ts_str:
            continue
        
        try:
            if isinstance(ts_str, (int, float)):
                entry_time = datetime.fromtimestamp(ts_str, tz=timezone.utc)
            else:
                entry_time = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                if entry_time.tzinfo is None:
                    entry_time = entry_time.replace(tzinfo=timezone.utc)
            
            age_minutes = (now - entry_time).total_seconds() / 60.0
            if age_minutes <= max_age_minutes:
                recent_count += 1
        except Exception:
            continue
    
    if recent_count == 0:
        return False, f"No entries in last {max_age_minutes} minutes"
    return True, f"{recent_count} recent entries in last {max_age_minutes} minutes"

def diagnose_signal_capture() -> Dict[str, Any]:
    """Diagnose signal capture mechanisms."""
    print_section("1. SIGNAL CAPTURE DIAGNOSTIC")
    
    results = {
        "uw_daemon_running": False,
        "cache_file_exists": False,
        "cache_has_data": False,
        "cache_recent": False,
        "enrichment_working": False,
        "issues": []
    }
    
    # Check UW Flow Daemon process (cross-platform)
    try:
        import subprocess
        import platform
        if platform.system() == "Windows":
            # Use tasklist on Windows
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe"],
                capture_output=True,
                text=True
            )
            # Check if uw_flow_daemon.py is in process list (basic check)
            daemon_running = "uw_flow_daemon" in str(result.stdout).lower() or Path("state/uw_flow_daemon.lock").exists()
        else:
            # Use pgrep on Unix
            result = subprocess.run(
                ["pgrep", "-f", "uw_flow_daemon.py"],
                capture_output=True,
                text=True
            )
            daemon_running = result.returncode == 0
        
        results["uw_daemon_running"] = daemon_running
        print_check("UW Flow Daemon Running", daemon_running, 
                   "Process found" if daemon_running else "Process not found (check lock file)")
        if not daemon_running:
            results["issues"].append("UW Flow Daemon is not running - signals won't be captured")
    except Exception as e:
        # Fallback: check lock file
        lock_file = Path("state/uw_flow_daemon.lock")
        daemon_running = lock_file.exists()
        results["uw_daemon_running"] = daemon_running
        print_check("UW Flow Daemon Running (lock file check)", daemon_running,
                   "Lock file exists" if daemon_running else "Lock file not found")
        if not daemon_running:
            results["issues"].append("UW Flow Daemon is not running - signals won't be captured")
    
    # Check cache file
    cache_path = Path("data/uw_flow_cache.json")
    exists, msg, cache_data = check_json_file(cache_path, "UW Flow Cache")
    results["cache_file_exists"] = exists
    print_check("Cache File Exists", exists, msg)
    
    if exists and cache_data:
        # Check cache has symbol data (not just metadata)
        symbol_keys = [k for k in cache_data.keys() if not k.startswith("_")]
        results["cache_has_data"] = len(symbol_keys) > 0
        print_check("Cache Has Symbol Data", results["cache_has_data"], 
                   f"{len(symbol_keys)} symbols in cache")
        
        if len(symbol_keys) == 0:
            results["issues"].append("Cache file exists but has no symbol data")
        
        # Check cache freshness
        metadata = cache_data.get("_metadata", {})
        last_update = metadata.get("last_update")
        if last_update:
            try:
                if isinstance(last_update, (int, float)):
                    update_time = datetime.fromtimestamp(last_update, tz=timezone.utc)
                else:
                    update_time = datetime.fromisoformat(str(last_update).replace("Z", "+00:00"))
                    if update_time.tzinfo is None:
                        update_time = update_time.replace(tzinfo=timezone.utc)
                
                age_minutes = (datetime.now(timezone.utc) - update_time).total_seconds() / 60.0
                results["cache_recent"] = age_minutes < 10  # Should update every 60s
                print_check("Cache Is Recent", results["cache_recent"], 
                          f"Last update: {age_minutes:.1f} minutes ago")
                if not results["cache_recent"]:
                    results["issues"].append(f"Cache is stale ({age_minutes:.1f} minutes old)")
            except Exception as e:
                print_check("Cache Freshness Check", False, f"Error: {e}")
        else:
            print_check("Cache Has Metadata", False, "No _metadata.last_update found")
            results["issues"].append("Cache missing update timestamp")
    else:
        results["issues"].append("Cache file missing or invalid")
    
    # Check enrichment module
    try:
        import uw_enrichment_v2
        results["enrichment_working"] = True
        print_check("Enrichment Module Available", True, "uw_enrichment_v2 imported successfully")
    except ImportError as e:
        results["enrichment_working"] = False
        print_check("Enrichment Module Available", False, f"Import error: {e}")
        results["issues"].append(f"Enrichment module not available: {e}")
    
    return results

def diagnose_signal_processing() -> Dict[str, Any]:
    """Diagnose signal processing and scoring."""
    print_section("2. SIGNAL PROCESSING DIAGNOSTIC")
    
    results = {
        "composite_scoring_available": False,
        "composite_scoring_working": False,
        "signals_logged": False,
        "recent_signals": False,
        "gate_logging_working": False,
        "issues": []
    }
    
    # Check composite scoring module
    try:
        import uw_composite_v2
        results["composite_scoring_available"] = True
        print_check("Composite Scoring Module Available", True, "uw_composite_v2 imported")
        
        # Try a test calculation - check available functions
        try:
            # Check what functions are available
            if hasattr(uw_composite_v2, "compute_composite_score_v2"):
                func = uw_composite_v2.compute_composite_score_v2
            elif hasattr(uw_composite_v2, "compute_composite_score_v3"):
                func = uw_composite_v2.compute_composite_score_v3
            elif hasattr(uw_composite_v2, "compute_composite_score"):
                func = uw_composite_v2.compute_composite_score
            else:
                raise AttributeError("No composite scoring function found")
            
            test_enriched = {"sentiment": "BULLISH", "conviction": 0.5}
            result = func("AAPL", test_enriched, "mixed")
            # Result might be dict or float
            if isinstance(result, dict):
                score = result.get("score", result.get("composite_score", 0.0))
            else:
                score = float(result) if result else 0.0
            results["composite_scoring_working"] = True
            print_check("Composite Scoring Functional", True, f"Test score: {score:.2f}")
        except Exception as e:
            results["composite_scoring_working"] = False
            print_check("Composite Scoring Functional", False, f"Test failed: {e}")
            results["issues"].append(f"Composite scoring test failed: {e}")
    except ImportError as e:
        print_check("Composite Scoring Module Available", False, f"Import error: {e}")
        results["issues"].append(f"Composite scoring module not available: {e}")
    
    # Check signal history logging
    signal_history_path = Path("state/signal_history.jsonl")
    exists, msg, entries = check_jsonl_file(signal_history_path, "Signal History Log", min_entries=0)
    results["signals_logged"] = exists
    print_check("Signal History Logging", exists, msg)
    
    if exists and entries:
        recent, recent_msg = check_recent_entries(entries, max_age_minutes=60)
        results["recent_signals"] = recent
        print_check("Recent Signal Logs", recent, recent_msg)
        if not recent:
            results["issues"].append("No recent signal logs (last 60 minutes)")
    else:
        results["issues"].append("Signal history log missing or empty")
    
    # Check gate logging
    gate_log_path = Path("logs/gate.jsonl")
    exists, msg, entries = check_jsonl_file(gate_log_path, "Gate Event Log", min_entries=0)
    results["gate_logging_working"] = exists
    print_check("Gate Event Logging", exists, msg)
    
    if exists and entries:
        recent, recent_msg = check_recent_entries(entries, max_age_minutes=60)
        print_check("Recent Gate Events", recent, recent_msg)
    
    # Check attribution logging
    attribution_path = CacheFiles.UW_ATTRIBUTION
    exists, msg, entries = check_jsonl_file(attribution_path, "UW Attribution Log", min_entries=0)
    print_check("UW Attribution Logging", exists, msg)
    
    return results

def diagnose_exit_criteria() -> Dict[str, Any]:
    """Diagnose exit criteria evaluation."""
    print_section("3. EXIT CRITERIA DIAGNOSTIC")
    
    results = {
        "evaluate_exits_function": False,
        "exit_logging_working": False,
        "recent_exit_logs": False,
        "exit_signals_captured": False,
        "structural_exit_available": False,
        "issues": []
    }
    
    # Check evaluate_exits function exists - just check if method exists in class
    try:
        from main import AlpacaExecutor
        results["evaluate_exits_function"] = hasattr(AlpacaExecutor, "evaluate_exits")
        print_check("evaluate_exits() Function Exists", results["evaluate_exits_function"], 
                   "AlpacaExecutor.evaluate_exits found")
        if not results["evaluate_exits_function"]:
            results["issues"].append("evaluate_exits() function not found in AlpacaExecutor")
    except Exception as e:
        print_check("evaluate_exits() Function Check", False, f"Error: {e}")
        results["issues"].append(f"Could not check evaluate_exits: {e}")
    
    # Check exit logging
    exit_log_path = Path("logs/exit.jsonl")
    exists, msg, entries = check_jsonl_file(exit_log_path, "Exit Event Log", min_entries=0)
    results["exit_logging_working"] = exists
    print_check("Exit Event Logging", exists, msg)
    
    if exists and entries:
        recent, recent_msg = check_recent_entries(entries, max_age_minutes=60)
        results["recent_exit_logs"] = recent
        print_check("Recent Exit Logs", recent, recent_msg)
        
        # Check exit signals are captured
        if entries:
            last_exit = entries[-1]
            has_reason = "reason" in last_exit or "close_reason" in last_exit
            has_signals = "exit_signals" in last_exit or "signals" in last_exit
            results["exit_signals_captured"] = has_reason or has_signals
            print_check("Exit Signals Captured", results["exit_signals_captured"],
                       "Exit logs contain reason/signals" if results["exit_signals_captured"] else "Missing exit reason/signals")
    else:
        results["issues"].append("Exit event log missing or empty")
    
    # Check structural exit module
    try:
        from structural_intelligence.structural_exit import StructuralExit
        results["structural_exit_available"] = True
        print_check("Structural Exit Module Available", True, "StructuralExit imported")
    except ImportError:
        results["structural_exit_available"] = False
        print_check("Structural Exit Module Available", False, "Module not found (optional)")
    
    # Check exit attribution logging
    attribution_path = Path("logs/attribution.jsonl")
    exists, msg, entries = check_jsonl_file(attribution_path, "Exit Attribution Log", min_entries=0)
    print_check("Exit Attribution Logging", exists, msg)
    
    if exists and entries:
        # Check for exit entries
        exit_entries = [e for e in entries if e.get("type") == "attribution" and e.get("context", {}).get("close_reason")]
        print_check("Exit Attribution Entries", len(exit_entries) > 0, 
                   f"{len(exit_entries)} exit attribution entries found")
    
    return results

def diagnose_logging_systems() -> Dict[str, Any]:
    """Diagnose all logging systems."""
    print_section("4. LOGGING SYSTEMS DIAGNOSTIC")
    
    results = {
        "log_functions_available": False,
        "log_directories_exist": False,
        "attribution_logging": False,
        "order_logging": False,
        "run_cycle_logging": False,
        "issues": []
    }
    
    # Check logging functions
    try:
        from main import log_event, jsonl_write, log_attribution, log_exit_attribution
        results["log_functions_available"] = True
        print_check("Logging Functions Available", True, 
                   "log_event, jsonl_write, log_attribution, log_exit_attribution found")
    except ImportError as e:
        print_check("Logging Functions Available", False, f"Import error: {e}")
        results["issues"].append(f"Logging functions not available: {e}")
    
    # Check log directories
    log_dir = Path("logs")
    data_dir = Path("data")
    state_dir = Path("state")
    
    dirs_exist = log_dir.exists() and data_dir.exists() and state_dir.exists()
    results["log_directories_exist"] = dirs_exist
    print_check("Log Directories Exist", dirs_exist, 
               f"logs: {log_dir.exists()}, data: {data_dir.exists()}, state: {state_dir.exists()}")
    
    if not dirs_exist:
        results["issues"].append("Required log directories missing")
    
    # Check attribution logging
    attribution_path = Path("logs/attribution.jsonl")
    exists, msg, entries = check_jsonl_file(attribution_path, "Attribution Log", min_entries=0)
    results["attribution_logging"] = exists
    print_check("Attribution Logging Active", exists, msg)
    
    if exists and entries:
        recent, recent_msg = check_recent_entries(entries, max_age_minutes=120)
        print_check("Recent Attribution Logs", recent, recent_msg)
    
    # Check order logging
    order_log_path = Path("logs/orders.jsonl")
    exists, msg, entries = check_jsonl_file(order_log_path, "Order Log", min_entries=0)
    results["order_logging"] = exists
    print_check("Order Logging Active", exists, msg)
    
    if exists and entries:
        recent, recent_msg = check_recent_entries(entries, max_age_minutes=120)
        print_check("Recent Order Logs", recent, recent_msg)
    
    # Check run cycle logging
    run_log_path = Path("logs/run.jsonl")
    exists, msg, entries = check_jsonl_file(run_log_path, "Run Cycle Log", min_entries=0)
    results["run_cycle_logging"] = exists
    print_check("Run Cycle Logging Active", exists, msg)
    
    if exists and entries:
        recent, recent_msg = check_recent_entries(entries, max_age_minutes=60)
        print_check("Recent Run Cycles", recent, recent_msg)
        if not recent:
            results["issues"].append("No recent run cycles (bot may not be running)")
    
    # Check system event logging
    system_log_path = Path("logs/system.jsonl")
    exists, msg, entries = check_jsonl_file(system_log_path, "System Event Log", min_entries=0)
    print_check("System Event Logging", exists, msg)
    
    return results

def diagnose_trade_execution() -> Dict[str, Any]:
    """Diagnose trade execution flow."""
    print_section("5. TRADE EXECUTION DIAGNOSTIC")
    
    results = {
        "executor_available": False,
        "decide_and_execute_function": False,
        "order_submission_working": False,
        "position_tracking": False,
        "issues": []
    }
    
    # Check executor class
    try:
        from main import AlpacaExecutor, StrategyEngine
        results["executor_available"] = True
        print_check("AlpacaExecutor Available", True, "Class imported successfully")
        
        # Check decide_and_execute - just check if function exists in class
        results["decide_and_execute_function"] = hasattr(StrategyEngine, "decide_and_execute")
        print_check("decide_and_execute() Function", results["decide_and_execute_function"],
                   "StrategyEngine.decide_and_execute found")
        if not results["decide_and_execute_function"]:
            results["issues"].append("decide_and_execute() function not found")
    except Exception as e:
        print_check("Executor Check", False, f"Error: {e}")
        results["issues"].append(f"Could not check executor: {e}")
    
    # Check position metadata
    position_metadata_path = Path("state/position_metadata.json")
    exists, msg, metadata = check_json_file(position_metadata_path, "Position Metadata")
    results["position_tracking"] = exists
    print_check("Position Metadata Tracking", exists, msg)
    
    if exists and metadata:
        position_count = len([k for k in metadata.keys() if not k.startswith("_")])
        print_check("Active Positions Tracked", position_count > 0, 
                   f"{position_count} positions in metadata")
    
    # Check order submission (via logs)
    order_log_path = Path("logs/orders.jsonl")
    exists, msg, entries = check_jsonl_file(order_log_path, "Order Submission Log", min_entries=0)
    results["order_submission_working"] = exists
    print_check("Order Submission Logging", exists, msg)
    
    if exists and entries:
        recent, recent_msg = check_recent_entries(entries, max_age_minutes=120)
        print_check("Recent Order Submissions", recent, recent_msg)
        if not recent:
            results["issues"].append("No recent order submissions")
    
    return results

def generate_checklist_report(all_results: Dict[str, Dict[str, Any]]) -> str:
    """Generate a comprehensive checklist report."""
    print_section("DIAGNOSTIC SUMMARY & CHECKLIST")
    
    report = []
    report.append("# Stock-Bot Trading Flow Diagnostic Checklist\n")
    report.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}\n\n")
    
    # Overall status
    total_checks = 0
    passed_checks = 0
    
    for section_name, results in all_results.items():
        report.append(f"## {section_name.upper().replace('_', ' ')}\n")
        
        for key, value in results.items():
            if key == "issues":
                continue
            if isinstance(value, bool):
                total_checks += 1
                if value:
                    passed_checks += 1
                    status = "[PASS]"
                else:
                    status = "[FAIL]"
                report.append(f"- {status} {key.replace('_', ' ').title()}\n")
        
        # List issues
        issues = results.get("issues", [])
        if issues:
            report.append(f"\n### Issues Found:\n")
            for issue in issues:
                report.append(f"- [ISSUE] {issue}\n")
        report.append("\n")
    
    # Overall summary
    report.append("## Overall Status\n\n")
    report.append(f"- **Total Checks:** {total_checks}\n")
    report.append(f"- **Passed:** {passed_checks}\n")
    report.append(f"- **Failed:** {total_checks - passed_checks}\n")
    report.append(f"- **Success Rate:** {(passed_checks/total_checks*100):.1f}%\n\n")
    
    # Proposed fixes
    all_issues = []
    for results in all_results.values():
        all_issues.extend(results.get("issues", []))
    
    if all_issues:
        report.append("## Proposed Fixes\n\n")
        for i, issue in enumerate(all_issues, 1):
            report.append(f"### Issue {i}: {issue}\n\n")
            
            # Suggest fixes based on issue type
            if "daemon" in issue.lower() or "process" in issue.lower():
                report.append("**Proposed Fix:**\n")
                report.append("1. Check if `uw_flow_daemon.py` is running: `ps aux | grep uw_flow_daemon` (Linux) or check Task Manager (Windows)\n")
                report.append("2. Restart the trading bot service: `systemctl restart trading-bot.service` (Linux) or restart manually (Windows)\n")
                report.append("3. Verify daemon starts in supervisor logs\n")
                report.append("4. Check lock file: `state/uw_flow_daemon.lock`\n\n")
            
            elif "cache" in issue.lower():
                report.append("**Proposed Fix:**\n")
                report.append("1. Check UW API credentials in `.env` file\n")
                report.append("2. Verify UW daemon is running and polling API\n")
                report.append("3. Check `data/uw_flow_cache.json` for data\n")
                report.append("4. Review daemon logs: `tail -f logs/uw_flow_daemon.jsonl`\n\n")
            
            elif "logging" in issue.lower() or "log" in issue.lower():
                report.append("**Proposed Fix:**\n")
                report.append("1. Verify log directories exist: `logs/`, `data/`, `state/`\n")
                report.append("2. Check file permissions on log directories\n")
                report.append("3. Review recent log entries for errors\n")
                report.append("4. Ensure logging functions are being called in code\n\n")
            
            elif "exit" in issue.lower():
                report.append("**Proposed Fix:**\n")
                report.append("1. Verify `evaluate_exits()` is called in `run_once()`\n")
                report.append("2. Check exit criteria thresholds are set correctly\n")
                report.append("3. Review exit logs: `tail -f logs/exit.jsonl`\n")
                report.append("4. Ensure positions exist to evaluate\n\n")
            
            elif "signal" in issue.lower():
                report.append("**Proposed Fix:**\n")
                report.append("1. Check signal capture: UW cache has data\n")
                report.append("2. Verify composite scoring is working\n")
                report.append("3. Review signal logs: `tail -f state/signal_history.jsonl`\n")
                report.append("4. Check gate thresholds aren't too high\n\n")
            
            else:
                report.append("**Proposed Fix:**\n")
                report.append("- Review error logs and code implementation\n")
                report.append("- Check related components for issues\n\n")
    
    return "".join(report)

def main():
    """Run comprehensive diagnostic."""
    print(f"\n{Colors.BOLD}Stock-Bot Comprehensive Trading Diagnostic{Colors.RESET}\n")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}\n")
    
    all_results = {}
    
    # Run all diagnostics
    all_results["Signal Capture"] = diagnose_signal_capture()
    all_results["Signal Processing"] = diagnose_signal_processing()
    all_results["Exit Criteria"] = diagnose_exit_criteria()
    all_results["Logging Systems"] = diagnose_logging_systems()
    all_results["Trade Execution"] = diagnose_trade_execution()
    
    # Generate report
    report = generate_checklist_report(all_results)
    
    # Save report
    report_path = Path("reports/TRADING_DIAGNOSTIC_CHECKLIST.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n{Colors.GREEN}Diagnostic complete!{Colors.RESET}")
    print(f"Report saved to: {report_path}\n")
    
    # Print summary
    total_issues = sum(len(r.get("issues", [])) for r in all_results.values())
    try:
        if total_issues == 0:
            print(f"{Colors.GREEN}[OK] All systems operational - no issues found!{Colors.RESET}\n")
        else:
            print(f"{Colors.YELLOW}[WARN] Found {total_issues} issue(s) - see report for details{Colors.RESET}\n")
    except UnicodeEncodeError:
        if total_issues == 0:
            print(f"[OK] All systems operational - no issues found!\n")
        else:
            print(f"[WARN] Found {total_issues} issue(s) - see report for details\n")
    
    return 0 if total_issues == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
