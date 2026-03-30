#!/usr/bin/env python3
"""Verify all dashboard tab endpoints return 200 with auth. Run on droplet: set -a && source .env && python3 scripts/dashboard_verify_all_tabs.py --json-out reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_<TS>.json"""
import argparse
import json
import os
import sys
import urllib.request
from base64 import b64encode

BASE = os.getenv("DASHBOARD_BASE_URL", "http://127.0.0.1:5000")
USER = os.getenv("DASHBOARD_USER", "").strip()
PW = os.getenv("DASHBOARD_PASS", "").strip()
AUTH = (b64encode(f"{USER}:{PW}".encode()).decode()) if (USER and PW) else None

# Alpaca dashboard: every tab-primary or strip endpoint (404 = hard failure on droplet).
TAB_ENDPOINTS = [
    "/api/dashboard/header_strip",
    "/api/alpaca_operational_activity?hours=72",
    "/api/version",
    "/api/versions",
    "/api/ping",
    "/api/direction_banner",
    "/api/situation",
    "/api/positions",
    "/api/stockbot/closed_trades",
    "/api/stockbot/fast_lane_ledger",
    "/api/sre/health",
    "/api/sre/self_heal_events?limit=5",
    "/api/executive_summary",
    "/api/failure_points",
    "/api/signal_history",
    "/api/learning_readiness",
    "/api/profitability_learning",
    "/api/dashboard/data_integrity",
    "/api/telemetry/latest/index",
    "/api/telemetry/latest/health",
    "/api/telemetry/latest/computed?name=live_vs_shadow_pnl",
    "/api/telemetry/latest/computed?name=bar_health_summary",
    "/api/paper-mode-intel-state",
    "/api/xai/auditor",
    "/api/xai/health",
]


def check_one(path: str) -> dict:
    url = BASE + path
    row = {
        "path": path,
        "url": url,
        "http_status": None,
        "ok_200": False,
        "error": None,
        "body_snippet": None,
    }
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Basic " + AUTH)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            code = r.getcode()
            row["http_status"] = code
            row["ok_200"] = code == 200
            body = r.read(8000)
            try:
                text = body.decode("utf-8", errors="replace")
            except Exception:
                text = str(body)[:500]
            row["body_snippet"] = text[:1200]
    except Exception as e:
        row["error"] = str(e)[:500]
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify dashboard tab APIs return HTTP 200 with Basic auth.")
    ap.add_argument(
        "--json-out",
        metavar="PATH",
        help="Write structured results (paths, status, errors, body snippets) to this file.",
    )
    args = ap.parse_args()

    if not AUTH:
        print("Set DASHBOARD_USER and DASHBOARD_PASS (or source .env)")
        return 1

    results = []
    ok = 0
    for path in TAB_ENDPOINTS:
        row = check_one(path)
        results.append(row)
        if row.get("ok_200"):
            ok += 1
            print(path, row.get("http_status"), "OK")
        elif row.get("http_status") is not None:
            print(path, row.get("http_status"), "")
        else:
            print(path, "FAIL", (row.get("error") or "")[:60])

    summary = {
        "base_url": BASE,
        "endpoints_total": len(TAB_ENDPOINTS),
        "ok_200": ok,
        "all_pass": ok == len(TAB_ENDPOINTS),
        "results": results,
    }

    print("---")
    print(ok, "/", len(TAB_ENDPOINTS), "returned 200")

    if args.json_out:
        out_path = args.json_out
        parent = os.path.dirname(out_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print("Wrote", out_path)

    return 0 if ok == len(TAB_ENDPOINTS) else 1


if __name__ == "__main__":
    sys.exit(main())
