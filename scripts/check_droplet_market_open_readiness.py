#!/usr/bin/env python3
"""Check droplet: service, TRADING_MODE, CSA state, dashboard, processes. No secrets printed."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from droplet_client import DropletClient


def main() -> int:
    c = DropletClient()
    out = []

    status = c.get_status()
    out.append("=== SERVICE ===")
    out.append("stock-bot service: " + str(status.get("service_status", "?")))
    out.append("process_count: " + str(status.get("process_count", "?")))
    out.append("branch: " + str(status.get("git", {}).get("branch", "?")))
    out.append("disk: " + str(status.get("disk_usage", "?")))
    out.append("memory: " + str(status.get("memory_usage", "?")))
    out.append("uptime: " + str(status.get("uptime", "?")))

    std, _, _ = c._execute_with_cd(
        "grep -E '^TRADING_MODE=' .env 2>/dev/null | sed 's/=.*/=***/'; "
        "grep -E '^ALPACA_BASE_URL=' .env 2>/dev/null | sed 's/=.*/=***/'; true"
    )
    out.append("")
    out.append("=== MODE (masked) ===")
    out.append(std.strip() if std else "(.env not readable)")

    std, _, _ = c._execute_with_cd("cat reports/state/TRADE_CSA_STATE.json 2>/dev/null")
    out.append("")
    out.append("=== CSA FIRST 100 ===")
    if std and "total_trade_events" in std:
        try:
            j = json.loads(std)
            out.append("total_trade_events: " + str(j.get("total_trade_events")))
            out.append("trades_until_next: 100 (first batch)")
        except Exception:
            out.append(std[:200])
    else:
        out.append(std[:200] if std else "MISSING")

    out.append("")
    out.append("=== DASHBOARD ===")
    for name, path in [("api/ping", "/api/ping"), ("profitability_learning", "/api/profitability_learning"), ("health", "/health")]:
        std, _, _ = c._execute("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000" + path + " 2>/dev/null || echo FAIL")
        out.append(name + ": HTTP " + (std.strip() if std else "FAIL"))

    std, _, _ = c._execute("curl -s http://127.0.0.1:5000/api/sre/health 2>/dev/null | head -c 400")
    out.append("")
    out.append("=== SRE HEALTH (snippet) ===")
    out.append(std[:400] if std else "N/A")

    std, _, _ = c._execute("ps aux | grep -E 'deploy_supervisor|main.py|dashboard.py' | grep -v grep | head -5")
    out.append("")
    out.append("=== PROCESSES ===")
    out.append(std[:500] if std else "none")

    print("\n".join(out))
    c.close()

    # Verdict
    ok = (
        status.get("service_status") == "active"
        and (status.get("process_count") or 0) >= 2
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
