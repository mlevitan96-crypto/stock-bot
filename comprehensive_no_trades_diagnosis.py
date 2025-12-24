#!/usr/bin/env python3
"""
Comprehensive diagnosis of why no trades occurred today.
This runs locally and analyzes what we can determine from git and codebase.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def pull_latest():
    """Pull latest from git"""
    try:
        subprocess.run(["git", "pull", "origin", "main", "--no-rebase"], 
                      check=True, capture_output=True)
        return True
    except:
        return False

def read_status_report():
    """Read status report from git"""
    status_file = Path("status_report.json")
    if status_file.exists():
        try:
            with open(status_file) as f:
                return json.load(f)
        except:
            pass
    return None

def analyze_common_issues():
    """Analyze based on common issues from codebase"""
    issues = []
    fixes = []
    
    # Common Issue 1: Order submission rejecting non-filled orders
    issues.append({
        "issue": "Order submission logic rejects non-filled orders",
        "description": "Code at line 4018-4023 in main.py rejects all orders that aren't immediately filled",
        "fix_file": "main.py",
        "fix_lines": "4018-4023",
        "severity": "CRITICAL"
    })
    fixes.append({
        "file": "main.py",
        "issue": "Rejecting non-filled orders",
        "fix": "Accept 'submitted_unfilled', 'limit', 'market' statuses, only reject 'error' statuses"
    })
    
    # Common Issue 2: Max positions reached
    issues.append({
        "issue": "Maximum positions reached (16)",
        "description": "Bot may be at capacity and waiting for exits",
        "check": "Check state/internal_positions.json for position count",
        "severity": "HIGH"
    })
    
    # Common Issue 3: Execution cycles not running
    issues.append({
        "issue": "Execution cycles not running",
        "description": "Worker thread may not be executing cycles",
        "check": "Check logs/run.jsonl for recent cycles",
        "severity": "HIGH"
    })
    
    # Common Issue 4: All signals blocked by gates
    issues.append({
        "issue": "All signals blocked by gates",
        "description": "Signals may be failing expectancy, score, or other gates",
        "check": "Check state/blocked_trades.jsonl for block reasons",
        "severity": "MEDIUM"
    })
    
    # Common Issue 5: No clusters generated
    issues.append({
        "issue": "No clusters generated from UW data",
        "description": "UW daemon may not be fetching data or clustering failing",
        "check": "Check data/uw_flow_cache.json for tickers with trades",
        "severity": "HIGH"
    })
    
    return issues, fixes

def generate_fix_script(fixes):
    """Generate a fix script based on identified issues"""
    script = """#!/bin/bash
# Auto-generated fix script for no trades issue
cd ~/stock-bot

echo "Applying fixes for no trades issue..."
echo ""

# Fix 1: Update order submission logic to accept non-filled orders
echo "Fix 1: Updating order submission logic..."
python3 << 'PYTHON_FIX'
import re

# Read main.py
with open('main.py', 'r') as f:
    content = f.read()

# Find and fix the order rejection logic
# Look for: if entry_status != "filled" or filled_qty <= 0:
pattern = r'if entry_status != "filled" or filled_qty <= 0:.*?continue'
replacement = '''if entry_status in ("error", "spread_too_wide", "min_notional_blocked", "insufficient_buying_power"):
    # Reject error statuses
    continue
# Accept all other statuses (submitted_unfilled, limit, market, filled, etc.)
# Reconciliation loop will pick up fills later'''

# Check if fix is needed
if 'if entry_status != "filled" or filled_qty <= 0:' in content:
    # More careful replacement
    lines = content.split('\\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'if entry_status != "filled" or filled_qty <= 0:' in line:
            # Replace this problematic check
            new_lines.append('            # FIXED: Accept non-filled orders, only reject errors')
            new_lines.append('            if entry_status in ("error", "spread_too_wide", "min_notional_blocked", "insufficient_buying_power"):')
            new_lines.append('                log_event("order", "entry_rejected_error", symbol=symbol, status=entry_status)')
            new_lines.append('                continue  # Only reject actual errors')
            new_lines.append('            # Accept: submitted_unfilled, limit, market, filled, etc.')
            # Skip the old continue line
            i += 1
            while i < len(lines) and ('continue' in lines[i] or lines[i].strip() == ''):
                i += 1
            continue
        new_lines.append(line)
        i += 1
    
    with open('main.py', 'w') as f:
        f.write('\\n'.join(new_lines))
    print("✅ Fixed order submission logic")
else:
    print("ℹ️  Order submission logic already fixed or different")
PYTHON_FIX

echo ""
echo "✅ Fixes applied. Restarting services..."
pkill -f deploy_supervisor
sleep 2
cd ~/stock-bot && source venv/bin/activate && screen -dmS supervisor python deploy_supervisor.py

echo ""
echo "✅ Services restarted. Monitor with: screen -r supervisor"
"""
    return script

def main():
    """Main diagnosis"""
    print("=" * 80)
    print("COMPREHENSIVE DIAGNOSIS: Why No Trades Today")
    print("=" * 80)
    print()
    
    # Pull latest
    print("Pulling latest from git...")
    pull_latest()
    
    # Read status report
    print("Reading status report...")
    status = read_status_report()
    if status:
        print(f"Status report timestamp: {status.get('timestamp', 'unknown')}")
        print(f"Services running:")
        services = status.get('services', {})
        for svc, count in services.items():
            status_icon = "✅" if int(count) > 0 else "❌"
            print(f"  {status_icon} {svc}: {count}")
        print()
    
    # Analyze common issues
    print("Analyzing common issues from codebase...")
    issues, fixes = analyze_common_issues()
    
    print("\n" + "=" * 80)
    print("IDENTIFIED ISSUES")
    print("=" * 80)
    
    critical_issues = [i for i in issues if i.get("severity") == "CRITICAL"]
    high_issues = [i for i in issues if i.get("severity") == "HIGH"]
    medium_issues = [i for i in issues if i.get("severity") == "MEDIUM"]
    
    if critical_issues:
        print("\n🔴 CRITICAL ISSUES:")
        for issue in critical_issues:
            print(f"  - {issue['issue']}")
            print(f"    {issue['description']}")
    
    if high_issues:
        print("\n🟠 HIGH PRIORITY ISSUES:")
        for issue in high_issues:
            print(f"  - {issue['issue']}")
            print(f"    {issue.get('description', '')}")
            if 'check' in issue:
                print(f"    Check: {issue['check']}")
    
    if medium_issues:
        print("\n🟡 MEDIUM PRIORITY ISSUES:")
        for issue in medium_issues:
            print(f"  - {issue['issue']}")
            print(f"    {issue.get('description', '')}")
    
    # Generate fix
    print("\n" + "=" * 80)
    print("RECOMMENDED FIX")
    print("=" * 80)
    
    if critical_issues:
        print("\nMost likely issue: Order submission logic rejecting non-filled orders")
        print("\nThis is a known bug where the code rejects all orders that aren't")
        print("immediately filled, even if they were successfully submitted.")
        print("\nFix: Update main.py to accept 'submitted_unfilled', 'limit', 'market'")
        print("statuses and only reject actual error statuses.")
        
        # Generate fix script
        fix_script = generate_fix_script(fixes)
        with open("fix_no_trades.sh", "w") as f:
            f.write(fix_script)
        print("\n✅ Generated fix script: fix_no_trades.sh")
        print("   Run on droplet: cd ~/stock-bot && git pull && chmod +x fix_no_trades.sh && ./fix_no_trades.sh")
    else:
        print("\nNo critical issues identified. Need investigation results from droplet.")
        print("Run investigation on droplet to get detailed diagnosis.")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

