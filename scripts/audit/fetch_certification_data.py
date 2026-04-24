#!/usr/bin/env python3
"""Fetch readiness and one redacted exit line from droplet for certification."""
import json
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from droplet_client import DropletClient
proj = "/root/stock-bot"
with DropletClient() as c:
    out, _, _ = c._execute(f"cat {proj}/state/direction_readiness.json 2>/dev/null")
    print("--- direction_readiness.json ---")
    print(out or "{}")
    out2, _, _ = c._execute(f"tail -5 {proj}/logs/exit_attribution.jsonl 2>/dev/null | head -1")
    if out2:
        d = json.loads(out2)
        redact = dict(d)
        for k in ("symbol", "entry_ts", "exit_ts", "trade_id"):
            if k in redact:
                redact[k] = "..."
        if "direction_intel_embed" in d and d["direction_intel_embed"]:
            redact["direction_intel_embed"] = {"intel_snapshot_entry": "(non-empty)", "intel_snapshot_exit": "(non-empty)"}
        print("--- redacted exit sample ---")
        print(json.dumps(redact, indent=2)[:1500])
