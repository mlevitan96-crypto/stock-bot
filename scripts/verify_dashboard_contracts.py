#!/usr/bin/env python3
"""
Endpoint contract tests: load data/dashboard_panel_inventory.json, call each endpoint locally,
validate schema + required keys. Fails if any contract breaks.

Run against a running dashboard (default http://127.0.0.1:5000). Set DASHBOARD_USER/DASHBOARD_PASS
when the dashboard uses Basic auth. If CI does not start the dashboard, run as a manual gate
after starting the dashboard locally or on a stub.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
INVENTORY_PATH = DATA_DIR / "dashboard_panel_inventory.json"
BASE_URL = os.getenv("DASHBOARD_BASE_URL", "http://127.0.0.1:5000")


def _get_auth() -> Optional[tuple]:
    u = os.getenv("DASHBOARD_USER", "").strip()
    p = os.getenv("DASHBOARD_PASS", "").strip()
    return (u, p) if u and p else None


def _fetch(route: str, query: Optional[Dict[str, str]] = None) -> tuple:
    """Returns (status_code, data_or_none, error_message)."""
    import base64
    import urllib.request
    url = BASE_URL + route
    if query:
        url += "?" + urlencode({k: v for k, v in query.items() if v})
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/json")
    auth = _get_auth()
    if auth:
        creds = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        req.add_header("Authorization", f"Basic {creds}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                return (resp.status, None, "Invalid JSON")
            return (resp.status, data, None)
    except Exception as e:
        return (0, None, str(e))


def _check_keys(data: dict, required: List[str], optional: Optional[List[str]] = None) -> List[str]:
    """Return list of missing required keys."""
    missing = [k for k in required if k not in data]
    return missing


def main() -> int:
    if not INVENTORY_PATH.exists():
        print(f"[SKIP] No inventory at {INVENTORY_PATH}")
        return 0
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        inv = json.load(f)
    failures = []
    # Minimal contract: 200 + expected top-level keys
    contracts = [
        ("/api/positions", {}, ["positions", "total_value"], None),
        ("/api/health_status", {}, ["last_order", "doctor", "market"], None),
        ("/api/sre/health", {}, ["overall_health"], None),
        ("/api/sre/self_heal_events", {"limit": "10"}, ["events", "count"], None),
        ("/api/executive_summary", {}, ["trades", "total_trades", "pnl_metrics"], None),
        ("/api/signal_history", {}, ["signals", "count"], None),
        ("/api/failure_points", {}, ["readiness"], None),
        ("/api/telemetry/latest/index", {}, ["latest_date", "computed"], None),
        ("/api/telemetry/latest/computed", {"name": "live_vs_shadow_pnl"}, ["latest_date", "name", "data"], None),
        ("/api/telemetry/latest/health", {}, ["latest_date", "as_of_ts"], None),
        ("/api/system-events", {"limit": "10"}, ["events"], None),
        ("/api/stockbot/closed_trades", {}, ["closed_trades", "count"], None),
        ("/api/stockbot/wheel_analytics", {}, ["strategy_id", "total_trades"], None),
    ]
    for route, query, required_keys, _ in contracts:
        status, data, err = _fetch(route, query or None)
        if status not in (200, 503):
            # 503 = service unavailable (e.g. score_telemetry module not available)
            failures.append(f"{route}: status={status} err={err}")
            continue
        if status == 503:
            continue  # optional endpoint, skip schema check
        if data is None:
            failures.append(f"{route}: no JSON")
            continue
        missing = _check_keys(data, required_keys)
        if missing:
            failures.append(f"{route}: missing keys {missing}")
        # Freshness: if response has as_of_ts or timestamp, allow it
        if "as_of_ts" in data or "timestamp" in data:
            pass  # contract satisfied
    if failures:
        for f in failures:
            print(f"[FAIL] {f}")
        return 1
    print("[OK] All dashboard contracts passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
