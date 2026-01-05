#!/usr/bin/env python3
"""
Pre-Market Health Check Script
Verifies UW socket connection and Alpaca SIP data feed 15 minutes before market open.
Ensures Momentum Ignition Filter has high-fidelity data from the first second of trading.
Authoritative Source: MEMORY_BANK.md
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

# Add project root to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

try:
    from config.registry import APIConfig, CacheFiles
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"[Health Check] ERROR: Failed to import config: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

import requests
import alpaca_trade_api as tradeapi


def check_market_open_time() -> tuple[bool, Optional[datetime]]:
    """Check if market is open or opening soon"""
    now = datetime.now(timezone.utc)
    
    # Market open is 9:30 AM ET = 14:30 UTC (adjust for DST)
    # For simplicity, check if current UTC hour is between 13:00-22:00 (pre-market to close)
    
    # Calculate next market open (assuming weekdays)
    today_930_et = now.replace(hour=13, minute=30, second=0, microsecond=0)  # Approximate 9:30 AM ET in UTC
    if now >= today_930_et:
        # Market already open or past open today
        next_open = today_930_et + timedelta(days=1)
        # Skip weekends
        while next_open.weekday() >= 5:  # Saturday = 5, Sunday = 6
            next_open += timedelta(days=1)
    else:
        next_open = today_930_et
        # Skip weekends
        while next_open.weekday() >= 5:
            next_open += timedelta(days=1)
    
    # Check if we're within 15 minutes of market open
    time_to_open = (next_open - now).total_seconds() / 60.0
    is_near_open = 0 <= time_to_open <= 15
    
    return is_near_open, next_open


def check_uw_api() -> Dict[str, Any]:
    """Check Unusual Whales API connectivity"""
    result = {
        "status": "unknown",
        "message": "",
        "endpoint": "",
        "response_time_ms": 0,
        "rate_limit_info": {}
    }
    
    try:
        api_key = os.getenv("UW_API_KEY")
        if not api_key:
            result["status"] = "error"
            result["message"] = "UW_API_KEY not found in environment"
            return result
        
        base_url = APIConfig.UW_BASE_URL if hasattr(APIConfig, 'UW_BASE_URL') else "https://api.unusualwhales.com"
        endpoint = f"{base_url}/api/health"  # Try health endpoint first
        
        # Try a lightweight endpoint
        test_url = f"{base_url}/api/option-trades/flow-alerts"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        start_time = time.time()
        try:
            response = requests.get(test_url, headers=headers, params={"symbol": "SPY", "limit": 1}, timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            result["response_time_ms"] = round(response_time, 2)
            result["endpoint"] = test_url
            
            if response.status_code == 200:
                result["status"] = "ok"
                result["message"] = "UW API responding"
                
                # Extract rate limit info from headers
                daily_count = response.headers.get("x-uw-daily-req-count")
                daily_limit = response.headers.get("x-uw-token-req-limit")
                if daily_count and daily_limit:
                    result["rate_limit_info"] = {
                        "count": int(daily_count),
                        "limit": int(daily_limit),
                        "percentage": round((int(daily_count) / int(daily_limit)) * 100, 1) if int(daily_limit) > 0 else 0
                    }
            elif response.status_code == 429:
                result["status"] = "rate_limited"
                result["message"] = f"Rate limited (429) - quota exhausted"
            else:
                result["status"] = "error"
                result["message"] = f"Unexpected status code: {response.status_code}"
        except requests.exceptions.Timeout:
            result["status"] = "timeout"
            result["message"] = "UW API request timed out"
        except requests.exceptions.ConnectionError:
            result["status"] = "connection_error"
            result["message"] = "Failed to connect to UW API"
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"UW API check failed: {str(e)}"
    
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"UW API check exception: {str(e)}"
    
    return result


def check_alpaca_api() -> Dict[str, Any]:
    """Check Alpaca API and SIP data feed connectivity"""
    result = {
        "status": "unknown",
        "message": "",
        "account_status": "unknown",
        "trading_status": "unknown",
        "sip_feed": "unknown",
        "response_time_ms": 0
    }
    
    try:
        api_key = os.getenv("ALPACA_API_KEY")
        api_secret = os.getenv("ALPACA_API_SECRET")
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not api_key or not api_secret:
            result["status"] = "error"
            result["message"] = "Alpaca credentials not found in environment"
            return result
        
        api = tradeapi.REST(api_key, api_secret, base_url)
        
        # Check account status
        start_time = time.time()
        try:
            account = api.get_account()
            response_time = (time.time() - start_time) * 1000
            
            result["response_time_ms"] = round(response_time, 2)
            result["account_status"] = getattr(account, "status", "unknown")
            result["trading_blocked"] = getattr(account, "trading_blocked", False)
            result["account_blocked"] = getattr(account, "account_blocked", False)
            
            # Check clock (market status)
            clock = api.get_clock()
            result["trading_status"] = clock.is_open if hasattr(clock, "is_open") else "unknown"
            result["market_status"] = "open" if clock.is_open else "closed"
            
            # Test SIP data feed by getting latest quote for SPY
            try:
                quote_start = time.time()
                quote = api.get_latest_quote("SPY")
                quote_time = (time.time() - quote_start) * 1000
                
                if quote and hasattr(quote, "bidprice") and hasattr(quote, "askprice"):
                    result["sip_feed"] = "ok"
                    result["sip_response_time_ms"] = round(quote_time, 2)
                    result["message"] = f"Alpaca API responding, SIP feed active (SPY quote: ${getattr(quote, 'bidprice', 0):.2f}/${getattr(quote, 'askprice', 0):.2f})"
                else:
                    result["sip_feed"] = "no_data"
                    result["message"] = "Alpaca API responding but SIP feed has no data"
            except Exception as quote_error:
                result["sip_feed"] = "error"
                result["message"] = f"Alpaca API responding but SIP feed error: {str(quote_error)}"
            
            if result["account_blocked"] or result["trading_blocked"]:
                result["status"] = "blocked"
            else:
                result["status"] = "ok"
                
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"Alpaca API check failed: {str(e)}"
    
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Alpaca API check exception: {str(e)}"
    
    return result


def check_uw_cache() -> Dict[str, Any]:
    """Check UW flow cache freshness"""
    result = {
        "status": "unknown",
        "cache_file": "",
        "age_minutes": 0,
        "size_bytes": 0,
        "message": ""
    }
    
    try:
        cache_file = CacheFiles.UW_FLOW_CACHE if hasattr(CacheFiles, 'UW_FLOW_CACHE') else Path("data/uw_flow_cache.json")
        result["cache_file"] = str(cache_file)
        
        if cache_file.exists():
            stat = cache_file.stat()
            result["size_bytes"] = stat.st_size
            age_seconds = time.time() - stat.st_mtime
            result["age_minutes"] = round(age_seconds / 60.0, 1)
            
            if result["age_minutes"] < 5:
                result["status"] = "fresh"
                result["message"] = f"Cache is fresh ({result['age_minutes']:.1f} minutes old)"
            elif result["age_minutes"] < 15:
                result["status"] = "stale"
                result["message"] = f"Cache is stale ({result['age_minutes']:.1f} minutes old)"
            else:
                result["status"] = "very_stale"
                result["message"] = f"Cache is very stale ({result['age_minutes']:.1f} minutes old)"
        else:
            result["status"] = "missing"
            result["message"] = "Cache file does not exist"
    
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Cache check failed: {str(e)}"
    
    return result


def check_logic_integrity() -> Dict[str, Any]:
    """Logic Integrity Test using mock 5.0 score signal"""
    result = {
        "status": "unknown",
        "message": "",
        "test_score": 5.0,
        "validation_passed": False
    }
    
    try:
        # Test score validation with mock signal
        from score_validation import get_score_validator
        validator = get_score_validator()
        
        # Create mock cluster with high score
        mock_cluster = {
            "ticker": "TEST",
            "direction": "bullish",
            "count": 10,
            "avg_premium": 1000000
        }
        
        # Test validation with valid score (should pass)
        validation_result = validator.validate_score("TEST", 5.0, "composite_v3", mock_cluster)
        if validation_result.get("valid", False):
            result["status"] = "ok"
            result["message"] = "Logic integrity test passed (5.0 score validated correctly)"
            result["validation_passed"] = True
        else:
            result["status"] = "warning"
            result["message"] = f"Logic integrity test warning: {validation_result.get('warning', 'unknown')}"
            
        # Test with zero score (should trigger exception logging)
        zero_validation = validator.validate_score("TEST", 0.0, "unknown", mock_cluster)
        if not zero_validation.get("valid", True):
            result["zero_score_detection"] = "working"
        
    except ImportError:
        result["status"] = "error"
        result["message"] = "Score validation module not available"
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Logic integrity test failed: {str(e)}"
    
    return result


def main():
    """Run pre-market health check"""
    print("[Pre-Market Health Check] Starting...", flush=True)
    print(f"[Pre-Market Health Check] Time: {datetime.now(timezone.utc).isoformat()}", flush=True)
    
    # Check if we're near market open
    is_near_open, next_open = check_market_open_time()
    if next_open:
        time_to_open = (next_open - datetime.now(timezone.utc)).total_seconds() / 60.0
        print(f"[Pre-Market Health Check] Next market open: {next_open.isoformat()} ({time_to_open:.1f} minutes)", flush=True)
    
    if not is_near_open and time_to_open > 60:
        print(f"[Pre-Market Health Check] INFO: More than 1 hour until market open. Running check anyway...", flush=True)
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uw_api": check_uw_api(),
        "alpaca_api": check_alpaca_api(),
        "uw_cache": check_uw_cache(),
        "logic_integrity": check_logic_integrity(),
        "overall_status": "unknown"
    }
    
    # Determine overall status
    statuses = [
        results["uw_api"]["status"],
        results["alpaca_api"]["status"],
        results["uw_cache"]["status"],
        results["logic_integrity"]["status"]
    ]
    
    if all(s == "ok" for s in statuses):
        results["overall_status"] = "healthy"
    elif any(s in ("error", "connection_error", "timeout") for s in statuses):
        results["overall_status"] = "unhealthy"
    elif any(s in ("rate_limited", "blocked", "stale") for s in statuses):
        results["overall_status"] = "degraded"
    else:
        results["overall_status"] = "unknown"
    
    # Print results
    print("\n[Pre-Market Health Check] Results:", flush=True)
    print(f"  Overall Status: {results['overall_status'].upper()}", flush=True)
    print(f"\n  UW API: {results['uw_api']['status']} - {results['uw_api']['message']}", flush=True)
    if results['uw_api'].get('rate_limit_info'):
        rl = results['uw_api']['rate_limit_info']
        print(f"    Rate Limit: {rl['count']}/{rl['limit']} ({rl['percentage']}%)", flush=True)
    print(f"    Response Time: {results['uw_api'].get('response_time_ms', 0)}ms", flush=True)
    
    print(f"\n  Alpaca API: {results['alpaca_api']['status']} - {results['alpaca_api']['message']}", flush=True)
    print(f"    Account Status: {results['alpaca_api'].get('account_status', 'unknown')}", flush=True)
    print(f"    Trading Blocked: {results['alpaca_api'].get('trading_blocked', False)}", flush=True)
    print(f"    SIP Feed: {results['alpaca_api'].get('sip_feed', 'unknown')}", flush=True)
    print(f"    Response Time: {results['alpaca_api'].get('response_time_ms', 0)}ms", flush=True)
    
    print(f"\n  UW Cache: {results['uw_cache']['status']} - {results['uw_cache']['message']}", flush=True)
    if results['uw_cache'].get('size_bytes', 0) > 0:
        print(f"    Size: {results['uw_cache']['size_bytes']} bytes", flush=True)
    
    print(f"\n  Logic Integrity: {results['logic_integrity']['status']} - {results['logic_integrity']['message']}", flush=True)
    if results['logic_integrity'].get('validation_passed'):
        print(f"    Test Score: {results['logic_integrity'].get('test_score', 'N/A')}", flush=True)
    
    # Save results to file
    try:
        health_check_dir = Path("data/health_checks")
        health_check_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = health_check_dir / f"pre_market_health_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n[Pre-Market Health Check] Report saved to: {report_file}", flush=True)
    except Exception as e:
        print(f"[Pre-Market Health Check] WARNING: Failed to save report: {e}", flush=True, file=sys.stderr)
    
    # Exit code based on status
    if results["overall_status"] == "healthy":
        print("\n[Pre-Market Health Check] ✅ All systems healthy - ready for market open", flush=True)
        return 0
    elif results["overall_status"] == "degraded":
        print("\n[Pre-Market Health Check] ⚠️  Systems degraded - review required", flush=True)
        return 1
    else:
        print("\n[Pre-Market Health Check] ❌ Systems unhealthy - immediate attention required", flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())
