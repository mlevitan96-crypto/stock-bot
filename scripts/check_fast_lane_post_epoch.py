#!/usr/bin/env python3
"""One-off: count post-epoch exits in exit_attribution.jsonl. Run on droplet."""
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
log_path = REPO / "logs" / "exit_attribution.jsonl"
config_path = REPO / "state" / "fast_lane_experiment" / "config.json"
epoch = os.environ.get("FAST_LANE_EPOCH") or "2026-03-17T13:30:00Z"
if not os.environ.get("FAST_LANE_EPOCH") and config_path.exists():
    try:
        with open(config_path) as f:
            cfg = json.load(f)
            epoch = (cfg.get("epoch_start_iso") or epoch).strip()
    except Exception:
        pass

count_post = 0
total = 0
with open(log_path) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        total += 1
        try:
            d = json.loads(line)
            ts = d.get("timestamp") or d.get("exit_timestamp") or d.get("ts") or ""
            if ts >= epoch:
                count_post += 1
        except Exception:
            pass
print("total_exits", total)
print("post_epoch_count", count_post)
print("epoch", epoch)
sys.exit(0)
