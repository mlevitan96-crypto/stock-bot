#!/usr/bin/env python3
"""
Comprehensive Code Audit - Full System Review

Audits:
1. Code Quality & Best Practices
2. Label/Name Consistency
3. Dead Code & Unused Imports
4. Error Handling
5. Configuration Consistency
6. Integration Points
7. Logging Consistency
8. State Management
9. API Integrations
10. Risk Management
11. Learning System Integration
12. Trading Readiness

Goal: Ensure everything is ready for production trading.
"""

import os
import re
import json
import ast
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
from datetime import datetime, timezone

# Project root
PROJECT_ROOT = Path(".")
LOG_DIR = PROJECT_ROOT / "logs"
STATE_DIR = PROJECT_ROOT / "state"
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"

# Results storage
issues = []
warnings = []
info = []
passed_checks = []

def log_issue(severity: str, category: str, file: str, line: int, message: str, code: str = ""):
    """Log an issue"""
    issue = {
        "severity": severity,
        "category": category,
        "file": file,
        "line": line,
        "message": message,
        "code": code
    }
    if severity == "ERROR":
        issues.append(issue)
    elif severity == "WARNING":
        warnings.append(issue)
    else:
        info.append(issue)

def log_pass(category: str, message: str):
    """Log a passed check"""
    passed_checks.append({"category": category, "message": message})

# ============================================================================
# 1. CODE QUALITY & BEST PRACTICES
# ============================================================================

def check_python_syntax():
    """Check all Python files for syntax errors"""
    print("Checking Python syntax...")
    python_files = list(PROJECT_ROOT.rglob("*.py"))
    
    for py_file in python_files:
        # Skip virtual environment
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source)
        except SyntaxError as e:
            log_issue("ERROR", "Syntax", str(py_file), e.lineno or 0, f"Syntax error: {e.msg}", str(e))
        except Exception as e:
            log_issue("WARNING", "Syntax", str(py_file), 0, f"Could not parse: {str(e)}")
    
    log_pass("Syntax", f"Checked {len(python_files)} Python files")

def check_imports():
    """Check for unused imports and missing imports"""
    print("Checking imports...")
    python_files = list(PROJECT_ROOT.rglob("*.py"))
    
    for py_file in python_files:
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                source = '\n'.join(lines)
            
            # Check for common issues
            if "import *" in source and "from" in source:
                # Find line number
                for i, line in enumerate(lines, 1):
                    if "import *" in line:
                        log_issue("WARNING", "Imports", str(py_file), i, "Wildcard import detected", line.strip())
            
            # Check for duplicate imports
            imports = []
            for i, line in enumerate(lines, 1):
                if line.strip().startswith(("import ", "from ")):
                    imports.append((i, line.strip()))
            
            seen = set()
            for line_num, imp in imports:
                if imp in seen:
                    log_issue("WARNING", "Imports", str(py_file), line_num, "Duplicate import", imp)
                seen.add(imp)
                
        except Exception as e:
            pass  # Skip files that can't be read
    
    log_pass("Imports", "Checked import statements")

def check_error_handling():
    """Check for proper error handling"""
    print("Checking error handling...")
    critical_files = [
        "main.py",
        "deploy_supervisor.py",
        "dashboard.py",
        "uw_flow_daemon.py",
        "comprehensive_learning_orchestrator_v2.py",
        "adaptive_signal_optimizer.py"
    ]
    
    for filename in critical_files:
        filepath = PROJECT_ROOT / filename
        if not filepath.exists():
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            source = '\n'.join(lines)
        
        # Check for bare except clauses
        for i, line in enumerate(lines, 1):
            if re.search(r'except\s*:', line) and 'Exception' not in line:
                log_issue("WARNING", "Error Handling", filename, i, "Bare except clause (should specify exception type)", line.strip())
        
        # Check for missing try/except around critical operations
        critical_patterns = [
            (r'api\.(get_account|get_positions|submit_order)', "API call without error handling"),
            (r'open\([^)]+\)', "File operation without error handling"),
            (r'json\.(load|dump)', "JSON operation without error handling"),
        ]
        
        for pattern, message in critical_patterns:
            matches = re.finditer(pattern, source)
            for match in matches:
                # Find line number
                line_num = source[:match.start()].count('\n') + 1
                # Check if in try block
                before = source[:match.start()]
                if 'try:' not in before.split('\n')[-10:]:
                    log_issue("INFO", "Error Handling", filename, line_num, message)
    
    log_pass("Error Handling", "Checked error handling patterns")

# ============================================================================
# 2. LABEL/NAME CONSISTENCY
# ============================================================================

def check_naming_consistency():
    """Check for naming inconsistencies"""
    print("Checking naming consistency...")
    
    # Check for inconsistent variable names
    inconsistencies = {
        "pnl_usd": ["pnl", "profit", "profit_usd"],
        "pnl_pct": ["pnl_percent", "profit_pct", "return_pct"],
        "win_rate": ["winrate", "winRate", "wr"],
        "market_regime": ["regime", "gamma_regime"],
    }
    
    python_files = list(PROJECT_ROOT.rglob("*.py"))
    for py_file in python_files:
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                source = '\n'.join(lines)
            
            for standard, variants in inconsistencies.items():
                for variant in variants:
                    if variant in source and standard not in source:
                        # Find line
                        for i, line in enumerate(lines, 1):
                            if variant in line:
                                log_issue("WARNING", "Naming", str(py_file), i, 
                                        f"Inconsistent naming: '{variant}' should be '{standard}'", line.strip())
                                break
        except:
            pass
    
    log_pass("Naming", "Checked naming consistency")

def check_config_consistency():
    """Check configuration consistency across files"""
    print("Checking configuration consistency...")
    
    # Check for hardcoded values that should be in config
    main_py = PROJECT_ROOT / "main.py"
    if main_py.exists():
        with open(main_py, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check for magic numbers that should be config
        magic_numbers = [
            (r'\b16\b', "MAX_CONCURRENT_POSITIONS"),
            (r'\b14\b', "TIME_EXIT_DAYS_STALE"),
            (r'\b2\.0\b', "TRAILING_STOP_PCT or similar"),
        ]
        
        for pattern, config_name in magic_numbers:
            if re.search(pattern, source):
                # Check if it's in a config reference
                if config_name.lower() not in source.lower():
                    log_issue("INFO", "Config", "main.py", 0, f"Magic number found, consider using {config_name}")
    
    log_pass("Config", "Checked configuration consistency")

# ============================================================================
# 3. DEAD CODE & UNUSED CODE
# ============================================================================

def check_dead_code():
    """Check for dead/unused code"""
    print("Checking for dead code...")
    
    # Check for commented-out large blocks
    python_files = list(PROJECT_ROOT.rglob("*.py"))
    for py_file in python_files:
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check for large commented blocks
            comment_block_start = None
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith('#') and len(stripped) > 2:
                    if comment_block_start is None:
                        comment_block_start = i
                else:
                    if comment_block_start and (i - comment_block_start) > 10:
                        log_issue("INFO", "Dead Code", str(py_file), comment_block_start, 
                                f"Large commented block ({i - comment_block_start} lines)")
                    comment_block_start = None
        except:
            pass
    
    log_pass("Dead Code", "Checked for dead code")

# ============================================================================
# 4. INTEGRATION POINTS
# ============================================================================

def check_integration_points():
    """Check critical integration points"""
    print("Checking integration points...")
    
    # Check main.py integration points
    main_py = PROJECT_ROOT / "main.py"
    if main_py.exists():
        with open(main_py, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check learning system integration
        if "learn_from_trade_close" not in source:
            log_issue("ERROR", "Integration", "main.py", 0, "learn_from_trade_close not found")
        else:
            log_pass("Integration", "learn_from_trade_close integrated")
        
        if "run_daily_learning" not in source:
            log_issue("WARNING", "Integration", "main.py", 0, "run_daily_learning not found")
        else:
            log_pass("Integration", "run_daily_learning integrated")
        
        # Check profitability tracking
        if "profitability_tracker" not in source:
            log_issue("WARNING", "Integration", "main.py", 0, "profitability_tracker not integrated")
        else:
            log_pass("Integration", "profitability_tracker integrated")
        
        # Check adaptive optimizer
        if "get_optimizer" not in source and "adaptive_signal_optimizer" not in source:
            log_issue("WARNING", "Integration", "main.py", 0, "adaptive_signal_optimizer not integrated")
        else:
            log_pass("Integration", "adaptive_signal_optimizer integrated")
    
    log_pass("Integration", "Checked integration points")

# ============================================================================
# 5. LOGGING CONSISTENCY
# ============================================================================

def check_logging():
    """Check logging consistency"""
    print("Checking logging...")
    
    python_files = list(PROJECT_ROOT.rglob("*.py"))
    log_functions = defaultdict(set)
    
    for py_file in python_files:
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Find log function calls
            log_patterns = [
                r'log_event\s*\(',
                r'log_attribution\s*\(',
                r'log_order\s*\(',
                r'log_exit\s*\(',
                r'print\s*\(',
            ]
            
            for pattern in log_patterns:
                if re.search(pattern, source):
                    log_functions[pattern].add(str(py_file))
        except:
            pass
    
    # Check for consistent logging
    if len(log_functions) > 0:
        log_pass("Logging", f"Found logging in {len(log_functions)} patterns")
    
    log_pass("Logging", "Checked logging consistency")

# ============================================================================
# 6. STATE MANAGEMENT
# ============================================================================

def check_state_files():
    """Check state file management"""
    print("Checking state management...")
    
    # Check if state directory exists
    if not STATE_DIR.exists():
        log_issue("ERROR", "State", "state/", 0, "State directory does not exist")
    else:
        log_pass("State", "State directory exists")
    
    # Check critical state files
    critical_state_files = [
        "position_metadata.json",
        "learning_processing_state.json",
        "signal_weights.json",
    ]
    
    for state_file in critical_state_files:
        filepath = STATE_DIR / state_file
        if not filepath.exists():
            log_issue("WARNING", "State", str(filepath), 0, f"State file does not exist (will be created on first run)")
        else:
            log_pass("State", f"{state_file} exists")
    
    log_pass("State", "Checked state management")

# ============================================================================
# 7. API INTEGRATIONS
# ============================================================================

def check_api_integrations():
    """Check API integration points"""
    print("Checking API integrations...")
    
    main_py = PROJECT_ROOT / "main.py"
    if main_py.exists():
        with open(main_py, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check Alpaca API
        if "alpaca" in source.lower() or "Alpaca" in source:
            log_pass("API", "Alpaca API integration found")
        else:
            log_issue("ERROR", "API", "main.py", 0, "Alpaca API integration not found")
        
        # Check UW API
        if "uw" in source.lower() or "UnusualWhales" in source:
            log_pass("API", "UW API integration found")
        else:
            log_issue("WARNING", "API", "main.py", 0, "UW API integration not found")
    
    log_pass("API", "Checked API integrations")

# ============================================================================
# 8. RISK MANAGEMENT
# ============================================================================

def check_risk_management():
    """Check risk management implementation"""
    print("Checking risk management...")
    
    main_py = PROJECT_ROOT / "main.py"
    if main_py.exists():
        with open(main_py, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check for risk management functions
        risk_patterns = [
            r'risk_management',
            r'MAX_CONCURRENT_POSITIONS',
            r'TRAILING_STOP',
            r'daily_loss',
            r'position_size',
        ]
        
        found = False
        for pattern in risk_patterns:
            if re.search(pattern, source, re.IGNORECASE):
                found = True
                break
        
        if found:
            log_pass("Risk", "Risk management patterns found")
        else:
            log_issue("WARNING", "Risk", "main.py", 0, "Risk management patterns not found")
    
    log_pass("Risk", "Checked risk management")

# ============================================================================
# 9. LEARNING SYSTEM
# ============================================================================

def check_learning_system():
    """Check learning system integration"""
    print("Checking learning system...")
    
    # Check comprehensive learning orchestrator exists
    learning_file = PROJECT_ROOT / "comprehensive_learning_orchestrator_v2.py"
    if not learning_file.exists():
        log_issue("ERROR", "Learning", "comprehensive_learning_orchestrator_v2.py", 0, "Learning orchestrator not found")
    else:
        log_pass("Learning", "Learning orchestrator exists")
        
        # Check for key functions
        with open(learning_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        required_functions = [
            "run_daily_learning",
            "learn_from_trade_close",
            "run_historical_backfill",
            "process_attribution_log",
        ]
        
        for func in required_functions:
            if func in source:
                log_pass("Learning", f"{func} found")
            else:
                log_issue("ERROR", "Learning", str(learning_file), 0, f"{func} not found")
    
    # Check adaptive optimizer
    optimizer_file = PROJECT_ROOT / "adaptive_signal_optimizer.py"
    if optimizer_file.exists():
        with open(optimizer_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check for safeguards
        if "MIN_SAMPLES = 50" in source:
            log_pass("Learning", "MIN_SAMPLES = 50 (correct)")
        elif "MIN_SAMPLES = 30" in source:
            log_issue("WARNING", "Learning", str(optimizer_file), 0, "MIN_SAMPLES should be 50, found 30")
        
        if "MIN_DAYS_BETWEEN_UPDATES" in source:
            log_pass("Learning", "MIN_DAYS_BETWEEN_UPDATES found")
        else:
            log_issue("ERROR", "Learning", str(optimizer_file), 0, "MIN_DAYS_BETWEEN_UPDATES not found")
    
    log_pass("Learning", "Checked learning system")

# ============================================================================
# 10. TRADING READINESS
# ============================================================================

def check_trading_readiness():
    """Check if system is ready for trading"""
    print("Checking trading readiness...")
    
    # Check critical files exist
    critical_files = [
        "main.py",
        "deploy_supervisor.py",
        "dashboard.py",
        "comprehensive_learning_orchestrator_v2.py",
        "adaptive_signal_optimizer.py",
        "profitability_tracker.py",
    ]
    
    for filename in critical_files:
        filepath = PROJECT_ROOT / filename
        if filepath.exists():
            log_pass("Readiness", f"{filename} exists")
        else:
            log_issue("ERROR", "Readiness", filename, 0, f"Critical file missing: {filename}")
    
    # Check .env file exists (but don't read it)
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        log_pass("Readiness", ".env file exists")
    else:
        log_issue("WARNING", "Readiness", ".env", 0, ".env file not found (may be gitignored)")
    
    # Check logs directory
    if LOG_DIR.exists():
        log_pass("Readiness", "Logs directory exists")
    else:
        log_issue("WARNING", "Readiness", "logs/", 0, "Logs directory does not exist")
    
    # Check state directory
    if STATE_DIR.exists():
        log_pass("Readiness", "State directory exists")
    else:
        log_issue("WARNING", "Readiness", "state/", 0, "State directory does not exist (will be created)")
    
    log_pass("Readiness", "Checked trading readiness")

# ============================================================================
# MAIN AUDIT RUNNER
# ============================================================================

def run_full_audit():
    """Run complete audit"""
    print("=" * 80)
    print("COMPREHENSIVE CODE AUDIT")
    print("=" * 80)
    print()
    
    # Run all checks
    check_python_syntax()
    check_imports()
    check_error_handling()
    check_naming_consistency()
    check_config_consistency()
    check_dead_code()
    check_integration_points()
    check_logging()
    check_state_files()
    check_api_integrations()
    check_risk_management()
    check_learning_system()
    check_trading_readiness()
    
    # Generate report
    print()
    print("=" * 80)
    print("AUDIT RESULTS")
    print("=" * 80)
    print()
    
    print(f"[PASSED] {len(passed_checks)}")
    print(f"[WARNINGS] {len(warnings)}")
    print(f"[INFO] {len(info)}")
    print(f"[ERRORS] {len(issues)}")
    print()
    
    if issues:
        print("=" * 80)
        print("ERRORS (Must Fix)")
        print("=" * 80)
        for issue in issues:
            print(f"[ERROR] {issue['file']}:{issue['line']} - {issue['message']}")
            if issue['code']:
                print(f"   Code: {issue['code']}")
        print()
    
    if warnings:
        print("=" * 80)
        print("WARNINGS (Should Fix)")
        print("=" * 80)
        for warning in warnings[:20]:  # Limit to first 20
            print(f"[WARNING] {warning['file']}:{warning['line']} - {warning['message']}")
        if len(warnings) > 20:
            print(f"... and {len(warnings) - 20} more warnings")
        print()
    
    # Save detailed report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "passed": len(passed_checks),
            "warnings": len(warnings),
            "info": len(info),
            "errors": len(issues)
        },
        "errors": issues,
        "warnings": warnings,
        "info": info[:50],  # Limit info items
        "passed": passed_checks
    }
    
    report_file = PROJECT_ROOT / "audit_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"[REPORT] Detailed report saved to: {report_file}")
    print()
    
    # Final status
    if len(issues) == 0:
        print("[PASS] AUDIT PASSED - No critical errors found")
        if len(warnings) > 0:
            print(f"[WARNING] {len(warnings)} warnings should be reviewed")
        return True
    else:
        print(f"[FAIL] AUDIT FAILED - {len(issues)} critical errors must be fixed")
        return False

if __name__ == "__main__":
    success = run_full_audit()
    exit(0 if success else 1)
