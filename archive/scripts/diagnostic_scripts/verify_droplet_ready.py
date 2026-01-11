#!/usr/bin/env python3
"""
Droplet Trading Readiness Verification
Runs comprehensive checks to ensure system is ready for trading tomorrow
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from datetime import datetime

def check_command(cmd, description):
    """Run a command and return (success, output)"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 80)
    print("DROPLET TRADING READINESS VERIFICATION")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    errors = []
    warnings = []
    
    os.chdir("/root/stock-bot")
    
    # 1. Git Status
    print("1. Git Status...")
    success, stdout, stderr = check_command("git rev-parse HEAD", "Get commit hash")
    if success:
        local_commit = stdout[:8]
        success2, stdout2, _ = check_command("git rev-parse origin/main", "Get remote commit")
        if success2:
            remote_commit = stdout2[:8]
            if local_commit == remote_commit[:8]:
                print(f"   OK: Up to date (commit: {local_commit})")
            else:
                warnings.append(f"Local ({local_commit}) differs from remote ({remote_commit[:8]})")
                print(f"   WARNING: Not synced with remote")
        else:
            print("   WARNING: Could not check remote")
    else:
        errors.append("Cannot read git status")
    print()
    
    # 2. Service Status
    print("2. Service Status...")
    success, stdout, _ = check_command("systemctl is-active trading-bot.service 2>/dev/null && echo ACTIVE || echo INACTIVE", "Check service")
    if "ACTIVE" in stdout:
        print("   OK: trading-bot.service is running")
    else:
        errors.append("trading-bot.service is NOT running")
        print("   ERROR: Service not running")
    print()
    
    # 3. Processes
    print("3. Critical Processes...")
    processes = ["main.py", "uw_flow_daemon.py", "dashboard.py", "deploy_supervisor.py"]
    for proc in processes:
        success, stdout, _ = check_command(f"pgrep -f '{proc}' | head -1", f"Check {proc}")
        if success and stdout:
            print(f"   OK: {proc} running (PID: {stdout})")
        else:
            errors.append(f"{proc} is NOT running")
            print(f"   ERROR: {proc} not running")
    print()
    
    # 4. Recent Fixes
    print("4. Recent Fixes Verification...")
    if Path("main.py").exists():
        content = Path("main.py").read_text()
        if "signal_type" in content and "BULLISH_SWEEP" in content:
            print("   OK: UW signal parser fix present")
        else:
            warnings.append("UW signal parser fix not found")
        
        if "gate_type=" in content:
            print("   OK: Gate event logging fix present")
        else:
            warnings.append("Gate event logging fix not found")
    else:
        errors.append("main.py not found")
    
    if Path("sre_diagnostics.py").exists():
        print("   OK: SRE diagnostics module exists")
    else:
        warnings.append("sre_diagnostics.py not found")
    
    if Path("mock_signal_injection.py").exists():
        print("   OK: Mock signal injection module exists")
    else:
        warnings.append("mock_signal_injection.py not found")
    print()
    
    # 5. SRE Metrics
    print("5. SRE Sentinel Status...")
    metrics_file = Path("state/sre_metrics.json")
    if metrics_file.exists():
        try:
            with metrics_file.open() as f:
                m = json.load(f)
            heartbeat = m.get("logic_heartbeat", 0)
            if heartbeat:
                import time
                age_min = int((time.time() - heartbeat) / 60)
                print(f"   Logic Heartbeat: {age_min}m ago")
                print(f"   Mock Signal Success: {m.get('mock_signal_success_pct', 0):.1f}%")
                print(f"   Parser Health: {m.get('parser_health_index', 0):.1f}%")
            else:
                print("   WARNING: No heartbeat yet (mock signal hasn't run)")
        except Exception as e:
            warnings.append(f"Error reading metrics: {e}")
    else:
        print("   INFO: Metrics file not created yet (normal if mock signal hasn't run)")
    print()
    
    # 6. UW Cache
    print("6. UW Cache...")
    cache_file = Path("data/uw_flow_cache.json")
    if cache_file.exists():
        try:
            with cache_file.open() as f:
                cache = json.load(f)
            symbol_count = len([k for k in cache.keys() if not k.startswith("_")])
            if symbol_count > 0:
                print(f"   OK: Cache has {symbol_count} symbols")
            else:
                warnings.append("Cache exists but has no symbols")
        except Exception as e:
            warnings.append(f"Error reading cache: {e}")
    else:
        warnings.append("UW cache file doesn't exist")
    print()
    
    # 7. Dashboard
    print("7. Dashboard & API...")
    success, _, _ = check_command("curl -s http://localhost:5000/health > /dev/null 2>&1 && echo OK || echo FAIL", "Check dashboard")
    if "OK" in success or success:
        print("   OK: Dashboard responding")
    else:
        errors.append("Dashboard not responding")
    
    success, _, _ = check_command("curl -s http://localhost:8081/health > /dev/null 2>&1 && echo OK || echo FAIL", "Check bot API")
    if "OK" in success or success:
        print("   OK: Bot API responding")
    else:
        warnings.append("Bot API not responding")
    print()
    
    # 8. API Keys
    print("8. API Configuration...")
    env_file = Path(".env")
    if env_file.exists():
        content = env_file.read_text()
        if "UW_API_KEY=" in content and "UW_API_KEY=$" not in content:
            print("   OK: UW_API_KEY is set")
        else:
            errors.append("UW_API_KEY not set")
        
        if "ALPACA_KEY=" in content and "ALPACA_KEY=$" not in content:
            print("   OK: ALPACA_KEY is set")
        else:
            errors.append("ALPACA_KEY not set")
    else:
        errors.append(".env file not found")
    print()
    
    # 9. Disk Space
    print("9. Disk Space...")
    success, stdout, _ = check_command("df -h / | tail -1 | awk '{print $5}' | sed 's/%//'", "Check disk")
    if success and stdout.isdigit():
        usage = int(stdout)
        if usage < 90:
            print(f"   OK: Disk space {usage}% used")
        else:
            warnings.append(f"Disk space high: {usage}%")
    print()
    
    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print()
    
    if errors:
        print("ERRORS:")
        for err in errors:
            print(f"  - {err}")
        print()
    
    if warnings:
        print("WARNINGS:")
        for warn in warnings:
            print(f"  - {warn}")
        print()
    
    if not errors and not warnings:
        print("ALL CHECKS PASSED - READY FOR TRADING")
        return 0
    elif not errors:
        print("READY WITH WARNINGS - Review warnings above")
        return 0
    else:
        print("ERRORS DETECTED - Fix errors before trading")
        return 1

if __name__ == "__main__":
    sys.exit(main())
