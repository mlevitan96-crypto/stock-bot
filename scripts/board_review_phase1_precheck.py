#!/usr/bin/env python3
"""Phase 1: Droplet precheck — deployed_commit, exit_attribution, dashboard, governance."""
from __future__ import annotations
import os
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
os.environ["DROPLET_RUN"] = "1"

def main():
    from droplet_client import DropletClient
    proj = "/root/stock-bot"
    c = DropletClient()
    print("=== PHASE 1 — DROPLET PRECHECK ===")
    out1, _, _ = c._execute(f"cd {proj} && git rev-parse HEAD 2>/dev/null || echo none")
    commit = (out1 or "").strip()
    if commit and commit != "none":
        print("deployed_commit:", commit[:12])
    else:
        print("deployed_commit: NOT_FOUND")
    out2, _, _ = c._execute(f"wc -l {proj}/logs/exit_attribution.jsonl 2>/dev/null || echo 0")
    parts = (out2 or "0").strip().split()
    print("exit_attribution.jsonl lines:", parts[0] if parts else "0")
    out3, _, _ = c._execute("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/health 2>/dev/null || echo 000")
    print("dashboard health:", (out3 or "000").strip())
    out4, _, _ = c._execute(f"cat {proj}/state/direction_readiness.json 2>/dev/null | head -5")
    print("governance (direction_readiness) present:", "telemetry_trades" in (out4 or ""))
    print("Precheck done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
