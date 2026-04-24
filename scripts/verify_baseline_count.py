#!/usr/bin/env python3
"""Verify 0-trade baseline by counting exits >= counting_started_utc."""
import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE = REPO / "state" / "alpaca_trade_notifications.json"
EXIT_ATTRIBUTION = REPO / "logs" / "exit_attribution.jsonl"

if not STATE.exists():
    print("Error: state file not found", file=sys.stderr)
    sys.exit(1)

with open(STATE, "r") as f:
    state = json.load(f)

counting_started_utc = state.get("counting_started_utc")
if not counting_started_utc:
    print("Error: counting_started_utc not found", file=sys.stderr)
    sys.exit(1)

try:
    watermark_dt = datetime.fromisoformat(counting_started_utc.replace("Z", "+00:00"))
except Exception as e:
    print(f"Error parsing watermark: {e}", file=sys.stderr)
    sys.exit(1)

count = 0
seen_keys = set()

if EXIT_ATTRIBUTION.exists():
    with open(EXIT_ATTRIBUTION, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            exit_ts = rec.get("exit_ts") or rec.get("timestamp")
            if not exit_ts:
                continue
            try:
                exit_dt = datetime.fromisoformat(str(exit_ts).replace("Z", "+00:00"))
            except Exception:
                continue
            
            if exit_dt < watermark_dt:
                continue
            
            # Deduplicate by canonical key
            et = rec.get("entry_ts") or rec.get("entry_timestamp")
            if et:
                key = f"live:{rec.get('symbol', '').upper()}:{datetime.fromisoformat(str(et).replace('Z', '+00:00')).strftime('%Y-%m-%dT%H:%M:%S')}"
                if key and key not in seen_keys:
                    seen_keys.add(key)
                    count += 1

print(f"Watermark: {counting_started_utc}")
print(f"Exits >= watermark: {count}")
print(f"Unique trades: {len(seen_keys)}")
sys.exit(0 if count == 0 else 1)
