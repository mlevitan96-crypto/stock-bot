#!/usr/bin/env python3
"""
Test Unusual Whales API endpoints to discover available signals.
Tests endpoints that might exist based on signal components defined in config.
"""

import os
import sys
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

UW_API_KEY = os.getenv("UW_API_KEY")
BASE_URL = "https://api.unusualwhales.com"

if not UW_API_KEY:
    print("❌ UW_API_KEY not found in environment")
    sys.exit(1)

headers = {"Authorization": f"Bearer {UW_API_KEY}"}
test_ticker = "AAPL"  # Use AAPL as test ticker

# Endpoints to test based on signal components
endpoints_to_test = [
    # High Priority
    f"/api/insider/{test_ticker}",
    f"/api/insider-trades/{test_ticker}",
    f"/api/congress/{test_ticker}",
    f"/api/politician-trades/{test_ticker}",
    f"/api/calendar/{test_ticker}",
    f"/api/events/{test_ticker}",
    f"/api/earnings/{test_ticker}",
    f"/api/stock/{test_ticker}/iv-rank",
    f"/api/stock/{test_ticker}/volatility/rank",
    f"/api/stock/{test_ticker}/iv-term-structure",
    f"/api/stock/{test_ticker}/iv-skew",
    f"/api/stock/{test_ticker}/volatility-smile",
    f"/api/stock/{test_ticker}/smile",
    f"/api/stock/{test_ticker}/oi-change",
    
    # Medium Priority
    f"/api/alerts/{test_ticker}",
    f"/api/unusual-activity/{test_ticker}",
    f"/api/stock/{test_ticker}/option-chain",
    f"/api/options/{test_ticker}/chain",
    f"/api/market/regime",
    f"/api/market/vix-term-structure",
    f"/api/option-trades/sweeps/{test_ticker}",
    f"/api/option-trades/blocks/{test_ticker}",
    f"/api/volume-alerts/{test_ticker}",
    f"/api/unusual-volume/{test_ticker}",
    
    # Additional potential endpoints
    f"/api/stock/{test_ticker}/unusual-activity",
    f"/api/stock/{test_ticker}/sentiment",
    f"/api/stock/{test_ticker}/momentum",
    f"/api/stock/{test_ticker}/analyst-ratings",
]

def test_endpoint(endpoint):
    """Test if an endpoint exists and returns data."""
    url = f"{BASE_URL}{endpoint}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            return {
                "status": "✅ AVAILABLE",
                "status_code": 200,
                "response_keys": list(data.keys()) if isinstance(data, dict) else "array",
                "sample": str(data)[:200] if data else "empty"
            }
        elif r.status_code == 404:
            return {"status": "❌ NOT FOUND", "status_code": 404}
        elif r.status_code == 429:
            return {"status": "⚠️  RATE LIMITED", "status_code": 429}
        else:
            return {
                "status": f"⚠️  ERROR ({r.status_code})",
                "status_code": r.status_code,
                "message": r.text[:200] if r.text else "No message"
            }
    except Exception as e:
        return {"status": f"❌ EXCEPTION", "error": str(e)[:200]}

def main():
    print("=" * 80)
    print("UNUSUAL WHALES API ENDPOINT DISCOVERY")
    print("=" * 80)
    print(f"Testing endpoints for ticker: {test_ticker}")
    print(f"Base URL: {BASE_URL}")
    print()
    
    results = {}
    
    for endpoint in endpoints_to_test:
        print(f"Testing: {endpoint}...", end=" ")
        result = test_endpoint(endpoint)
        results[endpoint] = result
        print(result["status"])
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    available = [ep for ep, r in results.items() if r.get("status_code") == 200]
    not_found = [ep for ep, r in results.items() if r.get("status_code") == 404]
    errors = [ep for ep, r in results.items() if r.get("status_code") not in [200, 404] and "EXCEPTION" not in r.get("status", "")]
    
    print(f"\n✅ Available Endpoints ({len(available)}):")
    for ep in available:
        result = results[ep]
        print(f"  {ep}")
        if "response_keys" in result:
            print(f"    Keys: {result['response_keys']}")
    
    print(f"\n❌ Not Found ({len(not_found)}):")
    for ep in not_found[:10]:  # Limit output
        print(f"  {ep}")
    if len(not_found) > 10:
        print(f"  ... and {len(not_found) - 10} more")
    
    if errors:
        print(f"\n⚠️  Errors ({len(errors)}):")
        for ep in errors[:5]:
            result = results[ep]
            print(f"  {ep}: {result.get('status', 'Unknown')}")
    
    # Save detailed results
    output_file = Path("data/uw_endpoint_discovery.json")
    output_file.parent.mkdir(exist_ok=True)
    with output_file.open("w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if available:
        print("\n✅ Found available endpoints - consider adding to uw_flow_daemon.py:")
        for ep in available:
            print(f"  - {ep}")
    else:
        print("\n⚠️  No new endpoints found. All tested endpoints returned 404.")
        print("   This could mean:")
        print("   1. Endpoints use different naming conventions")
        print("   2. Endpoints require different parameters")
        print("   3. Endpoints are not available in your subscription tier")

if __name__ == "__main__":
    main()
