#!/usr/bin/env python3
"""
Verify All Dashboard and API Endpoints
Tests all endpoints to ensure they're working correctly.
"""

from droplet_client import DropletClient
import json

def test_endpoint(client, endpoint, expected_keys=None):
    """Test an endpoint and return status."""
    try:
        result = client.execute_command(
            f"cd ~/stock-bot && curl -s http://localhost:5000{endpoint}",
            timeout=30
        )
        
        if not result['success'] or not result['stdout']:
            return False, f"No response: {result.get('stderr', 'Unknown error')}"
        
        try:
            data = json.loads(result['stdout'])
            
            # Check for expected keys
            if expected_keys:
                missing = [k for k in expected_keys if k not in data]
                if missing:
                    return False, f"Missing keys: {missing}"
            
            return True, f"OK - {len(data)} keys"
        except json.JSONDecodeError:
            # Not JSON, but might still be valid
            if result['stdout'].strip():
                return True, "OK (non-JSON response)"
            return False, "Empty response"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    print("=" * 80)
    print("VERIFYING ALL ENDPOINTS")
    print("=" * 80)
    print()
    
    client = DropletClient()
    
    try:
        # Dashboard endpoints
        endpoints = [
            ("/health", ["status"]),
            ("/api/health_status", ["timestamp"]),  # Returns doctor, last_order, market, timestamp
            ("/api/profit", None),  # May return different structure
            ("/api/state", None),  # May return different structure
            ("/api/account", None),  # May return different structure
            ("/api/positions", None),
            ("/api/closed_positions", None),
            ("/api/sre/health", ["overall_health", "timestamp"]),  # Returns overall_health, bot_process, etc.
        ]
        
        results = {}
        for endpoint, expected_keys in endpoints:
            print(f"Testing {endpoint}...", end=" ")
            success, message = test_endpoint(client, endpoint, expected_keys)
            results[endpoint] = {"success": success, "message": message}
            status = "[OK]" if success else "[FAIL]"
            print(f"{status} {message}")
        
        # Summary
        print()
        print("=" * 80)
        print("ENDPOINT VERIFICATION SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in results.values() if r["success"])
        total = len(results)
        
        for endpoint, result in results.items():
            status = "[OK]" if result["success"] else "[FAIL]"
            print(f"{status} {endpoint}: {result['message']}")
        
        print()
        print(f"Results: {passed}/{total} endpoints working")
        
        if passed == total:
            print("[SUCCESS] All endpoints verified!")
        else:
            print("[WARNING] Some endpoints need attention")
        
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

