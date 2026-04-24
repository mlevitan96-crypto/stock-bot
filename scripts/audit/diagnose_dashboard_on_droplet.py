#!/usr/bin/env python3
"""One-off: print droplet dashboard audit report and port/process info."""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from droplet_client import DropletClient
proj = "/root/stock-bot"
with DropletClient() as c:
    out, _, _ = c._execute(f"cat {proj}/reports/audit/DASHBOARD_VISIBILITY_AUDIT.md 2>/dev/null | head -40")
    print("--- DASHBOARD_VISIBILITY_AUDIT ---")
    print(out or "(empty)")
    out2, _, _ = c._execute("ss -tlnp 2>/dev/null | grep 5000 || true")
    print("--- Port 5000 ---")
    print(out2 or "(none)")
    out3, _, _ = c._execute("ps aux | grep dashboard | grep -v grep || true")
    print("--- Dashboard processes ---")
    print(out3 or "(none)")
