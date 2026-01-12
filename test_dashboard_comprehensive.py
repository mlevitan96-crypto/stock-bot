#!/usr/bin/env python3
"""
Comprehensive Dashboard Audit Script
Tests all dashboard endpoints and identifies issues
"""

import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime

def test_endpoint(name, url, method="GET", data=None, timeout=5):
    """Test a single endpoint"""
    try:
        if method == "GET":
            resp = requests.get(url, timeout=timeout)
        else:
            resp = requests.post(url, json=data, timeout=timeout)
        
        status = "✅" if resp.status_code == 200 else "❌"
        print(f"{status} {name}: {resp.status_code}")
        
        if resp.status_code == 200:
            try:
                data = resp.json()
                # Check if response has expected structure
                if isinstance(data, dict) and "error" in data:
                    print(f"   ⚠️  Response contains error: {data.get('error')}")
                return True, data
            except:
                print(f"   ⚠️  Response is not valid JSON")
                return True, None
        else:
            print(f"   ❌ Status: {resp.status_code}")
            try:
                error_data = resp.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {resp.text[:200]}")
            return False, None
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: Connection refused (dashboard not running?)")
        return False, None
    except requests.exceptions.Timeout:
        print(f"❌ {name}: Timeout after {timeout}s")
        return False, None
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__}: {str(e)}")
        return False, None

def check_data_sources():
    """Check if required data sources exist"""
    print("\n" + "="*60)
    print("CHECKING DATA SOURCES")
    print("="*60)
    
    sources = {
        "state/position_metadata.json": "Position metadata",
        "state/bot_heartbeat.json": "Bot heartbeat",
        "state/closed_positions.json": "Closed positions",
        "state/health.json": "System health",
        "logs/attribution.jsonl": "Attribution logs",
        "data/live_orders.jsonl": "Live orders",
        "logs/orders.jsonl": "Order logs",
        "logs/trading.jsonl": "Trading logs",
        "logs/xai_*.jsonl": "XAI logs (pattern)",
    }
    
    for path_str, desc in sources.items():
        if "*" in path_str:
            # Pattern match
            import glob
            matches = glob.glob(path_str)
            if matches:
                print(f"✅ {desc}: {len(matches)} file(s) found")
            else:
                print(f"⚠️  {desc}: No files found")
        else:
            path = Path(path_str)
            if path.exists():
                size = path.stat().st_size
                print(f"✅ {desc}: {path_str} ({size} bytes)")
            else:
                print(f"⚠️  {desc}: {path_str} not found")

def check_imports():
    """Check if critical imports work"""
    print("\n" + "="*60)
    print("CHECKING IMPORTS")
    print("="*60)
    
    imports = [
        ("flask", "Flask"),
        ("alpaca_trade_api", "Alpaca API"),
        ("config.registry", "Config registry"),
        ("executive_summary_generator", "Executive summary"),
        ("sre_monitoring", "SRE monitoring"),
        ("sre_diagnostics", "SRE diagnostics"),
        ("telemetry.score_telemetry", "Score telemetry"),
        ("uw_composite_v2", "UW composite"),
        ("shadow_tracker", "Shadow tracker"),
        ("signal_history_storage", "Signal history"),
    ]
    
    for module, name in imports:
        try:
            __import__(module)
            print(f"✅ {name}: OK")
        except ImportError as e:
            print(f"❌ {name}: ImportError - {str(e)}")
        except Exception as e:
            print(f"⚠️  {name}: {type(e).__name__} - {str(e)}")

def main():
    print("="*60)
    print("COMPREHENSIVE DASHBOARD AUDIT")
    print("="*60)
    print(f"Time: {datetime.now().isoformat()}")
    
    # Check if dashboard is running
    base_url = "http://localhost:5000"
    
    print("\n" + "="*60)
    print("TESTING DASHBOARD ENDPOINTS")
    print("="*60)
    
    endpoints = [
        ("Root", f"{base_url}/"),
        ("Health", f"{base_url}/health"),
        ("Positions API", f"{base_url}/api/positions"),
        ("Closed Positions", f"{base_url}/api/closed_positions"),
        ("System Health", f"{base_url}/api/system/health"),
        ("SRE Health", f"{base_url}/api/sre/health"),
        ("XAI Auditor", f"{base_url}/api/xai/auditor"),
        ("XAI Health", f"{base_url}/api/xai/health"),
        ("Executive Summary", f"{base_url}/api/executive_summary"),
        ("Health Status", f"{base_url}/api/health_status"),
        ("Scores Distribution", f"{base_url}/api/scores/distribution"),
        ("Scores Components", f"{base_url}/api/scores/components"),
        ("Scores Telemetry", f"{base_url}/api/scores/telemetry"),
        ("Failure Points", f"{base_url}/api/failure_points"),
        ("Signal History", f"{base_url}/api/signal_history"),
    ]
    
    results = {}
    for name, url in endpoints:
        success, data = test_endpoint(name, url)
        results[name] = {"success": success, "data": data}
        time.sleep(0.1)  # Small delay between requests
    
    # Check data sources
    check_data_sources()
    
    # Check imports
    check_imports()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    successful = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    print(f"Endpoints tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    
    if successful < total:
        print("\n❌ FAILED ENDPOINTS:")
        for name, result in results.items():
            if not result["success"]:
                print(f"   - {name}")
    
    # Check for common issues
    print("\n" + "="*60)
    print("COMMON ISSUES CHECK")
    print("="*60)
    
    # Check if Alpaca API is configured
    alpaca_key = Path(".env").exists() or any(
        k in ["ALPACA_API_KEY", "ALPACA_KEY"] 
        for k in ["ALPACA_API_KEY", "ALPACA_KEY"]
    )
    if not alpaca_key:
        print("⚠️  Alpaca API credentials may not be configured")
    
    # Check if critical files exist
    critical_files = [
        "state/position_metadata.json",
        "state/bot_heartbeat.json",
    ]
    
    missing_critical = []
    for f in critical_files:
        if not Path(f).exists():
            missing_critical.append(f)
    
    if missing_critical:
        print(f"⚠️  Missing critical files: {', '.join(missing_critical)}")
    else:
        print("✅ All critical files present")
    
    # Save results
    results_file = Path("dashboard_audit_results.json")
    with results_file.open("w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": {k: {"success": v["success"]} for k, v in results.items()},
            "summary": {
                "total": total,
                "successful": successful,
                "failed": total - successful
            }
        }, f, indent=2)
    
    print(f"\n✅ Results saved to {results_file}")

if __name__ == "__main__":
    main()
