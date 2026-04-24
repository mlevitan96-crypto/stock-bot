#!/usr/bin/env python3
"""
Probe Alpaca dashboard Flask routes (local repo). Requires DASHBOARD_USER / DASHBOARD_PASS in env.

Usage (PowerShell):
  $env:DASHBOARD_USER='x'; $env:DASHBOARD_PASS='y'
  python scripts/alpaca_dashboard_truth_probe.py
  python scripts/alpaca_dashboard_truth_probe.py --json reports/ALPACA_DASHBOARD_DATA_SANITY_<TS>.json
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Same paths as dashboard_verify_all_tabs (expanded)
PATHS = [
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
    "/api/paper-mode-intel-state",
    "/api/xai/auditor",
    "/api/xai/health",
]


def _auth_header() -> str:
    u = os.getenv("DASHBOARD_USER", "").strip()
    p = os.getenv("DASHBOARD_PASS", "").strip()
    if not u or not p:
        return ""
    tok = base64.b64encode(f"{u}:{p}".encode()).decode()
    return f"Basic {tok}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="Write full probe results to this path")
    args = ap.parse_args()

    if not _auth_header():
        print("Set DASHBOARD_USER and DASHBOARD_PASS", file=sys.stderr)
        return 1

    sys.path.insert(0, str(REPO))
    os.chdir(REPO)
    import dashboard  # noqa: E402

    client = dashboard.app.test_client()
    auth = _auth_header()
    results = []
    ts = datetime.now(timezone.utc).isoformat()

    for path in PATHS:
        entry: dict = {"path": path, "status": None, "error": None, "summary": {}}
        try:
            r = client.get(path, headers={"Authorization": auth})
            entry["status"] = r.status_code
            ct = (r.headers.get("Content-Type") or "").lower()
            if "json" in ct and r.data:
                try:
                    body = r.get_json()
                    entry["summary"] = _summarize_json(path, body)
                except Exception as e:
                    entry["error"] = f"json_parse:{e}"
            elif r.status_code != 200:
                entry["summary"] = {"body_prefix": r.data[:200].decode("utf-8", errors="replace")}
        except Exception as e:
            entry["error"] = str(e)
        results.append(entry)

    out = {
        "generated_at_utc": ts,
        "repo_root": str(REPO),
        "endpoints": results,
    }
    if args.json:
        outp = REPO / args.json
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print("Wrote", outp)

    ok = sum(1 for e in results if e.get("status") == 200)
    print(f"OK {ok}/{len(results)} endpoints HTTP 200")
    for e in results:
        st = e.get("status")
        mark = "OK" if st == 200 else "FAIL"
        print(f"  [{mark}] {e['path']} -> {st} {e.get('summary') or e.get('error') or ''}")
    return 0 if ok == len(results) else 1


def _summarize_json(path: str, body: object) -> dict:
    if not isinstance(body, dict):
        return {"type": type(body).__name__}
    s: dict = {}
    if "generated_at_utc" in body:
        s["generated_at_utc"] = body.get("generated_at_utc")
    if "as_of_ts" in body:
        s["as_of_ts"] = body.get("as_of_ts")
    if "latest_date" in body:
        s["latest_date"] = body.get("latest_date")
    if "positions" in body and isinstance(body["positions"], list):
        s["positions_count"] = len(body["positions"])
    if "closed_trades" in body and isinstance(body["closed_trades"], list):
        s["closed_trades_count"] = len(body["closed_trades"])
    if "signals" in body and isinstance(body["signals"], list):
        s["signals_count"] = len(body["signals"])
    if "cycles" in body and isinstance(body["cycles"], list):
        s["cycles_count"] = len(body["cycles"])
    if "message" in body and body.get("message"):
        s["message"] = str(body["message"])[:120]
    if body.get("error") is not None and body.get("error") != "":
        s["error"] = str(body.get("error"))[:200]
    if path.endswith("/data_integrity") or "data_integrity" in path:
        if "alpaca_strict" in body:
            a = body.get("alpaca_strict")
            if isinstance(a, dict):
                s["LEARNING_STATUS"] = a.get("LEARNING_STATUS")
                s["trades_complete"] = a.get("trades_complete")
    return s


if __name__ == "__main__":
    raise SystemExit(main())
