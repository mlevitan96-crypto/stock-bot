#!/usr/bin/env python3
"""
Comprehensive UW API Endpoint Test
Tests all endpoints used by the system to verify they're working.
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

UW_API_KEY = os.getenv("UW_API_KEY")
BASE_URL = "https://api.unusualwhales.com"

if not UW_API_KEY:
    print("ERROR: UW_API_KEY not found in environment")
    sys.exit(1)

headers = {"Authorization": f"Bearer {UW_API_KEY}"}
test_ticker = "AAPL"  # Use AAPL as test ticker

# Core endpoints used by the system
endpoints_to_test = [
    # Core trading signals (from uw_flow_daemon.py)
    {
        "name": "option_flow_alerts",
        "endpoint": "/api/option-trades/flow-alerts",
        "method": "GET",
        "params": {}
    },
    {
        "name": "dark_pool",
        "endpoint": f"/api/darkpool/{test_ticker}",
        "method": "GET",
        "params": {}
    },
    {
        "name": "greeks",
        "endpoint": f"/api/stock/{test_ticker}/greeks",
        "method": "GET",
        "params": {}
    },
    {
        "name": "top_net_impact",
        "endpoint": "/api/market/top-net-impact",
        "method": "GET",
        "params": {}
    },
    
    # Additional endpoints from contracts
    {
        "name": "market_tide",
        "endpoint": "/api/market/market-tide",
        "method": "GET",
        "params": {}
    },
    {
        "name": "greek_exposure",
        "endpoint": f"/api/stock/{test_ticker}/greek-exposure",
        "method": "GET",
        "params": {}
    },
    {
        "name": "oi_change",
        "endpoint": f"/api/stock/{test_ticker}/oi-change",
        "method": "GET",
        "params": {}
    },
    {
        "name": "etf_flow",
        "endpoint": f"/api/etfs/{test_ticker}/in-outflow",
        "method": "GET",
        "params": {}
    },
    {
        "name": "iv_rank",
        "endpoint": f"/api/stock/{test_ticker}/iv-rank",
        "method": "GET",
        "params": {}
    },
]

def test_endpoint(endpoint_info):
    """Test a single endpoint and return results."""
    name = endpoint_info["name"]
    endpoint = endpoint_info["endpoint"]
    method = endpoint_info.get("method", "GET")
    params = endpoint_info.get("params", {})
    
    result = {
        "name": name,
        "endpoint": endpoint,
        "status": "unknown",
        "status_code": None,
        "response_time_ms": None,
        "has_data": False,
        "error": None,
        "sample_data": None
    }
    
    try:
        url = f"{BASE_URL}{endpoint}"
        start_time = datetime.now()
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            response = requests.post(url, headers=headers, json=params, timeout=10)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        result["status_code"] = response.status_code
        result["response_time_ms"] = round(response_time, 2)
        
        if response.status_code == 200:
            try:
                data = response.json()
                result["status"] = "success"
                result["has_data"] = bool(data)
                
                # Store sample data (first few items if it's a list)
                if isinstance(data, list) and len(data) > 0:
                    result["sample_data"] = data[0] if len(data) > 0 else None
                elif isinstance(data, dict):
                    # Store a subset of keys to avoid huge responses
                    sample = {}
                    for key in list(data.keys())[:5]:
                        sample[key] = data[key]
                    result["sample_data"] = sample
                else:
                    result["sample_data"] = data
                    
            except json.JSONDecodeError:
                result["status"] = "error"
                result["error"] = "Invalid JSON response"
        elif response.status_code == 401:
            result["status"] = "error"
            result["error"] = "Authentication failed - check API key"
        elif response.status_code == 403:
            result["status"] = "error"
            result["error"] = "Forbidden - check API permissions"
        elif response.status_code == 404:
            result["status"] = "error"
            result["error"] = "Endpoint not found"
        elif response.status_code == 429:
            result["status"] = "error"
            result["error"] = "Rate limit exceeded"
        else:
            result["status"] = "error"
            result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
            
    except requests.exceptions.Timeout:
        result["status"] = "error"
        result["error"] = "Request timeout"
    except requests.exceptions.ConnectionError:
        result["status"] = "error"
        result["error"] = "Connection error"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def main():
    """Test all endpoints and generate report."""
    print("=" * 60)
    print("UW API ENDPOINT TEST")
    print("=" * 60)
    print(f"Testing {len(endpoints_to_test)} endpoints...")
    print(f"Test ticker: {test_ticker}")
    print(f"Base URL: {BASE_URL}")
    print()
    
    results = []
    success_count = 0
    error_count = 0
    
    for endpoint_info in endpoints_to_test:
        print(f"Testing {endpoint_info['name']}...", end=" ", flush=True)
        result = test_endpoint(endpoint_info)
        results.append(result)
        
        if result["status"] == "success":
            print(f"OK ({result['response_time_ms']:.0f}ms)")
            success_count += 1
        else:
            print(f"FAILED: {result.get('error', 'Unknown error')}")
            error_count += 1
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total endpoints: {len(endpoints_to_test)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {error_count}")
    print()
    
    # Generate detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_ticker": test_ticker,
        "summary": {
            "total": len(endpoints_to_test),
            "successful": success_count,
            "failed": error_count
        },
        "results": results
    }
    
    # Save report
    report_file = "uw_endpoint_test_results.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Detailed report saved to: {report_file}")
    print()
    
    # Print failed endpoints
    if error_count > 0:
        print("FAILED ENDPOINTS:")
        for result in results:
            if result["status"] != "success":
                print(f"  - {result['name']}: {result.get('error', 'Unknown')}")
        print()
    
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

