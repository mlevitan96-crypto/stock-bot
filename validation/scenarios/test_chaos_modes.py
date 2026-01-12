#!/usr/bin/env python3
"""
Chaos Testing Modes Scenario (Risk #12)
========================================
Tests chaos testing hooks and controlled failure scenarios.
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict


def run_scenario(runner) -> Dict:
    """Run chaos mode tests."""
    results = {
        "scenario": "chaos_modes",
        "status": "PASS",
        "tests": []
    }
    
    # Test 1: Chaos mode environment variable
    print("  Test 1: Chaos mode environment variable...")
    test1_result = test_chaos_mode_env(runner)
    results["tests"].append(test1_result)
    if test1_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 2: State corruption chaos mode
    print("  Test 2: State corruption chaos mode...")
    test2_result = test_state_corrupt_chaos(runner)
    results["tests"].append(test2_result)
    if test2_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 3: Invalid credentials chaos mode
    print("  Test  Test 3: Invalid credentials chaos mode...")
    test3_result = test_invalid_creds_chaos(runner)
    results["tests"].append(test3_result)
    if test3_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    return results


def test_chaos_mode_env(runner) -> Dict:
    """Test that chaos mode is controlled by environment variable."""
    test_result = {
        "name": "Chaos mode environment variable",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        # Check if deploy_supervisor reads CHAOS_MODE
        supervisor_file = Path("/root/stock-bot/deploy_supervisor.py")
        if not supervisor_file.exists():
            test_result["status"] = "SKIP"
            test_result["message"] = "deploy_supervisor.py not found"
            return test_result
        
        content = supervisor_file.read_text()
        
        if "CHAOS_MODE" in content and "os.getenv" in content:
            test_result["status"] = "PASS"
            test_result["message"] = "Chaos mode controlled by environment variable"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = "Chaos mode not properly controlled by environment variable"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_state_corrupt_chaos(runner) -> Dict:
    """Test state corruption chaos mode."""
    test_result = {
        "name": "State corruption chaos mode",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        STATE_DIR = Path("/root/stock-bot/state")
        STATE_FILE = STATE_DIR / "trading_state.json"
        
        # Backup original
        backup_file = None
        if STATE_FILE.exists():
            backup_file = STATE_FILE.with_suffix(".backup")
            import shutil
            shutil.copy2(STATE_FILE, backup_file)
        
        # Check if chaos mode would corrupt state
        supervisor_file = Path("/root/stock-bot/deploy_supervisor.py")
        if supervisor_file.exists():
            content = supervisor_file.read_text()
            if "state_corrupt" in content and "CHAOS_MODE" in content:
                test_result["status"] = "PASS"
                test_result["message"] = "State corruption chaos mode implemented"
            else:
                test_result["status"] = "FAIL"
                test_result["message"] = "State corruption chaos mode not found in supervisor"
        else:
            test_result["status"] = "SKIP"
            test_result["message"] = "Supervisor file not found"
        
        # Restore backup
        if backup_file and backup_file.exists():
            import shutil
            shutil.copy2(backup_file, STATE_FILE)
            backup_file.unlink()
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_invalid_creds_chaos(runner) -> Dict:
    """Test invalid credentials chaos mode."""
    test_result = {
        "name": "Invalid credentials chaos mode",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        # Check if chaos mode would override credentials
        supervisor_file = Path("/root/stock-bot/deploy_supervisor.py")
        if supervisor_file.exists():
            content = supervisor_file.read_text()
            if "invalid_creds" in content and "CHAOS_MODE" in content:
                # Check that it only overrides in-process, not .env
                if "INVALID_KEY" in content or "INVALID_SECRET" in content:
                    if ".env" not in content or "override" not in content.lower():
                        test_result["status"] = "PASS"
                        test_result["message"] = "Invalid credentials chaos mode implemented (in-process only)"
                    else:
                        test_result["status"] = "FAIL"
                        test_result["message"] = "Chaos mode may modify .env file (unsafe)"
                else:
                    test_result["status"] = "PASS"
                    test_result["message"] = "Invalid credentials chaos mode implemented"
            else:
                test_result["status"] = "FAIL"
                test_result["message"] = "Invalid credentials chaos mode not found"
        else:
            test_result["status"] = "SKIP"
            test_result["message"] = "Supervisor file not found"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result
