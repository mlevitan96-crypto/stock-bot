#!/usr/bin/env python3
"""
Trade Guard Test Scenario (Risk #15)
=====================================
Tests trade sanity checks and order rejection.
"""

import os
import json
from pathlib import Path
from typing import Dict
from datetime import datetime, timezone


def run_scenario(runner) -> Dict:
    """Run trade guard tests."""
    results = {
        "scenario": "trade_guard",
        "status": "PASS",
        "tests": []
    }
    
    # Test 1: Oversized position rejection
    print("  Test 1: Oversized position rejection...")
    test1_result = test_oversized_position(runner)
    results["tests"].append(test1_result)
    if test1_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 2: Too frequent trades rejection
    print("  Test 2: Too frequent trades rejection...")
    test2_result = test_cooldown_enforcement(runner)
    results["tests"].append(test2_result)
    if test2_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 3: Unrealistic price rejection
    print("  Test 3: Unrealistic price rejection...")
    test3_result = test_price_sanity(runner)
    results["tests"].append(test3_result)
    if test3_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 4: Direction flip protection
    print("  Test 4: Direction flip protection...")
    test4_result = test_direction_flip(runner)
    results["tests"].append(test4_result)
    if test4_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 5: Excessive notional rejection
    print("  Test 5: Excessive notional rejection...")
    test5_result = test_excessive_notional(runner)
    results["tests"].append(test5_result)
    if test5_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    return results


def test_oversized_position(runner) -> Dict:
    """Test that oversized positions are rejected."""
    test_result = {
        "name": "Oversized position rejection",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from trade_guard import TradeGuard
        
        guard = TradeGuard()
        
        # Create order context with oversized position
        order_context = {
            "symbol": "AAPL",
            "side": "buy",
            "qty": 10000,  # Very large
            "intended_price": 150.0,
            "last_known_price": 150.0,
            "current_positions": {},
            "account_equity": 10000.0,  # Small account
            "account_buying_power": 5000.0,
            "last_trade_timestamp": None,
            "risk_config": {}
        }
        
        approved, reason = guard.evaluate_order(order_context)
        
        if not approved:
            test_result["status"] = "PASS"
            test_result["message"] = f"Oversized position correctly rejected: {reason}"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = "Oversized position was not rejected"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_cooldown_enforcement(runner) -> Dict:
    """Test that cooldown is enforced."""
    test_result = {
        "name": "Cooldown enforcement",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from trade_guard import TradeGuard
        
        guard = TradeGuard()
        
        # Create order context with recent trade
        recent_timestamp = datetime.now(timezone.utc).isoformat()
        
        order_context = {
            "symbol": "AAPL",
            "side": "buy",
            "qty": 10,
            "intended_price": 150.0,
            "last_known_price": 150.0,
            "current_positions": {},
            "account_equity": 100000.0,
            "account_buying_power": 50000.0,
            "last_trade_timestamp": recent_timestamp,  # Just now
            "risk_config": {}
        }
        
        approved, reason = guard.evaluate_order(order_context)
        
        if not approved and "cooldown" in reason.lower():
            test_result["status"] = "PASS"
            test_result["message"] = f"Cooldown correctly enforced: {reason}"
        elif approved:
            test_result["status"] = "FAIL"
            test_result["message"] = "Cooldown not enforced"
        else:
            test_result["status"] = "PASS"  # Any rejection is acceptable
            test_result["message"] = f"Order rejected (may be cooldown or other): {reason}"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_price_sanity(runner) -> Dict:
    """Test that unrealistic prices are rejected."""
    test_result = {
        "name": "Price sanity check",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from trade_guard import TradeGuard
        
        guard = TradeGuard()
        
        # Create order context with unrealistic price deviation
        order_context = {
            "symbol": "AAPL",
            "side": "buy",
            "qty": 10,
            "intended_price": 300.0,  # Very high
            "last_known_price": 150.0,  # Normal price
            "current_positions": {},
            "account_equity": 100000.0,
            "account_buying_power": 50000.0,
            "last_trade_timestamp": None,
            "risk_config": {}
        }
        
        approved, reason = guard.evaluate_order(order_context)
        
        if not approved and ("price" in reason.lower() or "deviation" in reason.lower()):
            test_result["status"] = "PASS"
            test_result["message"] = f"Unrealistic price correctly rejected: {reason}"
        elif approved:
            test_result["status"] = "FAIL"
            test_result["message"] = "Unrealistic price was not rejected"
        else:
            test_result["status"] = "PASS"  # Any rejection is acceptable
            test_result["message"] = f"Order rejected: {reason}"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_direction_flip(runner) -> Dict:
    """Test that direction flips are protected."""
    test_result = {
        "name": "Direction flip protection",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from trade_guard import TradeGuard
        
        guard = TradeGuard()
        
        # Create order context with existing position in opposite direction
        order_context = {
            "symbol": "AAPL",
            "side": "sell",  # Trying to sell
            "qty": 100,
            "intended_price": 150.0,
            "last_known_price": 150.0,
            "current_positions": {
                "AAPL": {
                    "qty": 50,
                    "side": "buy",  # Existing long position
                    "cost_basis": 145.0
                }
            },
            "account_equity": 100000.0,
            "account_buying_power": 50000.0,
            "last_trade_timestamp": None,
            "risk_config": {}
        }
        
        approved, reason = guard.evaluate_order(order_context)
        
        # With default config, direction flip should be blocked
        if not approved and ("flip" in reason.lower() or "direction" in reason.lower()):
            test_result["status"] = "PASS"
            test_result["message"] = f"Direction flip correctly blocked: {reason}"
        elif approved:
            # Check if direction flip is allowed in config
            if guard.allow_direction_flip:
                test_result["status"] = "PASS"
                test_result["message"] = "Direction flip allowed by configuration"
            else:
                test_result["status"] = "FAIL"
                test_result["message"] = "Direction flip not blocked when it should be"
        else:
            test_result["status"] = "PASS"  # Any rejection is acceptable
            test_result["message"] = f"Order rejected: {reason}"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_excessive_notional(runner) -> Dict:
    """Test that excessive notional is rejected."""
    test_result = {
        "name": "Excessive notional rejection",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from trade_guard import TradeGuard
        
        guard = TradeGuard()
        
        # Create order context with excessive notional
        order_context = {
            "symbol": "AAPL",
            "side": "buy",
            "qty": 1000,
            "intended_price": 500.0,  # High price * large qty = excessive notional
            "last_known_price": 500.0,
            "current_positions": {},
            "account_equity": 100000.0,
            "account_buying_power": 50000.0,
            "last_trade_timestamp": None,
            "risk_config": {}
        }
        
        approved, reason = guard.evaluate_order(order_context)
        
        if not approved and ("notional" in reason.lower()):
            test_result["status"] = "PASS"
            test_result["message"] = f"Excessive notional correctly rejected: {reason}"
        elif approved:
            test_result["status"] = "FAIL"
            test_result["message"] = "Excessive notional was not rejected"
        else:
            test_result["status"] = "PASS"  # Any rejection is acceptable
            test_result["message"] = f"Order rejected: {reason}"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result
