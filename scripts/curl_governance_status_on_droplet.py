#!/usr/bin/env python3
"""Curl /api/governance/status on droplet with auth from .env. Run from repo root."""
import os
import sys
import json
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from droplet_client import DropletClient

def main():
    c = DropletClient()
    # Bash: source .env then curl with basic auth (no secrets in output)
    cmd = (
        "cd /root/stock-bot && "
        "export $(grep -E '^DASHBOARD_USER=|^DASHBOARD_PASS=' .env 2>/dev/null | xargs) 2>/dev/null; "
        "curl -s -u \"${DASHBOARD_USER}:${DASHBOARD_PASS}\" http://localhost:5000/api/governance/status 2>/dev/null || echo '{}'"
    )
    out, err, rc = c._execute(cmd, timeout=15)
    print(out or err or "{}")
    if out and out.strip().startswith("{"):
        j = json.loads(out)
        if "error" not in j:
            print("\n# Parsed: avg_profit_giveback=%s, stopping_condition_met=%s, decision=%s" % (
                j.get("avg_profit_giveback"), j.get("stopping_condition_met"), j.get("decision")), file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
