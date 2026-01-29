#!/usr/bin/env python3
"""
Verify telemetry endpoints resolve correctly (absolute paths, no 404 for index/health when empty).
Run before push to ensure dashboard Telemetry tab and SRE bar health don't break.

Usage:
  python scripts/verify_telemetry_endpoints.py

Uses the Flask app from dashboard.py; does not require a running server.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    # Avoid loading dashboard auth/registry that may fail outside full env
    import os
    os.environ.setdefault("DASHBOARD_USER", "test")
    os.environ.setdefault("DASHBOARD_PASS", "test")

    failures = []

    # 1) Telemetry root is absolute
    try:
        from dashboard import TELEMETRY_ROOT, _DASHBOARD_ROOT
        if not TELEMETRY_ROOT.is_absolute():
            failures.append("TELEMETRY_ROOT should be absolute")
        if TELEMETRY_ROOT != _DASHBOARD_ROOT / "telemetry":
            failures.append("TELEMETRY_ROOT should be _DASHBOARD_ROOT / 'telemetry'")
    except Exception as e:
        failures.append(f"Import dashboard: {e}")

    # 2) _latest_telemetry_dir returns path or None; never crashes
    try:
        from dashboard import _latest_telemetry_dir
        tdir = _latest_telemetry_dir()
        if tdir is not None and not tdir.is_absolute():
            failures.append("_latest_telemetry_dir() should return absolute path or None")
    except Exception as e:
        failures.append(f"_latest_telemetry_dir: {e}")

    # Basic auth for test client (dashboard requires auth)
    import base64
    auth_header = {"Authorization": "Basic " + base64.b64encode(b"test:test").decode()}

    # 3) Index returns 200 (with or without bundle)
    try:
        from dashboard import app
        with app.test_client() as c:
            r = c.get("/api/telemetry/latest/index", headers=auth_header)
            if r.status_code != 200:
                failures.append(f"GET /api/telemetry/latest/index returned {r.status_code}")
            else:
                data = r.get_json() or {}
                if "latest_date" not in data and "message" not in data:
                    failures.append("Index response should have latest_date or message")
                if data.get("latest_date") is None and "telemetry_root" not in data:
                    failures.append("When no bundle, index should include telemetry_root")
    except Exception as e:
        failures.append(f"Index endpoint: {e}")

    # 4) Health returns 200 (with or without bundle)
    try:
        from dashboard import app
        with app.test_client() as c:
            r = c.get("/api/telemetry/latest/health", headers=auth_header)
            if r.status_code != 200:
                failures.append(f"GET /api/telemetry/latest/health returned {r.status_code}")
            else:
                data = r.get_json() or {}
                if "computed_index" not in data and "message" not in data:
                    failures.append("Health response should have computed_index or message")
    except Exception as e:
        failures.append(f"Health endpoint: {e}")

    # 5) Paper-mode intel state uses TELEMETRY_ROOT
    try:
        from dashboard import app
        with app.test_client() as c:
            r = c.get("/api/paper-mode-intel-state", headers=auth_header)
            if r.status_code != 200:
                failures.append(f"GET /api/paper-mode-intel-state returned {r.status_code}")
    except Exception as e:
        failures.append(f"Paper-mode endpoint: {e}")

    if failures:
        for f in failures:
            print(f"[FAIL] {f}")
        return 1
    print("[OK] Telemetry endpoints: TELEMETRY_ROOT absolute, index/health return 200, paper-mode OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
