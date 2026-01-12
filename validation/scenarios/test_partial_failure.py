#!/usr/bin/env python3
"""
Partial Service Failure Test Scenario (Risk #9)
================================================
Tests detection and response to partial service failures.
"""

import os
import json
import time
import subprocess
import signal
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict

STATE_DIR = Path("/root/stock-bot/state")
HEALTH_FILE = STATE_DIR / "health.json"


def run_scenario(runner) -> Dict:
    """Run partial failure tests."""
    results = {
        "scenario": "partial_failure",
        "status": "PASS",
        "tests": []
    }
    
    # Test 1: Kill trading-bot process
    print("  Test 1: Kill trading-bot process...")
    test1_result = test_kill_trading_bot(runner)
    results["tests"].append(test1_result)
    if test1_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 2: Health registry updates
    print("  Test 2: Health registry updates...")
    test2_result = test_health_registry(runner)
    results["tests"].append(test2_result)
    if test2_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 3: Overall health aggregation
    print("  Test 3: Overall health aggregation...")
    test3_result = test_health_aggregation(runner)
    results["tests"].append(test3_result)
    if test3_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    return results


def test_kill_trading_bot(runner) -> Dict:
    """Test that killing trading-bot is detected and health updated."""
    test_result = {
        "name": "Kill trading-bot detection",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        # Find trading-bot process
        result = subprocess.run(
            ["pgrep", "-f", "python.*main.py"],
            capture_output=True,
            timeout=2
        )
        
        if result.returncode != 0:
            test_result["status"] = "SKIP"
            test_result["message"] = "Trading-bot process not running - cannot test kill detection"
            return test_result
        
        pids = result.stdout.decode().strip().split('\n')
        if not pids or not pids[0]:
            test_result["status"] = "SKIP"
            test_result["message"] = "No trading-bot PID found"
            return test_result
        
        pid = int(pids[0])
        
        # Capture initial health
        runner.capture_snapshot("before_kill")
        initial_health = runner.read_health()
        
        # Kill the process
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)  # Wait for supervisor to detect
        except ProcessLookupError:
            # Process already dead
            pass
        
        # Wait a bit for supervisor to update health
        time.sleep(5)
        
        # Capture updated health
        runner.capture_snapshot("after_kill")
        updated_health = runner.read_health()
        
        # Check if health was updated
        if updated_health:
            trading_bot_status = None
            if "details" in updated_health:
                trading_bot_details = updated_health["details"].get("trading-bot", {})
                trading_bot_status = trading_bot_details.get("status")
            
            if trading_bot_status in ["FAILED", "DEGRADED"]:
                test_result["status"] = "PASS"
                test_result["message"] = f"Trading-bot failure detected, status: {trading_bot_status}"
            elif updated_health.get("overall_status") in ["FAILED", "DEGRADED"]:
                test_result["status"] = "PASS"
                test_result["message"] = f"Overall health reflects failure: {updated_health.get('overall_status')}"
            else:
                test_result["status"] = "FAIL"
                test_result["message"] = "Health not updated after trading-bot kill"
                test_result["details"] = f"Health: {json.dumps(updated_health, indent=2)}"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = "Health file not found or not readable after kill"
        
        # Capture logs
        runner.capture_logs("after_kill", lines=30)
        
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_health_registry(runner) -> Dict:
    """Test that health registry tracks all services."""
    test_result = {
        "name": "Health registry tracking",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        health = runner.read_health()
        
        if not health:
            test_result["status"] = "FAIL"
            test_result["message"] = "Health file not found"
            return test_result
        
        # Check for required services
        required_services = ["trading-bot", "uw-daemon", "dashboard", "heartbeat-keeper"]
        services_tracked = []
        
        if "details" in health:
            for service in required_services:
                if service in health["details"]:
                    services_tracked.append(service)
        
        if len(services_tracked) >= len(required_services):
            test_result["status"] = "PASS"
            test_result["message"] = f"All required services tracked: {', '.join(services_tracked)}"
        else:
            missing = set(required_services) - set(services_tracked)
            test_result["status"] = "FAIL"
            test_result["message"] = f"Missing services in health registry: {', '.join(missing)}"
            test_result["details"] = f"Tracked: {services_tracked}"
        
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_health_aggregation(runner) -> Dict:
    """Test that overall health is correctly aggregated."""
    test_result = {
        "name": "Health aggregation",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        health = runner.read_health()
        
        if not health:
            test_result["status"] = "FAIL"
            test_result["message"] = "Health file not found"
            return test_result
        
        overall_status = health.get("overall_status")
        services = health.get("services", {})
        
        if not overall_status:
            test_result["status"] = "FAIL"
            test_result["message"] = "Overall status not present in health"
            return test_result
        
        # Validate aggregation logic
        critical_services = ["trading-bot", "uw-daemon", "heartbeat-keeper"]
        critical_statuses = [services.get(s, "UNKNOWN") for s in critical_services]
        
        # Check if aggregation is correct
        if "FAILED" in critical_statuses and overall_status != "FAILED":
            test_result["status"] = "FAIL"
            test_result["message"] = "Overall status should be FAILED when critical service is FAILED"
            test_result["details"] = f"Critical statuses: {critical_statuses}, Overall: {overall_status}"
        elif "DEGRADED" in critical_statuses and overall_status not in ["DEGRADED", "FAILED"]:
            test_result["status"] = "FAIL"
            test_result["message"] = "Overall status should reflect critical service degradation"
            test_result["details"] = f"Critical statuses: {critical_statuses}, Overall: {overall_status}"
        elif all(s == "OK" for s in critical_statuses) and overall_status == "OK":
            test_result["status"] = "PASS"
            test_result["message"] = "Health aggregation correct: all critical services OK"
        else:
            test_result["status"] = "PASS"
            test_result["message"] = f"Health aggregation appears correct: {overall_status}"
            test_result["details"] = f"Critical statuses: {critical_statuses}"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result
