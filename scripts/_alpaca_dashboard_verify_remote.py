#!/usr/bin/env python3
"""Run on droplet: verify dashboard APIs and HTML snippets (reads /root/stock-bot/.env)."""
from __future__ import annotations

import base64
import json
import sys
import urllib.request
from pathlib import Path

ENV_PATH = Path("/root/stock-bot/.env")


def _headers() -> dict[str, str]:
    u = p = None
    for raw in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("DASHBOARD_USER="):
            u = line.split("=", 1)[1].strip().strip('"').strip("'")
        elif line.startswith("DASHBOARD_PASS="):
            p = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not u or not p:
        print("VERIFY_ERR missing DASHBOARD_USER/PASS", file=sys.stderr)
        sys.exit(2)
    tok = base64.b64encode(f"{u}:{p}".encode()).decode()
    return {"Authorization": f"Basic {tok}"}


def _get(path: str) -> tuple[int, bytes]:
    req = urllib.request.Request(f"http://127.0.0.1:5000{path}", headers=_headers())
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read()


def main() -> int:
    st, body = _get("/api/dashboard/data_integrity")
    print("DI_HTTP", st)
    if st != 200:
        print("DI_BODY_HEAD", body[:300])
        return 1
    d = json.loads(body.decode())
    print("DI_generated_at_utc", d.get("generated_at_utc"))
    print("DI_has_data_sources", "data_sources" in d)
    a = d.get("alpaca_strict") or {}
    print("DI_LEARNING_STATUS", a.get("LEARNING_STATUS"))
    print("DI_learning_fail_closed_reason", a.get("learning_fail_closed_reason"))

    st2, body2 = _get("/api/stockbot/closed_trades")
    print("CT_HTTP", st2)
    if st2 != 200:
        print("CT_BODY_HEAD", body2[:300])
        return 1
    ct = json.loads(body2.decode())
    rows = ct.get("closed_trades") or []
    t0 = rows[0] if rows else {}
    print("CT_row_count", len(rows))
    print("CT_has_strict_alpaca_chain", "strict_alpaca_chain" in t0)
    print("CT_has_entry_reason_display", "entry_reason_display" in t0)
    print("CT_has_fees_display", "fees_display" in t0)
    print("CT_has_alpaca_strict_summary", "alpaca_strict_summary" in ct)
    summ = ct.get("alpaca_strict_summary")
    if isinstance(summ, dict):
        print("CT_summary_LEARNING_STATUS", summ.get("LEARNING_STATUS"))

    st3, body3 = _get("/")
    print("ROOT_HTTP", st3)
    html = body3.decode("utf-8", errors="replace")
    print("UI_system_health_tab", 'data-tab="system_health"' in html)
    print("UI_no_xai_data_tab", 'data-tab="xai"' not in html)
    print("UI_no_natural_language_auditor_button", "Natural Language Auditor" not in html[:200000])
    print("UI_no_telemetry_health_tab_id", "telemetry_health-tab" not in html)
    print("UI_loadSystemHealth_wired", "loadSystemHealth" in html and "/api/dashboard/data_integrity" in html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
