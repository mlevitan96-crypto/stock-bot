#!/usr/bin/env python3
"""
Comprehensive Dashboard Fix
Fixes all UW API endpoint monitoring and dashboard issues
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_dashboard_code():
    """Verify dashboard.py has all required components"""
    dashboard_file = Path("dashboard.py")
    if not dashboard_file.exists():
        return {"error": "dashboard.py not found"}
    
    content = dashboard_file.read_text()
    
    issues = []
    fixes_needed = []
    
    # Check 1: UW endpoints in SRE health response
    if "uw_api_endpoints" not in content:
        issues.append("Dashboard doesn't display uw_api_endpoints from SRE health")
        fixes_needed.append("Add uw_api_endpoints display in SRE dashboard HTML")
    
    # Check 2: SRE endpoint properly calls get_sre_health
    if "from sre_monitoring import get_sre_health" not in content:
        if "get_sre_health()" in content:
            # It's imported differently, check if it works
            pass
        else:
            issues.append("Dashboard doesn't import get_sre_health from sre_monitoring")
            fixes_needed.append("Add: from sre_monitoring import get_sre_health")
    
    # Check 3: UW API endpoints section in SRE dashboard HTML
    if "UW API Endpoints Health" not in content:
        issues.append("SRE dashboard HTML missing UW API Endpoints section")
        fixes_needed.append("Add UW API Endpoints section to SRE_DASHBOARD_HTML")
    
    # Check 4: Frontend JavaScript renders UW endpoints
    if "data.uw_api_endpoints" not in content:
        issues.append("Frontend JavaScript doesn't render uw_api_endpoints")
        fixes_needed.append("Add JavaScript to render uw_api_endpoints in updateSREDashboard()")
    
    return {
        "issues": issues,
        "fixes_needed": fixes_needed,
        "all_ok": len(issues) == 0
    }

def check_sre_monitoring():
    """Verify sre_monitoring.py properly returns UW endpoints"""
    sre_file = Path("sre_monitoring.py")
    if not sre_file.exists():
        return {"error": "sre_monitoring.py not found"}
    
    content = sre_file.read_text()
    
    issues = []
    
    # Check 1: check_uw_api_health method exists
    if "def check_uw_api_health" not in content:
        issues.append("check_uw_api_health method not found")
    
    # Check 2: get_comprehensive_health includes uw_api_endpoints
    if "uw_api_endpoints" not in content:
        issues.append("get_comprehensive_health doesn't include uw_api_endpoints")
    
    # Check 3: Uses UW_ENDPOINT_CONTRACTS
    if "UW_ENDPOINT_CONTRACTS" not in content:
        issues.append("sre_monitoring doesn't use UW_ENDPOINT_CONTRACTS from config")
    
    return {
        "issues": issues,
        "all_ok": len(issues) == 0
    }

def test_sre_health_endpoint():
    """Test if /api/sre/health returns UW endpoints"""
    try:
        import requests
        resp = requests.get("http://localhost:5000/api/sre/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            has_uw_endpoints = "uw_api_endpoints" in data
            uw_endpoints_count = len(data.get("uw_api_endpoints", {}))
            return {
                "endpoint_working": True,
                "has_uw_endpoints": has_uw_endpoints,
                "uw_endpoints_count": uw_endpoints_count,
                "all_ok": has_uw_endpoints and uw_endpoints_count > 0
            }
        else:
            return {
                "endpoint_working": False,
                "status_code": resp.status_code,
                "all_ok": False
            }
    except Exception as e:
        return {
            "endpoint_working": False,
            "error": str(e),
            "all_ok": False
        }

def main():
    print("=" * 70)
    print("COMPREHENSIVE DASHBOARD FIX ANALYSIS")
    print("=" * 70)
    print()
    
    # 1. Check dashboard code
    print("[1] Checking dashboard.py...")
    dashboard_check = check_dashboard_code()
    if "error" in dashboard_check:
        print(f"   ❌ {dashboard_check['error']}")
    elif dashboard_check["all_ok"]:
        print("   ✅ Dashboard code structure is correct")
    else:
        print("   ⚠️  Dashboard code issues found:")
        for issue in dashboard_check["issues"]:
            print(f"      - {issue}")
        print("   Fixes needed:")
        for fix in dashboard_check["fixes_needed"]:
            print(f"      - {fix}")
    print()
    
    # 2. Check sre_monitoring
    print("[2] Checking sre_monitoring.py...")
    sre_check = check_sre_monitoring()
    if "error" in sre_check:
        print(f"   ❌ {sre_check['error']}")
    elif sre_check["all_ok"]:
        print("   ✅ sre_monitoring.py structure is correct")
    else:
        print("   ⚠️  sre_monitoring.py issues found:")
        for issue in sre_check["issues"]:
            print(f"      - {issue}")
    print()
    
    # 3. Test SRE health endpoint
    print("[3] Testing /api/sre/health endpoint...")
    endpoint_test = test_sre_health_endpoint()
    if endpoint_test["endpoint_working"]:
        print("   ✅ Endpoint is responding")
        if endpoint_test["has_uw_endpoints"]:
            print(f"   ✅ UW endpoints included ({endpoint_test['uw_endpoints_count']} endpoints)")
        else:
            print("   ❌ UW endpoints NOT in response")
    else:
        print(f"   ❌ Endpoint not working: {endpoint_test.get('error', 'unknown')}")
    print()
    
    # 4. Summary
    print("=" * 70)
    all_checks_ok = (
        dashboard_check.get("all_ok", False) and
        sre_check.get("all_ok", False) and
        endpoint_test.get("all_ok", False)
    )
    
    if all_checks_ok:
        print("✅ ALL CHECKS PASSED - Dashboard and UW monitoring should be working")
    else:
        print("❌ ISSUES FOUND - See details above")
        print()
        print("RECOMMENDED FIXES:")
        print("1. Ensure sre_monitoring.py's get_comprehensive_health() includes:")
        print("   result['uw_api_endpoints'] = self.check_uw_api_health()")
        print("2. Ensure dashboard.py's /api/sre/health calls get_sre_health()")
        print("3. Ensure SRE dashboard HTML displays uw_api_endpoints")
        print("4. Restart dashboard after fixes")
    print("=" * 70)

if __name__ == "__main__":
    main()
