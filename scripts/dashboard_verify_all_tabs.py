#!/usr/bin/env python3
"""Verify all dashboard tab endpoints return 200 with auth. Run on droplet: set -a && source .env && python3 scripts/dashboard_verify_all_tabs.py"""
import os
import sys
import urllib.request
from base64 import b64encode

BASE = os.getenv("DASHBOARD_BASE_URL", "http://127.0.0.1:5000")
USER = os.getenv("DASHBOARD_USER", "").strip()
PW = os.getenv("DASHBOARD_PASS", "").strip()
AUTH = (b64encode(f"{USER}:{PW}".encode()).decode()) if (USER and PW) else None

TAB_ENDPOINTS = [
    "/api/version",
    "/api/positions",
    "/api/sre/health",
    "/api/executive_summary",
    "/api/xai/auditor",
    "/api/failure_points",
    "/api/signal_history",
    "/api/telemetry/latest/index",
]


def main():
    if not AUTH:
        print("Set DASHBOARD_USER and DASHBOARD_PASS (or source .env)")
        return 1
    ok = 0
    for path in TAB_ENDPOINTS:
        req = urllib.request.Request(BASE + path)
        req.add_header("Authorization", "Basic " + AUTH)
        try:
            r = urllib.request.urlopen(req, timeout=15)
            status = r.status
            ok += 1 if status == 200 else 0
            print(path, status, "OK" if status == 200 else "")
        except Exception as e:
            print(path, "FAIL", str(e)[:60])
    print("---")
    print(ok, "/", len(TAB_ENDPOINTS), "returned 200")
    return 0 if ok == len(TAB_ENDPOINTS) else 1


if __name__ == "__main__":
    sys.exit(main())
