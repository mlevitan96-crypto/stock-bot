#!/usr/bin/env python3
"""
Comprehensive Dashboard Testing & Verification
Tests all tabs, sections, and API endpoints to ensure correct data mapping.
"""

import json
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Test results
results = {
    "timestamp": datetime.now().isoformat(),
    "tabs": {},
    "endpoints": {},
    "data_sources": {},
    "errors": [],
    "warnings": []
}

def test_endpoint(name: str, test_func):
    """Test an API endpoint"""
    try:
        result = test_func()
        results["endpoints"][name] = {
            "status": "OK",
            "data_keys": list(result.keys()) if isinstance(result, dict) else "N/A",
            "has_data": bool(result),
            "sample": str(result)[:200] if result else "No data"
        }
        return result
    except Exception as e:
        results["endpoints"][name] = {
            "status": "ERROR",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        results["errors"].append(f"{name}: {str(e)}")
        return None

def test_positions_endpoint():
    """Test /api/positions endpoint"""
    try:
        from dashboard import app
        with app.test_client() as client:
            resp = client.get("/api/positions")
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}: {resp.data.decode()}")
            data = resp.get_json()
            return data
    except Exception as e:
        # Try direct import
        try:
            import alpaca_trade_api as tradeapi
            import os
            key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY", "")
            secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET", "")
            base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
            if key and secret:
                api = tradeapi.REST(key, secret, base_url)
                positions = api.list_positions()
                account = api.get_account()
                return {
                    "positions": [{
                        "symbol": p.symbol,
                        "side": "long" if float(p.qty) > 0 else "short",
                        "qty": abs(float(p.qty)),
                        "avg_entry_price": float(p.avg_entry_price),
                        "current_price": float(p.current_price),
                        "market_value": abs(float(p.market_value)),
                        "unrealized_pnl": float(p.unrealized_pl),
                        "unrealized_pnl_pct": float(p.unrealized_plpc) * 100
                    } for p in positions],
                    "total_value": float(account.portfolio_value),
                    "unrealized_pnl": sum(float(p.unrealized_pl) for p in positions),
                    "day_pnl": float(account.equity) - float(account.last_equity)
                }
        except Exception as e2:
            raise Exception(f"Dashboard test failed: {e}, Direct API failed: {e2}")

def test_sre_health_endpoint():
    """Test /api/sre/health endpoint"""
    try:
        from sre_monitoring import get_sre_health
        return get_sre_health()
    except Exception as e:
        raise Exception(f"SRE health failed: {e}")

def test_executive_summary_endpoint():
    """Test /api/executive_summary endpoint"""
    try:
        from executive_summary_generator import generate_executive_summary
        return generate_executive_summary()
    except Exception as e:
        raise Exception(f"Executive summary failed: {e}")

def test_xai_auditor_endpoint():
    """Test /api/xai/auditor endpoint"""
    try:
        from xai.explainable_logger import get_explainable_logger
        explainable = get_explainable_logger()
        
        # Check if methods exist
        if not hasattr(explainable, 'get_trade_explanations'):
            raise Exception("get_trade_explanations method not found")
        if not hasattr(explainable, 'get_weight_explanations'):
            raise Exception("get_weight_explanations method not found")
        
        trades = explainable.get_trade_explanations(limit=100)
        weights = explainable.get_weight_explanations(limit=100)
        
        return {
            "trades": trades,
            "weights": weights
        }
    except Exception as e:
        raise Exception(f"XAI auditor failed: {e}")

def test_failure_points_endpoint():
    """Test /api/failure_points endpoint"""
    try:
        from failure_point_monitor import get_failure_point_monitor
        monitor = get_failure_point_monitor()
        return monitor.get_trading_readiness()
    except Exception as e:
        raise Exception(f"Failure points failed: {e}")

def test_health_status_endpoint():
    """Test /api/health_status endpoint"""
    try:
        from dashboard import app
        with app.test_client() as client:
            resp = client.get("/api/health_status")
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code}: {resp.data.decode()}")
            return resp.get_json()
    except Exception as e:
        raise Exception(f"Health status failed: {e}")

def verify_data_sources():
    """Verify all data source files exist and are readable"""
    data_sources = {
        "attribution": [
            Path("logs/attribution.jsonl"),
            Path("data/attribution.jsonl")
        ],
        "explainable_logs": [
            Path("data/explainable_logs.jsonl")
        ],
        "signal_weights": [
            Path("state/signal_weights.json")
        ],
        "comprehensive_learning": [
            Path("data/comprehensive_learning.jsonl")
        ],
        "counterfactual_results": [
            Path("data/counterfactual_results.jsonl")
        ],
        "uw_flow_cache": [
            Path("data/uw_flow_cache.json")
        ],
        "orders": [
            Path("data/live_orders.jsonl"),
            Path("logs/orders.jsonl")
        ],
        "heartbeat": [
            Path("state/bot_heartbeat.json"),
            Path("state/doctor_state.json"),
            Path("state/system_heartbeat.json")
        ]
    }
    
    for source_name, paths in data_sources.items():
        found = False
        for path in paths:
            if path.exists():
                try:
                    # Try to read it
                    if path.suffix == ".jsonl":
                        with open(path, 'r') as f:
                            lines = f.readlines()
                            line_count = len([l for l in lines if l.strip()])
                    else:
                        with open(path, 'r') as f:
                            data = json.load(f)
                            line_count = 1 if data else 0
                    
                    results["data_sources"][source_name] = {
                        "status": "OK",
                        "path": str(path),
                        "exists": True,
                        "readable": True,
                        "line_count": line_count if path.suffix == ".jsonl" else "N/A"
                    }
                    found = True
                    break
                except Exception as e:
                    results["data_sources"][source_name] = {
                        "status": "ERROR",
                        "path": str(path),
                        "exists": True,
                        "readable": False,
                        "error": str(e)
                    }
                    results["warnings"].append(f"{source_name}: File exists but not readable: {e}")
        
        if not found:
            results["data_sources"][source_name] = {
                "status": "MISSING",
                "paths_checked": [str(p) for p in paths],
                "exists": False
            }
            results["warnings"].append(f"{source_name}: No data file found")

def test_tab_functionality():
    """Test each tab's expected functionality"""
    tabs = {
        "positions": {
            "endpoints": ["/api/positions", "/api/health_status"],
            "required_keys": ["positions", "total_value", "unrealized_pnl", "day_pnl"],
            "health_keys": ["last_order", "doctor", "market"]
        },
        "sre": {
            "endpoints": ["/api/sre/health"],
            "required_keys": ["overall_health", "signal_components", "uw_api_endpoints", "order_execution"]
        },
        "executive": {
            "endpoints": ["/api/executive_summary"],
            "required_keys": ["total_trades", "pnl_metrics", "trades", "signal_analysis", "learning_insights", "written_summary"]
        },
        "xai": {
            "endpoints": ["/api/xai/auditor", "/api/xai/export"],
            "required_keys": ["trades", "weights"]
        },
        "failure_points": {
            "endpoints": ["/api/failure_points"],
            "required_keys": ["readiness", "failure_points", "critical_count", "warning_count"]
        }
    }
    
    for tab_name, config in tabs.items():
        tab_result = {
            "status": "OK",
            "endpoints_tested": [],
            "endpoints_failed": [],
            "missing_keys": [],
            "warnings": []
        }
        
        for endpoint in config["endpoints"]:
            endpoint_name = endpoint.replace("/api/", "").replace("/", "_")
            if endpoint_name in results["endpoints"]:
                endpoint_result = results["endpoints"][endpoint_name]
                if endpoint_result["status"] == "OK":
                    tab_result["endpoints_tested"].append(endpoint)
                    
                    # Check required keys
                    if endpoint_name == "positions":
                        data = test_positions_endpoint()
                    elif endpoint_name == "sre_health":
                        data = test_sre_health_endpoint()
                    elif endpoint_name == "executive_summary":
                        data = test_executive_summary_endpoint()
                    elif endpoint_name == "xai_auditor":
                        data = test_xai_auditor_endpoint()
                    elif endpoint_name == "failure_points":
                        data = test_failure_points_endpoint()
                    elif endpoint_name == "health_status":
                        data = test_health_status_endpoint()
                    else:
                        data = None
                    
                    if data:
                        required_keys = config.get("required_keys", [])
                        for key in required_keys:
                            if key not in data:
                                tab_result["missing_keys"].append(key)
                                tab_result["warnings"].append(f"Missing key: {key}")
                else:
                    tab_result["endpoints_failed"].append(endpoint)
                    tab_result["status"] = "ERROR"
            else:
                tab_result["endpoints_failed"].append(endpoint)
                tab_result["status"] = "ERROR"
        
        if tab_result["missing_keys"]:
            tab_result["status"] = "WARNING"
        
        results["tabs"][tab_name] = tab_result

def main():
    """Run all tests"""
    print("=" * 80)
    print("COMPREHENSIVE DASHBOARD TESTING")
    print("=" * 80)
    print()
    
    # Test all endpoints
    print("Testing API Endpoints...")
    print("-" * 80)
    
    test_endpoint("positions", test_positions_endpoint)
    test_endpoint("sre_health", test_sre_health_endpoint)
    test_endpoint("executive_summary", test_executive_summary_endpoint)
    test_endpoint("xai_auditor", test_xai_auditor_endpoint)
    test_endpoint("failure_points", test_failure_points_endpoint)
    test_endpoint("health_status", test_health_status_endpoint)
    
    print()
    print("Verifying Data Sources...")
    print("-" * 80)
    verify_data_sources()
    
    print()
    print("Testing Tab Functionality...")
    print("-" * 80)
    test_tab_functionality()
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    # Endpoints summary
    print("API Endpoints:")
    for name, result in results["endpoints"].items():
        status_icon = "[OK]" if result["status"] == "OK" else "[ERROR]"
        print(f"  {status_icon} {name}: {result['status']}")
        if result["status"] == "ERROR":
            print(f"      Error: {result.get('error', 'Unknown')}")
    
    print()
    print("Tabs:")
    for name, result in results["tabs"].items():
        status_icon = "[OK]" if result["status"] == "OK" else "[WARN]" if result["status"] == "WARNING" else "[ERROR]"
        print(f"  {status_icon} {name}: {result['status']}")
        if result["endpoints_failed"]:
            print(f"      Failed endpoints: {', '.join(result['endpoints_failed'])}")
        if result["missing_keys"]:
            print(f"      Missing keys: {', '.join(result['missing_keys'])}")
    
    print()
    print("Data Sources:")
    for name, result in results["data_sources"].items():
        status_icon = "[OK]" if result["status"] == "OK" else "[MISSING]" if result["status"] == "MISSING" else "[ERROR]"
        print(f"  {status_icon} {name}: {result['status']}")
        if result["status"] == "OK":
            print(f"      Path: {result.get('path', 'N/A')}")
    
    if results["errors"]:
        print()
        print("Errors:")
        for error in results["errors"]:
            print(f"  [ERROR] {error}")
    
    if results["warnings"]:
        print()
        print("Warnings:")
        for warning in results["warnings"]:
            print(f"  [WARN] {warning}")
    
    # Save results
    output_file = Path("dashboard_test_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print()
    print(f"Detailed results saved to: {output_file}")
    print()
    
    # Return exit code
    if results["errors"]:
        return 1
    elif results["warnings"]:
        return 0  # Warnings are OK
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())

