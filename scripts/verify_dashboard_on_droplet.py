#!/usr/bin/env python3
"""Verify dashboard on droplet: GET / returns 200 and HTML has no raw placeholders."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from droplet_client import DropletClient

def main():
    c = DropletClient()
    # Curl dashboard (no auth - we exempt GET /)
    out, err, code = c._execute(
        "curl -s -w '\\nHTTP_CODE:%{http_code}' http://127.0.0.1:5000/ 2>/dev/null"
    )
    if "HTTP_CODE:" in out:
        parts = out.rsplit("HTTP_CODE:", 1)
        body = parts[0].strip()
        status = parts[1].strip().split("\n")[0]
    else:
        body = out
        status = "?"
    has_placeholder = "__BANNER_HTML__" in body or "__SITUATION_HTML__" in body or "__BANNER_SEV__" in body
    has_content = ("direction-banner" in body or "Trading Bot" in body or "dashboard" in body.lower())
    # Also check key APIs (no auth required for these)
    o2, _, _ = c._execute("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/direction_banner 2>/dev/null")
    o3, _, _ = c._execute("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/situation 2>/dev/null")
    api_ok = o2.strip() == "200" and o3.strip() == "200"
    print("API direction_banner:", o2.strip())
    print("API situation:", o3.strip())
    ok = status == "200" and not has_placeholder and has_content and api_ok
    print("HTTP status:", status)
    print("Placeholders in HTML:", has_placeholder)
    print("Has content:", has_content)
    print("LIVE VERIFICATION:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
