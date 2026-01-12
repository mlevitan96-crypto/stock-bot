#!/usr/bin/env python3
"""
State Persistence Test Scenario (Risk #6)
==========================================
Tests state persistence and reconciliation under failure conditions.
"""

import os
import json
import time
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

STATE_DIR = Path("/root/stock-bot/state")
STATE_FILE = STATE_DIR / "trading_state.json"


def run_scenario(runner) -> Dict:
    """Run state persistence tests."""
    results = {
        "scenario": "state_persistence",
        "status": "PASS",
        "tests": []
    }
    
    # Test 1: Corrupted state file recovery
    print("  Test 1: Corrupted state file recovery...")
    test1_result = test_corrupted_state_recovery(runner)
    results["tests"].append(test1_result)
    if test1_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 2: State reconciliation after restart
    print("  Test 2: State reconciliation after restart...")
    test2_result = test_state_reconciliation(runner)
    results["tests"].append(test2_result)
    if test2_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 3: Atomic write integrity
    print("  Test 3: Atomic write integrity...")
    test3_result = test_atomic_write(runner)
    results["tests"].append(test3_result)
    if test3_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    return results


def test_corrupted_state_recovery(runner) -> Dict:
    """Test that corrupted state files are detected and recovered."""
    test_result = {
        "name": "Corrupted state file recovery",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        # Backup original state file if it exists
        backup_file = None
        if STATE_FILE.exists():
            backup_file = STATE_FILE.with_suffix(".backup")
            shutil.copy2(STATE_FILE, backup_file)
        
        # Corrupt the state file
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text("{ invalid json }")
        
        # Capture snapshot
        runner.capture_snapshot("corrupted_state_before")
        
        # Try to load state (should trigger self-heal)
        try:
            from state_manager import StateManager
            manager = StateManager(None)  # No API for this test
            state = manager.load_state()
            
            # Check if corruption was handled
            if STATE_FILE.exists():
                # File should be valid JSON now (recovered)
                try:
                    with open(STATE_FILE, 'r') as f:
                        json.load(f)
                    test_result["status"] = "PASS"
                    test_result["message"] = "State file corruption detected and recovered"
                except json.JSONDecodeError:
                    # Check if corrupt file was moved to backup
                    corrupt_backups = list(STATE_DIR.glob("trading_state.json.corrupt.*"))
                    if corrupt_backups:
                        test_result["status"] = "PASS"
                        test_result["message"] = f"Corrupt file quarantined: {corrupt_backups[0].name}"
                    else:
                        test_result["status"] = "FAIL"
                        test_result["message"] = "Corrupt file not properly handled"
            else:
                # File was removed (acceptable if starting fresh)
                test_result["status"] = "PASS"
                test_result["message"] = "Corrupt file removed, starting with empty state"
            
        except Exception as e:
            test_result["status"] = "FAIL"
            test_result["message"] = f"State manager failed to handle corruption: {e}"
            test_result["details"] = str(e)
        
        # Restore backup if it existed
        if backup_file and backup_file.exists():
            shutil.copy2(backup_file, STATE_FILE)
            backup_file.unlink()
        elif not STATE_FILE.exists() and backup_file and backup_file.exists():
            shutil.copy2(backup_file, STATE_FILE)
            backup_file.unlink()
        
        runner.capture_snapshot("corrupted_state_after")
        
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_state_reconciliation(runner) -> Dict:
    """Test that state reconciles with Alpaca on startup."""
    test_result = {
        "name": "State reconciliation",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        # Check if we can access Alpaca API
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv("/root/stock-bot/.env")
            
            alpaca_key = os.getenv("ALPACA_KEY")
            alpaca_secret = os.getenv("ALPACA_SECRET")
            alpaca_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
            
            if not alpaca_key or not alpaca_secret:
                test_result["status"] = "SKIP"
                test_result["message"] = "Alpaca credentials not available - skipping reconciliation test"
                return test_result
            
            # Test reconciliation
            from state_manager import StateManager
            import alpaca_trade_api as tradeapi
            
            api = tradeapi.REST(alpaca_key, alpaca_secret, alpaca_url)
            manager = StateManager(api)
            
            # Load state
            state = manager.load_state()
            
            # Attempt reconciliation
            reconciled = manager.reconcile_with_alpaca(state)
            
            if reconciled:
                test_result["status"] = "PASS"
                test_result["message"] = "State reconciliation with Alpaca succeeded"
                
                # Verify state structure
                final_state = manager.get_state()
                if "open_positions" in final_state and "reconciliation_status" in final_state:
                    test_result["details"] = f"Reconciled {len(final_state.get('open_positions', {}))} positions"
                else:
                    test_result["status"] = "FAIL"
                    test_result["message"] = "Reconciliation succeeded but state structure invalid"
            else:
                test_result["status"] = "FAIL"
                test_result["message"] = "State reconciliation failed"
                test_result["details"] = state.get("reconciliation_error", "Unknown error")
        
        except ImportError:
            test_result["status"] = "SKIP"
            test_result["message"] = "Required modules not available - skipping reconciliation test"
        except Exception as e:
            test_result["status"] = "FAIL"
            test_result["message"] = f"Reconciliation test failed: {e}"
            test_result["details"] = str(e)
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_atomic_write(runner) -> Dict:
    """Test that state writes are atomic."""
    test_result = {
        "name": "Atomic write integrity",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from state_manager import StateManager
        from config.registry import atomic_write_json
        
        # Backup original
        backup_file = None
        if STATE_FILE.exists():
            backup_file = STATE_FILE.with_suffix(".backup")
            shutil.copy2(STATE_FILE, backup_file)
        
        # Test atomic write
        test_data = {
            "state_version": 1,
            "test_timestamp": datetime.now(timezone.utc).isoformat(),
            "test_data": "atomic_write_test"
        }
        
        try:
            atomic_write_json(STATE_FILE, test_data)
            
            # Verify file exists and is valid
            if STATE_FILE.exists():
                with open(STATE_FILE, 'r') as f:
                    loaded_data = json.load(f)
                
                if loaded_data.get("test_data") == "atomic_write_test":
                    test_result["status"] = "PASS"
                    test_result["message"] = "Atomic write succeeded and data is valid"
                else:
                    test_result["status"] = "FAIL"
                    test_result["message"] = "Atomic write completed but data mismatch"
            else:
                test_result["status"] = "FAIL"
                test_result["message"] = "Atomic write did not create file"
        
        except Exception as e:
            test_result["status"] = "FAIL"
            test_result["message"] = f"Atomic write failed: {e}"
            test_result["details"] = str(e)
        
        # Restore backup
        if backup_file and backup_file.exists():
            shutil.copy2(backup_file, STATE_FILE)
            backup_file.unlink()
        elif STATE_FILE.exists():
            STATE_FILE.unlink()
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result
