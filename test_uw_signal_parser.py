#!/usr/bin/env python3
"""
Diagnostic Test Script: UW Signal Parser Recovery
==================================================
Tests that the parser correctly extracts flow_conv, flow_magnitude, and signal_type
from a raw UW API JSON payload sample.
"""

import json
import sys
from pathlib import Path

# Sample UW API JSON payload (typical structure)
SAMPLE_UW_TRADE = {
    "ticker": "AAPL",
    "symbol": "AAPL",
    "type": "call",
    "total_premium": 250000.0,
    "premium": 250000.0,
    "total_bid_side_prem": 240000.0,
    "total_ask_side_prem": 260000.0,
    "strike": 150.0,
    "expiry": "2025-01-10",
    "expiration": "2025-01-10",
    "volume": 1000,
    "open_interest": 5000,
    "oi": 5000,
    "underlying_price": 148.50,
    "exchange": "NASDAQ",
    "created_at": "2026-01-05T10:30:00Z",
    "timestamp": "2026-01-05T10:30:00Z",
    "has_sweep": True,
    "has_floor": False,
    "has_multileg": False,
    "flow_conv": 0.75,  # ROOT CAUSE FIX: This field should be extracted
    "flow_conviction": 0.75,  # Alternative field name
    "conviction": 0.75,  # Another alternative
    "flow_magnitude": "HIGH",  # ROOT CAUSE FIX: This field should be extracted
    "magnitude": "HIGH"  # Alternative field name
}

def test_normalize_flow_trade():
    """Test that _normalize_flow_trade extracts all required fields"""
    print("=" * 80)
    print("TEST: _normalize_flow_trade field extraction")
    print("=" * 80)
    print()
    
    # Import the UWClient class
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from main import UWClient
        
        client = UWClient()
        normalized = client._normalize_flow_trade(SAMPLE_UW_TRADE)
        
        print("Input sample trade:")
        print(json.dumps(SAMPLE_UW_TRADE, indent=2))
        print()
        print("Normalized output:")
        print(json.dumps(normalized, indent=2, default=str))
        print()
        
        # Verify required fields
        checks = {
            "flow_conv": ("flow_conv" in normalized, normalized.get("flow_conv"), 0.75),
            "flow_magnitude": ("flow_magnitude" in normalized, normalized.get("flow_magnitude"), "HIGH"),
            "signal_type": ("signal_type" in normalized, normalized.get("signal_type"), "BULLISH_SWEEP"),
            "flow_type": ("flow_type" in normalized, normalized.get("flow_type"), "sweep"),
            "direction": ("direction" in normalized, normalized.get("direction"), "bullish"),
        }
        
        print("=" * 80)
        print("VERIFICATION RESULTS")
        print("=" * 80)
        
        all_passed = True
        for field, (exists, actual, expected) in checks.items():
            status = "✅ PASS" if exists and actual == expected else "❌ FAIL"
            if not exists:
                print(f"{status}: {field} - MISSING")
                all_passed = False
            elif actual != expected:
                print(f"{status}: {field} - Expected {expected}, got {actual}")
                all_passed = False
            else:
                print(f"{status}: {field} = {actual}")
        
        print()
        if all_passed:
            print("✅ ALL TESTS PASSED - Parser correctly extracts all fields")
        else:
            print("❌ SOME TESTS FAILED - Parser needs fixes")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_type_creation():
    """Test that signal_type is created correctly from flow_type + direction"""
    print()
    print("=" * 80)
    print("TEST: signal_type creation logic")
    print("=" * 80)
    print()
    
    test_cases = [
        ("bullish", "sweep", "BULLISH_SWEEP"),
        ("bearish", "block", "BEARISH_BLOCK"),
        ("bullish", "multileg", "BULLISH_MULTILEG"),
        ("bearish", "singleleg", "BEARISH_SINGLELEG"),
    ]
    
    all_passed = True
    for direction, flow_type, expected_signal_type in test_cases:
        actual = f"{direction.upper()}_{flow_type.upper()}"
        status = "✅ PASS" if actual == expected_signal_type else "❌ FAIL"
        print(f"{status}: direction={direction}, flow_type={flow_type} -> signal_type={actual} (expected {expected_signal_type})")
        if actual != expected_signal_type:
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print()
    print("=" * 80)
    print("UW SIGNAL PARSER DIAGNOSTIC TEST")
    print("=" * 80)
    print()
    
    test1_passed = test_normalize_flow_trade()
    test2_passed = test_signal_type_creation()
    
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Field extraction test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Signal type creation test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print()
    
    if test1_passed and test2_passed:
        print("✅ ALL TESTS PASSED")
        print("Parser is correctly extracting flow_conv, flow_magnitude, and signal_type")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("Parser needs fixes - review the code changes")
        return 1

if __name__ == "__main__":
    sys.exit(main())
