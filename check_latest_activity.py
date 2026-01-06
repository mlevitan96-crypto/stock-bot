#!/usr/bin/env python3
"""Check latest activity and verify fixes are working"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# Check most recent run cycles
run_path = Path("logs/run.jsonl")
if run_path.exists():
    with open(run_path) as f:
        lines = f.readlines()
        if lines:
            latest = json.loads(lines[-1])
            ts = latest.get("ts", "")
            clusters = latest.get("clusters", 0)
            orders = latest.get("orders", 0)
            print(f"Latest run cycle: {ts}")
            print(f"  Clusters: {clusters}, Orders: {orders}")
            print()

# Check most recent attribution
attr_path = Path("data/uw_attribution.jsonl")
if attr_path.exists():
    with open(attr_path) as f:
        lines = f.readlines()
        if lines:
            latest = json.loads(lines[-1])
            ts = latest.get("ts", 0)
            symbol = latest.get("symbol", "UNKNOWN")
            score = latest.get("score", 0.0)
            decision = latest.get("decision", "unknown")
            threshold = latest.get("threshold", 0.0)
            
            # Convert timestamp
            from datetime import datetime
            dt = datetime.fromtimestamp(ts)
            
            print(f"Latest attribution: {dt}")
            print(f"  Symbol: {symbol}, Score: {score:.3f}, Threshold: {threshold:.2f}, Decision: {decision}")
            print()

# Check most recent gate events
gate_path = Path("logs/composite_gate.jsonl")
if gate_path.exists():
    with open(gate_path) as f:
        lines = f.readlines()
        if lines:
            latest = json.loads(lines[-1])
            ts = latest.get("ts", "")
            symbol = latest.get("symbol", "UNKNOWN")
            score = latest.get("score", 0.0)
            threshold = latest.get("threshold", 0.0)
            print(f"Latest gate event: {ts}")
            print(f"  Symbol: {symbol}, Score: {score:.3f}, Threshold: {threshold:.2f}")
            print()

# Verify runtime values
print("Runtime verification:")
import uw_composite_v2
print(f"  ENTRY_THRESHOLDS: {uw_composite_v2.ENTRY_THRESHOLDS}")
print(f"  get_threshold('AAPL', 'base'): {uw_composite_v2.get_threshold('AAPL', 'base')}")
print(f"  get_weight('options_flow', 'mixed'): {uw_composite_v2.get_weight('options_flow', 'mixed')}")
