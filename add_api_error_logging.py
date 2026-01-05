#!/usr/bin/env python3
"""
Add comprehensive API error logging to submit_order calls
This script will add error logging that captures RAW Alpaca API error responses
"""

import re

def add_error_logging_to_submit_order():
    """Add comprehensive error logging to all submit_order calls"""
    
    file_path = "main.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern 1: Submit order with backoff (limit orders)
    pattern1 = r'(o = backoff\(submit_order\)\(\)\n\s+order_id = getattr\(o, "id", None\))'
    
    replacement1 = '''o = backoff(submit_order)()
                    order_id = getattr(o, "id", None)
                    # CRITICAL: Log API response for debugging
                    if not order_id:
                        try:
                            error_details = {
                                "symbol": symbol,
                                "qty": qty,
                                "side": side,
                                "limit_price": limit_price,
                                "client_order_id": client_order_id,
                                "order_object": str(o) if o else None,
                                "order_type": type(o).__name__ if o else None,
                                "order_dict": o.__dict__ if hasattr(o, '__dict__') else None
                            }
                            log_event("critical_api_failure", "submit_order_no_id", **error_details)
                            # Also write to dedicated log file
                            import json
                            from pathlib import Path
                            log_file = Path("logs/critical_api_failure.log")
                            log_file.parent.mkdir(exist_ok=True)
                            with log_file.open("a") as lf:
                                lf.write(f"{datetime.now(timezone.utc).isoformat()} | submit_order_no_id | {json.dumps(error_details)}\\n")
                        except Exception as log_err:
                            pass  # Don't fail on logging error'''
    
    # Pattern 2: Direct submit_order calls (market orders)
    pattern2 = r'(o = self\.api\.submit_order\([^)]+\)\n\s+order_id = getattr\(o, "id", None\))'
    
    replacement2 = '''o = self.api.submit_order(...)
                    # CRITICAL: Capture API exceptions and log RAW response
                    try:
                        o = self.api.submit_order(...)
                    except Exception as api_err:
                        error_details = {
                            "symbol": symbol,
                            "qty": qty,
                            "side": side,
                            "error_type": type(api_err).__name__,
                            "error_message": str(api_err),
                            "error_args": api_err.args if hasattr(api_err, 'args') else None,
                            "error_dict": api_err.__dict__ if hasattr(api_err, '__dict__') else None
                        }
                        # Check if it's an HTTP error with response body
                        if hasattr(api_err, 'status_code'):
                            error_details["status_code"] = api_err.status_code
                        if hasattr(api_err, 'response'):
                            try:
                                error_details["response_body"] = api_err.response.text if hasattr(api_err.response, 'text') else str(api_err.response)
                                error_details["response_json"] = api_err.response.json() if hasattr(api_err.response, 'json') else None
                            except:
                                pass
                        log_event("critical_api_failure", "submit_order_exception", **error_details)
                        # Write to dedicated log file
                        import json
                        from pathlib import Path
                        from datetime import datetime, timezone
                        log_file = Path("logs/critical_api_failure.log")
                        log_file.parent.mkdir(exist_ok=True)
                        with log_file.open("a") as lf:
                            lf.write(f"{datetime.now(timezone.utc).isoformat()} | submit_order_exception | {json.dumps(error_details)}\\n")
                        raise  # Re-raise the exception
                    order_id = getattr(o, "id", None)'''
    
    # Actually, let me create a more targeted fix by reading the actual code structure
    print("This script needs to be run manually after reading the actual code structure")
    print("The fix needs to be applied directly to the submit_entry method")

if __name__ == "__main__":
    add_error_logging_to_submit_order()
