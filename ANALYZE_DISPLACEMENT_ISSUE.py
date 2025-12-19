#!/usr/bin/env python3
"""
Deep analysis of why displacement isn't working - read actual logs and state
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Find log directories
LOGS_DIR = Path("logs")
STATE_DIR = Path("state")
DATA_DIR = Path("data")

print("=" * 80)
print("DEEP DISPLACEMENT ANALYSIS")
print("=" * 80)
print()

# 1. Check displacement logs (all locations)
print("1. DISPLACEMENT LOGS")
print("-" * 80)
displacement_files = [
    LOGS_DIR / "displacement.jsonl",
    DATA_DIR / "displacement.jsonl",
    Path("displacement.jsonl")
]

found_logs = False
for log_file in displacement_files:
    if log_file.exists():
        print(f"Found: {log_file}")
        found_logs = True
        
        # Read last 100 lines
        lines = log_file.read_text().splitlines()[-100:]
        now = time.time()
        cutoff_1h = now - 3600
        
        events_1h = []
        for line in lines:
            try:
                event = json.loads(line.strip())
                ts = event.get("ts") or event.get("_ts", 0)
                if isinstance(ts, str):
                    # Parse ISO timestamp
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        ts = dt.timestamp()
                    except:
                        ts = 0
                if ts > cutoff_1h:
                    events_1h.append((ts, event))
            except:
                pass
        
        if events_1h:
            print(f"  Events in last hour: {len(events_1h)}")
            for ts, e in sorted(events_1h, key=lambda x: x[0])[-10:]:
                msg = e.get("msg", "unknown")
                symbol = e.get("symbol", "unknown")
                reasons = e.get("reasons", {})
                new_score = e.get("new_signal_score", 0)
                print(f"  {datetime.fromtimestamp(ts).strftime('%H:%M:%S')}: {msg} - {symbol} (score: {new_score:.2f})")
                if reasons:
                    print(f"    Reasons: {reasons}")
        else:
            print("  ⚠️  No events in last hour")
        break

if not found_logs:
    print("⚠️  No displacement log file found in any location")
    print("  This means displacement may not be logging OR logs are elsewhere")
print()

# 2. Check gate logs for displacement attempts
print("2. GATE LOGS (displacement attempts)")
print("-" * 80)
gate_file = LOGS_DIR / "gate.jsonl"
if gate_file.exists():
    lines = gate_file.read_text().splitlines()[-200:]
    now = time.time()
    cutoff_1h = now - 3600
    
    displacement_attempts = []
    for line in lines:
        try:
            event = json.loads(line.strip())
            msg = event.get("msg", "")
            if "displacement" in msg.lower() or "max_positions" in msg.lower():
                ts = event.get("ts") or event.get("_ts", 0)
                if isinstance(ts, str):
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        ts = dt.timestamp()
                    except:
                        ts = 0
                if ts > cutoff_1h:
                    displacement_attempts.append((ts, event))
        except:
            pass
    
    if displacement_attempts:
        print(f"Displacement-related gate events in last hour: {len(displacement_attempts)}")
        for ts, e in sorted(displacement_attempts, key=lambda x: x[0])[-10:]:
            msg = e.get("msg", "unknown")
            symbol = e.get("symbol", "unknown")
            no_candidates = e.get("no_candidates", False)
            print(f"  {datetime.fromtimestamp(ts).strftime('%H:%M:%S')}: {msg} - {symbol}")
            if no_candidates:
                print(f"    ⚠️  NO DISPLACEMENT CANDIDATES FOUND")
    else:
        print("⚠️  No displacement attempts in gate logs")
else:
    print("⚠️  Gate log not found")
print()

# 3. Check position metadata to see actual positions
print("3. POSITION METADATA")
print("-" * 80)
metadata_file = STATE_DIR / "position_metadata.json"
if metadata_file.exists():
    try:
        metadata = json.loads(metadata_file.read_text())
        print(f"Positions in metadata: {len(metadata)}")
        
        now = datetime.now(timezone.utc)
        for symbol, pos_data in list(metadata.items())[:20]:  # First 20
            entry_ts_str = pos_data.get("entry_ts")
            entry_score = pos_data.get("entry_score", 0)
            
            if entry_ts_str:
                try:
                    entry_ts = datetime.fromisoformat(entry_ts_str.replace("Z", "+00:00"))
                    if entry_ts.tzinfo is None:
                        entry_ts = entry_ts.replace(tzinfo=timezone.utc)
                    age_hours = (now - entry_ts).total_seconds() / 3600
                    print(f"  {symbol}: age={age_hours:.1f}h, entry_score={entry_score:.2f}")
                except:
                    print(f"  {symbol}: entry_score={entry_score:.2f} (age unknown)")
            else:
                print(f"  {symbol}: entry_score={entry_score:.2f} (no entry_ts)")
    except Exception as e:
        print(f"⚠️  Could not read metadata: {e}")
else:
    print("⚠️  Position metadata file not found")
print()

# 4. Check recent signals to see what scores are being generated
print("4. RECENT SIGNAL SCORES")
print("-" * 80)
signals_file = LOGS_DIR / "signals.jsonl"
if signals_file.exists():
    lines = signals_file.read_text().splitlines()[-50:]
    now = time.time()
    cutoff_10m = now - 600
    
    recent_signals = []
    for line in lines:
        try:
            event = json.loads(line.strip())
            cluster = event.get("cluster", {})
            symbol = cluster.get("symbol", "")
            score = cluster.get("score", 0)
            ts = event.get("ts") or event.get("_ts", 0)
            if isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    ts = dt.timestamp()
                except:
                    ts = 0
            if ts > cutoff_10m and score > 0:
                recent_signals.append((ts, symbol, score))
        except:
            pass
    
    if recent_signals:
        print(f"Recent signals (last 10 min): {len(recent_signals)}")
        for ts, symbol, score in sorted(recent_signals, key=lambda x: x[0])[-10:]:
            print(f"  {datetime.fromtimestamp(ts).strftime('%H:%M:%S')}: {symbol} = {score:.2f}")
    else:
        print("⚠️  No recent signals")
else:
    print("⚠️  Signals log not found")
print()

# 5. Check Config values
print("5. DISPLACEMENT CONFIG VALUES")
print("-" * 80)
print("Expected thresholds (from code):")
print("  DISPLACEMENT_MIN_AGE_HOURS = 4")
print("  DISPLACEMENT_MAX_PNL_PCT = 0.01 (1%)")
print("  DISPLACEMENT_SCORE_ADVANTAGE = 2.0")
print("  DISPLACEMENT_COOLDOWN_HOURS = 6")
print()
print("These are VERY STRICT criteria:")
print("  - Position must be > 4 hours old")
print("  - Position P&L must be within ±1% (most positions move more)")
print("  - New signal must exceed original by 2.0 points")
print("  - Position not displaced in last 6 hours")
print()

# 6. Root cause analysis
print("=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)
print()
print("Based on the evidence:")
print("  1. Displacement is being CALLED (we see 'max_positions_reached' in gate logs)")
print("  2. Displacement is NOT finding candidates (no displacement events logged)")
print("  3. This means ALL positions are failing one of the 4 criteria:")
print()
print("Most likely causes:")
print("  A) Positions are too new (< 4 hours old)")
print("  B) Positions have P&L outside ±1% (too strict - most positions move more)")
print("  C) New signals don't exceed original by 2.0 (very high bar)")
print("  D) All positions recently displaced (6-hour cooldown)")
print()
print("SOLUTION: We need to see the ACTUAL position data to know which criteria")
print("          are failing. The diagnostic can't access Alpaca API, so we need")
print("          to either:")
print("  1. Add better logging to displacement function")
print("  2. Relax the criteria (especially max_pnl_pct)")
print("  3. Check if exits are working (should close losing/stale positions)")
print()
