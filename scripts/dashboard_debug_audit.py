#!/usr/bin/env python3
"""
Dashboard full debug audit: page load, version, positions, auth.
Run locally with DASHBOARD_USER/DASHBOARD_PASS set, or on droplet.
Usage: python scripts/dashboard_debug_audit.py [BASE_URL]
Default BASE_URL: http://127.0.0.1:5000
"""

from __future__ import annotations

import os
import sys
import urllib.request
import urllib.error
from base64 import b64encode

def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000").rstrip("/")
    user = os.getenv("DASHBOARD_USER", "").strip()
    pw = os.getenv("DASHBOARD_PASS", "").strip()
    auth = (b64encode(f"{user}:{pw}".encode()).decode()) if (user and pw) else None

    def get(path: str, use_auth: bool) -> tuple[int, str, str]:
        url = base + path
        req = urllib.request.Request(url)
        if use_auth and auth:
            req.add_header("Authorization", "Basic " + auth)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read().decode("utf-8", errors="replace")
                return r.status, r.headers.get("Content-Type", ""), body[:500]
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type", ""), e.read().decode("utf-8", errors="replace")[:300]
        except Exception as e:
            return -1, "", str(e)

    print("Dashboard debug audit")
    print("Base URL:", base)
    print("Auth configured:", bool(auth))
    print()

    # 1) GET / without auth -> expect 401
    code, ct, body = get("/", False)
    print("GET / (no auth):", code, ct[:50] if ct else "")
    if code == 401:
        print("  OK – 401 as expected")
    else:
        print("  Unexpected (expected 401). Body sample:", body[:150])
    print()

    # 2) GET / with auth -> expect 200, HTML
    code, ct, body = get("/", True)
    print("GET / (with auth):", code, ct[:50] if ct else "")
    if code == 200:
        has_script = "loadVersionBadge" in body and "version-badge" in body
        print("  OK – 200, HTML. Script/version-badge present:", has_script)
    else:
        print("  Failed. Body sample:", body[:200])
    print()

    # 3) GET /api/ping with auth -> expect 200, JSON
    code, ct, body = get("/api/ping", True)
    print("GET /api/ping (with auth):", code, ct[:50] if ct else "")
    if code == 200 and "ok" in body:
        print("  OK – 200, JSON with ok")
    else:
        print("  Unexpected. Body:", body[:200])
    print()

    # 4) GET /api/version with auth -> expect 200, JSON
    code, ct, body = get("/api/version", True)
    print("GET /api/version (with auth):", code, ct[:50] if ct else "")
    if code == 200 and "git_commit" in body:
        print("  OK – 200, version JSON")
    else:
        print("  Unexpected. Body:", body[:200])
    print()

    # 5) GET /api/version without auth -> expect 401
    code, ct, body = get("/api/version", False)
    print("GET /api/version (no auth):", code)
    if code == 401:
        print("  OK – 401 as expected")
    else:
        print("  Unexpected (expected 401)")
    print()

    # 6) GET /api/positions with auth -> expect 200, JSON
    code, ct, body = get("/api/positions", True)
    print("GET /api/positions (with auth):", code, ct[:50] if ct else "")
    if code == 200:
        has_positions = "positions" in body
        print("  OK – 200, JSON. Has 'positions':", has_positions)
    else:
        print("  Failed. Body sample:", body[:200])

    print()
    print("If all (with auth) return 200 but the browser still shows nothing:")
    print("  - Hard refresh (Ctrl+F5) and log in again when prompted.")
    print("  - Open DevTools (F12) -> Network: check if /api/version and /api/positions return 200.")
    print("  - Console: look for JS errors or CORS messages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
