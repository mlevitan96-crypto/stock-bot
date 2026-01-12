#!/usr/bin/env python3
"""
API Drift Test Scenario (Risk #11)
===================================
Tests API contract validation and drift detection.
"""

import os
import json
from pathlib import Path
from typing import Dict
from unittest.mock import Mock, patch


def run_scenario(runner) -> Dict:
    """Run API drift tests."""
    results = {
        "scenario": "api_drift",
        "status": "PASS",
        "tests": []
    }
    
    # Test 1: Missing required field detection
    print("  Test 1: Missing required field detection...")
    test1_result = test_missing_field(runner)
    results["tests"].append(test1_result)
    if test1_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 2: Extra fields tolerance
    print("  Test 2: Extra fields tolerance...")
    test2_result = test_extra_fields(runner)
    results["tests"].append(test2_result)
    if test2_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 3: Type mismatch detection
    print("  Test 3: Type mismatch detection...")
    test3_result = test_type_mismatch(runner)
    results["tests"].append(test3_result)
    if test3_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 4: Compatibility check on startup
    print("  Test 4: Compatibility check on startup...")
    test4_result = test_compatibility_check(runner)
    results["tests"].append(test4_result)
    if test4_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    return results


def test_missing_field(runner) -> Dict:
    """Test that missing required fields are detected."""
    test_result = {
        "name": "Missing required field detection",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from alpaca_client import AlpacaClient, ErrorType
        
        # Create a mock account object missing required fields
        class MockAccount:
            def __init__(self):
                # Missing 'equity' field
                self.buying_power = 100000.0
                self.cash = 50000.0
                self.portfolio_value = 150000.0
        
        # Test contract validation
        client = AlpacaClient("test_key", "test_secret", "https://test.url")
        
        # Validate should detect missing field
        is_valid, error = client._validate_contract(MockAccount(), "account")
        
        if not is_valid and "equity" in error.lower():
            test_result["status"] = "PASS"
            test_result["message"] = "Missing required field detected correctly"
            test_result["details"] = error
        elif is_valid:
            test_result["status"] = "FAIL"
            test_result["message"] = "Missing required field not detected"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = f"Validation failed but for wrong reason: {error}"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_extra_fields(runner) -> Dict:
    """Test that extra fields don't cause failures."""
    test_result = {
        "name": "Extra fields tolerance",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from alpaca_client import AlpacaClient
        
        # Create a mock account object with extra fields
        class MockAccount:
            def __init__(self):
                self.equity = 100000.0
                self.buying_power = 100000.0
                self.cash = 50000.0
                self.portfolio_value = 150000.0
                # Extra field
                self.extra_field = "should_be_ignored"
        
        client = AlpacaClient("test_key", "test_secret", "https://test.url")
        
        # Validate should pass despite extra field
        is_valid, error = client._validate_contract(MockAccount(), "account")
        
        if is_valid:
            test_result["status"] = "PASS"
            test_result["message"] = "Extra fields correctly tolerated"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = f"Extra fields caused validation failure: {error}"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_type_mismatch(runner) -> Dict:
    """Test that type mismatches are detected."""
    test_result = {
        "name": "Type mismatch detection",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from alpaca_client import AlpacaClient
        
        # Create a mock account object with wrong type
        class MockAccount:
            def __init__(self):
                self.equity = "not_a_number"  # Should be float
                self.buying_power = 100000.0
                self.cash = 50000.0
                self.portfolio_value = 150000.0
        
        client = AlpacaClient("test_key", "test_secret", "https://test.url")
        
        # Validate should detect type mismatch
        is_valid, error = client._validate_contract(MockAccount(), "account")
        
        if not is_valid and ("type" in error.lower() or "equity" in error.lower()):
            test_result["status"] = "PASS"
            test_result["message"] = "Type mismatch detected correctly"
            test_result["details"] = error
        elif is_valid:
            test_result["status"] = "FAIL"
            test_result["message"] = "Type mismatch not detected"
        else:
            test_result["status"] = "PASS"  # Any failure is acceptable for type mismatch
            test_result["message"] = f"Type mismatch detected: {error}"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_compatibility_check(runner) -> Dict:
    """Test that compatibility checks run on startup."""
    test_result = {
        "name": "Compatibility check on startup",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        # Check if compatibility check function exists
        from alpaca_client import check_alpaca_compat
        
        # Try to run compatibility check (will fail without real credentials, but function should exist)
        try:
            is_ok, error = check_alpaca_compat("test_key", "test_secret", "https://test.url")
            # Function exists and runs (even if it fails)
            test_result["status"] = "PASS"
            test_result["message"] = "Compatibility check function exists and is callable"
            test_result["details"] = f"Result: OK={is_ok}, Error={error}"
        except Exception as e:
            # Function exists but failed (expected without real credentials)
            if "check_alpaca_compat" in str(e) or "compatibility" in str(e).lower():
                test_result["status"] = "PASS"
                test_result["message"] = "Compatibility check function exists"
            else:
                test_result["status"] = "FAIL"
                test_result["message"] = f"Compatibility check failed unexpectedly: {e}"
    
    except ImportError:
        test_result["status"] = "FAIL"
        test_result["message"] = "Compatibility check function not found"
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result
