#!/usr/bin/env python3
"""Verify /api/rolling_pnl_5d and dashboard health on droplet."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from droplet_client import DropletClient

c = DropletClient()
r = c.execute_command("curl -s http://127.0.0.1:5000/api/rolling_pnl_5d 2>/dev/null | head -c 600")
print("API /api/rolling_pnl_5d:", (r.get("stdout") or r.get("stderr") or "?")[:600])
r2 = c.execute_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/api/telemetry_health 2>/dev/null")
print("Dashboard health:", r2.get("stdout"), "(200=OK)")
