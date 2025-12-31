#!/usr/bin/env python3
"""
Harden XAI (Natural Language Auditor) System
============================================
This script identifies and fixes issues with the XAI system to ensure it's robust and reliable.
"""

import sys
sys.path.insert(0, ".")

from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional

def diagnose_xai_issues():
    """Diagnose all potential issues with the XAI system"""
    print("=== XAI System Diagnosis ===\n")
    
    issues = []
    
    # 1. Check if log file exists
    log_file = Path("data/explainable_logs.jsonl")
    if not log_file.exists():
        issues.append("CRITICAL: XAI log file does not exist")
        print("❌ XAI log file missing")
    else:
        print(f"✅ XAI log file exists: {log_file}")
        # Check file permissions
        if not log_file.is_file():
            issues.append("CRITICAL: XAI log file is not a regular file")
        if not log_file.stat().st_size > 0:
            issues.append("WARNING: XAI log file is empty")
    
    # 2. Check for trade entries vs exits
    if log_file.exists():
        entries = []
        exits = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        if rec.get("type") == "trade_entry":
                            entries.append(rec)
                        elif rec.get("type") == "trade_exit":
                            exits.append(rec)
                    except:
                        continue
        
        print(f"\n📊 XAI Log Statistics:")
        print(f"   Trade entries: {len(entries)}")
        print(f"   Trade exits: {len(exits)}")
        
        if len(entries) == 0 and len(exits) > 0:
            issues.append("CRITICAL: No trade entries logged, but exits exist - entries not being logged!")
        elif len(entries) < len(exits) * 0.5:
            issues.append("WARNING: Very few trade entries compared to exits - possible logging issue")
    
    # 3. Check for TEST symbols
    if log_file.exists():
        test_symbols = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        symbol = str(rec.get("symbol", "")).upper()
                        if "TEST" in symbol:
                            test_symbols.append(rec)
                    except:
                        continue
        
        if test_symbols:
            issues.append(f"WARNING: Found {len(test_symbols)} entries with TEST symbols")
            print(f"⚠️  Found {len(test_symbols)} TEST symbol entries")
        else:
            print("✅ No TEST symbols found")
    
    # 4. Check for missing required fields
    if log_file.exists():
        missing_fields = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if line.strip():
                    try:
                        rec = json.loads(line)
                        if rec.get("type") in ("trade_entry", "trade_exit"):
                            if not rec.get("symbol"):
                                missing_fields.append(f"Line {i+1}: Missing symbol")
                            if not rec.get("why"):
                                missing_fields.append(f"Line {i+1}: Missing 'why' explanation")
                            if not rec.get("timestamp"):
                                missing_fields.append(f"Line {i+1}: Missing timestamp")
                    except:
                        continue
        
        if missing_fields:
            issues.append(f"ERROR: Missing required fields: {missing_fields[:5]}")
            print(f"❌ Found {len(missing_fields)} entries with missing fields")
        else:
            print("✅ All entries have required fields")
    
    # 5. Check dashboard endpoint
    print("\n🔍 Checking dashboard endpoint...")
    try:
        import requests
        response = requests.get("http://localhost:5000/api/xai/auditor", timeout=5)
        if response.status_code == 200:
            data = response.json()
            trades = data.get("trades", [])
            weights = data.get("weights", [])
            print(f"✅ Dashboard endpoint working: {len(trades)} trades, {len(weights)} weights")
            
            if not trades and log_file.exists():
                issues.append("WARNING: Dashboard endpoint returns no trades despite log file existing")
        else:
            issues.append(f"ERROR: Dashboard endpoint returned status {response.status_code}")
            print(f"❌ Dashboard endpoint error: {response.status_code}")
    except Exception as e:
        issues.append(f"ERROR: Cannot reach dashboard endpoint: {e}")
        print(f"❌ Cannot reach dashboard: {e}")
    
    # Summary
    print(f"\n=== Diagnosis Summary ===")
    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ No issues found!")
    
    return issues

def fix_xai_issues(issues: List[str]):
    """Fix identified issues"""
    print("\n=== Fixing Issues ===\n")
    
    fixes_applied = []
    
    # Fix 1: Create log file if missing
    log_file = Path("data/explainable_logs.jsonl")
    if "XAI log file does not exist" in str(issues):
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.touch()
        fixes_applied.append("Created missing XAI log file")
        print("✅ Created XAI log file")
    
    # Fix 2: Backfill missing trade entries from attribution logs
    if "No trade entries logged" in str(issues) or "Very few trade entries" in str(issues):
        print("🔧 Attempting to backfill trade entries from attribution logs...")
        try:
            from backfill_xai_exits import backfill_entries_from_attribution
            backfill_entries_from_attribution()
            fixes_applied.append("Backfilled trade entries from attribution logs")
            print("✅ Backfilled trade entries")
        except Exception as e:
            print(f"⚠️  Could not backfill: {e}")
    
    return fixes_applied

if __name__ == "__main__":
    issues = diagnose_xai_issues()
    if issues:
        fixes = fix_xai_issues(issues)
        if fixes:
            print(f"\n✅ Applied {len(fixes)} fixes")
        else:
            print("\n⚠️  Some issues require manual intervention")
    else:
        print("\n✅ System is healthy!")
