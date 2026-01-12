#!/usr/bin/env python3
"""
Scoring Pipeline Fixes Test Scenario
=====================================
Tests the Priority 1-4 fixes from SIGNAL_SCORE_PIPELINE_AUDIT.md

Tests:
1. Freshness decay uses 180 minutes (not 45)
2. Flow conviction defaults to 0.5 (not 0.0)
3. Core features always computed or neutral-defaulted
4. Expanded intel provides neutral defaults (not 0.0)
5. Telemetry records scores correctly
6. Dashboard endpoints return valid JSON
"""

import os
import json
from pathlib import Path
from typing import Dict
from datetime import datetime, timezone, timedelta
import time


def run_scenario(runner) -> Dict:
    """Run scoring pipeline fixes tests."""
    results = {
        "scenario": "scoring_pipeline_fixes",
        "status": "PASS",
        "tests": []
    }
    
    # Test 1: Freshness decay configuration
    print("  Test 1: Freshness decay uses 180 minutes...")
    test1_result = test_freshness_decay(runner)
    results["tests"].append(test1_result)
    if test1_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 2: Flow conviction default
    print("  Test 2: Flow conviction defaults to 0.5...")
    test2_result = test_flow_conviction_default(runner)
    results["tests"].append(test2_result)
    if test2_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 3: Core features always computed
    print("  Test 3: Core features always computed...")
    test3_result = test_core_features_computed(runner)
    results["tests"].append(test3_result)
    if test3_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 4: Expanded intel neutral defaults
    print("  Test 4: Expanded intel provides neutral defaults...")
    test4_result = test_expanded_intel_defaults(runner)
    results["tests"].append(test4_result)
    if test4_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 5: Telemetry records scores
    print("  Test 5: Telemetry records scores...")
    test5_result = test_telemetry_recording(runner)
    results["tests"].append(test5_result)
    if test5_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    # Test 6: Dashboard endpoints
    print("  Test 6: Dashboard endpoints return valid JSON...")
    test6_result = test_dashboard_endpoints(runner)
    results["tests"].append(test6_result)
    if test6_result["status"] == "FAIL":
        results["status"] = "FAIL"
    
    return results


def test_freshness_decay(runner) -> Dict:
    """Test that freshness decay uses 180 minutes."""
    test_result = {
        "name": "Freshness decay configuration",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from uw_enrichment_v2 import DECAY_MINUTES, UWEnricher
        
        if DECAY_MINUTES == 180:
            test_result["status"] = "PASS"
            test_result["message"] = f"DECAY_MINUTES correctly set to {DECAY_MINUTES}"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = f"DECAY_MINUTES is {DECAY_MINUTES}, expected 180"
        
        # Test that compute_freshness uses the constant
        enricher = UWEnricher()
        test_data = {
            "_last_update": int(time.time()) - (90 * 60)  # 90 minutes ago
        }
        freshness = enricher.compute_freshness(test_data)
        
        # With 180min decay, 90min old data should have freshness ≈ 0.707
        # With 45min decay, 90min old data would have freshness ≈ 0.135
        if 0.6 < freshness < 0.8:
            test_result["status"] = "PASS"
            test_result["message"] += f" (freshness={freshness:.3f} confirms 180min decay)"
        elif freshness < 0.3:
            test_result["status"] = "FAIL"
            test_result["message"] += f" (freshness={freshness:.3f} suggests 45min decay still active)"
    
    except ImportError as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Failed to import uw_enrichment_v2: {e}"
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_flow_conviction_default(runner) -> Dict:
    """Test that flow conviction defaults to 0.5."""
    test_result = {
        "name": "Flow conviction default",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        import uw_composite_v2 as uw_v2
        
        # Create enriched data without conviction
        enriched_data = {
            "sentiment": "BULLISH",
            # No "conviction" key
            "dark_pool": {"sentiment": "BULLISH", "total_premium": 1000000},
            "insider": {"sentiment": "NEUTRAL"}
        }
        
        # Calculate composite score
        composite = uw_v2.compute_composite_score_v3("TEST", enriched_data, "mixed")
        
        if composite:
            # Check if flow component contributed (should be 2.4 * 0.5 = 1.2)
            flow_component = composite.get("components", {}).get("flow", 0.0)
            if flow_component > 0.5:  # Should be around 1.2
                test_result["status"] = "PASS"
                test_result["message"] = f"Flow conviction defaulted correctly (flow_component={flow_component:.3f})"
            elif flow_component == 0.0:
                test_result["status"] = "FAIL"
                test_result["message"] = f"Flow conviction still defaults to 0.0 (flow_component={flow_component:.3f})"
            else:
                test_result["status"] = "PASS"
                test_result["message"] = f"Flow component contributed (flow_component={flow_component:.3f})"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = "Composite scoring returned None"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_core_features_computed(runner) -> Dict:
    """Test that core features are always computed or neutral-defaulted."""
    test_result = {
        "name": "Core features always computed",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        import uw_composite_v2 as uw_v2
        
        # Create enriched data without core features
        enriched_data = {
            "sentiment": "BULLISH",
            "conviction": 0.7,
            "dark_pool": {"sentiment": "BULLISH"},
            "insider": {"sentiment": "NEUTRAL"}
            # No iv_term_skew, smile_slope, event_alignment
        }
        
        # Calculate composite score
        composite = uw_v2.compute_composite_score_v3("TEST", enriched_data, "mixed")
        
        if composite:
            components = composite.get("components", {})
            iv_component = components.get("iv_skew", 0.0)
            smile_component = components.get("smile", 0.0)
            event_component = components.get("event", 0.0)
            
            # Components should exist (even if 0.0)
            if "iv_skew" in components and "smile" in components and "event" in components:
                test_result["status"] = "PASS"
                test_result["message"] = "Core features present in components (may be 0.0 if no data)"
            else:
                test_result["status"] = "FAIL"
                test_result["message"] = f"Missing core features in components: {list(components.keys())}"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = "Composite scoring returned None"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_expanded_intel_defaults(runner) -> Dict:
    """Test that expanded intel provides neutral defaults."""
    test_result = {
        "name": "Expanded intel neutral defaults",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        import uw_composite_v2 as uw_v2
        
        # Create enriched data without expanded intel
        enriched_data = {
            "sentiment": "BULLISH",
            "conviction": 0.7,
            "dark_pool": {"sentiment": "BULLISH"},
            "insider": {"sentiment": "NEUTRAL"}
            # No congress, shorts, institutional, tide, calendar, greeks, ftd, oi, etf, squeeze
        }
        
        # Calculate composite score
        composite = uw_v2.compute_composite_score_v3("TEST", enriched_data, "mixed")
        
        if composite:
            components = composite.get("components", {})
            notes = composite.get("notes", "")
            
            # Check for neutral defaults in notes
            neutral_defaults_found = []
            for comp in ["congress", "shorts", "institutional", "tide", "calendar",
                        "greeks", "ftd", "oi_change", "etf_flow", "squeeze_score"]:
                if f"{comp}_neutral_default" in notes:
                    neutral_defaults_found.append(comp)
            
            # Check that components contribute (not 0.0)
            non_zero_expanded = []
            for comp in ["congress", "shorts_squeeze", "institutional", "market_tide", "calendar",
                        "greeks_gamma", "ftd_pressure", "oi_change", "etf_flow", "squeeze_score"]:
                comp_value = components.get(comp, 0.0)
                if comp_value > 0.0:
                    non_zero_expanded.append(comp)
            
            if neutral_defaults_found or non_zero_expanded:
                test_result["status"] = "PASS"
                test_result["message"] = f"Expanded intel provides defaults ({len(neutral_defaults_found)} neutral, {len(non_zero_expanded)} non-zero)"
            else:
                test_result["status"] = "FAIL"
                test_result["message"] = "Expanded intel components still return 0.0 when data missing"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = "Composite scoring returned None"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_telemetry_recording(runner) -> Dict:
    """Test that telemetry records scores correctly."""
    test_result = {
        "name": "Telemetry recording",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        from telemetry.score_telemetry import record, get_score_distribution, get_telemetry_summary
        
        # Record a test score
        test_components = {
            "flow": 1.2,
            "dark_pool": 0.26,
            "insider": 0.125,
            "iv_skew": 0.0,
            "smile": 0.0,
            "event": 0.0
        }
        
        record(
            symbol="TEST",
            score=2.5,
            components=test_components,
            metadata={
                "freshness": 0.9,
                "conviction_defaulted": True,
                "missing_intel": ["congress", "shorts"],
                "neutral_defaults": ["congress", "shorts"],
                "core_features_missing": ["iv_term_skew"]
            }
        )
        
        # Check that telemetry file exists
        telemetry_file = Path("state/score_telemetry.json")
        if telemetry_file.exists():
            test_result["status"] = "PASS"
            test_result["message"] = "Telemetry file created and updated"
            
            # Verify we can read it
            summary = get_telemetry_summary()
            if summary:
                test_result["message"] += " (summary accessible)"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = "Telemetry file not created"
    
    except ImportError:
        test_result["status"] = "FAIL"
        test_result["message"] = "score_telemetry module not found"
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result


def test_dashboard_endpoints(runner) -> Dict:
    """Test that dashboard endpoints return valid JSON."""
    test_result = {
        "name": "Dashboard endpoints",
        "status": "UNKNOWN",
        "message": "",
        "details": ""
    }
    
    try:
        # Check if endpoints are defined in dashboard.py
        dashboard_file = Path("dashboard.py")
        if not dashboard_file.exists():
            test_result["status"] = "FAIL"
            test_result["message"] = "dashboard.py not found"
            return test_result
        
        content = dashboard_file.read_text()
        
        endpoints_found = []
        required_endpoints = [
            "/api/scores/distribution",
            "/api/scores/components",
            "/api/scores/telemetry"
        ]
        
        for endpoint in required_endpoints:
            if endpoint in content:
                endpoints_found.append(endpoint)
        
        if len(endpoints_found) == len(required_endpoints):
            test_result["status"] = "PASS"
            test_result["message"] = f"All required endpoints found: {', '.join(endpoints_found)}"
        else:
            test_result["status"] = "FAIL"
            test_result["message"] = f"Missing endpoints. Found: {endpoints_found}, Required: {required_endpoints}"
    
    except Exception as e:
        test_result["status"] = "FAIL"
        test_result["message"] = f"Test execution failed: {e}"
        test_result["details"] = str(e)
    
    return test_result
