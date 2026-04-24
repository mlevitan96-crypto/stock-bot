#!/usr/bin/env python3
"""Collect trade-data inventory from droplet: log paths, line counts, and sample record keys. Output JSON to stdout."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

# Logs that contain trade/exit/attribution data (MEMORY_BANK + pipeline)
TRADE_LOGS = [
    "logs/exit_attribution.jsonl",
    "logs/alpaca_entry_attribution.jsonl",
    "logs/alpaca_exit_attribution.jsonl",
    "logs/attribution.jsonl",
    "logs/master_trade_log.jsonl",
    "logs/signal_context.jsonl",
    "logs/exits.jsonl",
]


def main() -> int:
    from droplet_client import DropletClient
    proj = "/root/stock-bot"
    client = DropletClient()
    out = {"project_dir": client.project_dir, "logs": {}}
    for rel in TRADE_LOGS:
        path = f"{client.project_dir}/{rel}"
        # Line count
        lc = client.execute_command(f"wc -l {path} 2>/dev/null || echo '0'", timeout=10)
        line_count = 0
        if lc.get("stdout"):
            parts = lc["stdout"].strip().split()
            if parts:
                try:
                    line_count = int(parts[0])
                except ValueError:
                    pass
        # Last line (sample) - keys only to keep small
        tail = client.execute_command(f"tail -1 {path} 2>/dev/null", timeout=10)
        sample_keys = []
        if tail.get("stdout") and tail["stdout"].strip():
            try:
                obj = json.loads(tail["stdout"].strip())
                sample_keys = list(obj.keys()) if isinstance(obj, dict) else []
            except json.JSONDecodeError:
                sample_keys = ["<not json>"]
        out["logs"][rel] = {"line_count": line_count, "sample_record_keys": sample_keys}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
