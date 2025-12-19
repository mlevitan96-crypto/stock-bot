#!/usr/bin/env python3
"""
Diagnose why bot isn't executing cycles
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timezone

LOGS_DIR = Path("logs")
DATA_DIR = Path("data")

print("=" * 80)
print("BOT EXECUTION DIAGNOSIS")
print("=" * 80)
print()

# 1. Check run.jsonl for recent activity
print("1. RECENT EXECUTION CYCLES")
print("-" * 80)
run_file = LOGS_DIR / "run.jsonl"
if run_file.exists():
    now = time.time()
    lines = run_file.read_text().splitlines()
    print(f"Total cycles in log: {len(lines)}")
    
    if lines:
        # Get last 5 cycles
        for line in lines[-5:]:
            try:
                event = json.loads(line.strip())
                ts = event.get("_ts", 0)
                age_min = (now - ts) / 60
                clusters = event.get("clusters", 0)
                orders = event.get("orders", 0)
                msg = event.get("msg", "unknown")
                print(f"  {age_min:.1f} min ago: {msg}, {clusters} clusters, {orders} orders")
            except:
                pass
    else:
        print("  No cycles logged")
else:
    print("  Run log file does not exist")
print()

# 2. Check for errors in logs
print("2. RECENT ERRORS")
print("-" * 80)
error_files = [
    LOGS_DIR / "worker_error.jsonl",
    LOGS_DIR / "alert_error.jsonl",
    DATA_DIR / "uw_error.jsonl"
]

for error_file in error_files:
    if error_file.exists():
        now = time.time()
        cutoff_1h = now - 3600
        errors_1h = []
        
        for line in error_file.read_text().splitlines()[-50:]:
            try:
                event = json.loads(line.strip())
                if event.get("_ts", 0) > cutoff_1h:
                    errors_1h.append(event)
            except:
                pass
        
        if errors_1h:
            print(f"{error_file.name}: {len(errors_1h)} errors in last hour")
            for err in errors_1h[-3:]:
                print(f"  {err.get('event', 'unknown')}: {err.get('error', 'unknown')[:100]}")
        else:
            print(f"{error_file.name}: No errors in last hour")
    else:
        print(f"{error_file.name}: File does not exist")
print()

# 3. Check heartbeat
print("3. HEARTBEAT STATUS")
print("-" * 80)
heartbeat_file = LOGS_DIR / "heartbeat.jsonl"
if heartbeat_file.exists():
    now = time.time()
    lines = heartbeat_file.read_text().splitlines()
    if lines:
        try:
            last_heartbeat = json.loads(lines[-1].strip())
            hb_ts = last_heartbeat.get("_ts", 0)
            hb_age = (now - hb_ts) / 60
            print(f"Last heartbeat: {hb_age:.1f} minutes ago")
            if hb_age > 5:
                print(f"  ⚠️  Heartbeat stale (should be < 1 minute)")
        except:
            print("  Could not parse heartbeat")
    else:
        print("  No heartbeat entries")
else:
    print("  Heartbeat file does not exist")
print()

# 4. Check if bot is stuck
print("4. PROCESS STATUS")
print("-" * 80)
import subprocess
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
if "main.py" in result.stdout:
    for line in result.stdout.split("\n"):
        if "main.py" in line and "grep" not in line:
            parts = line.split()
            if len(parts) > 10:
                pid = parts[1]
                cpu = parts[2]
                mem = parts[3]
                time_str = parts[9]
                print(f"PID: {pid}, CPU: {cpu}%, MEM: {mem}%, TIME: {time_str}")
                if float(cpu) < 0.1:
                    print("  ⚠️  CPU usage very low - bot may be stuck or sleeping")
else:
    print("  Bot process not found")
print()

# 5. Check environment variables
print("5. CRITICAL ENV VARS")
print("-" * 80)
critical_vars = ["UW_API_KEY", "ALPACA_KEY", "ALPACA_SECRET", "TRADING_MODE"]
for var in critical_vars:
    val = os.getenv(var, "")
    if val:
        # Mask sensitive values
        if "KEY" in var or "SECRET" in var:
            print(f"{var}: {'*' * min(len(val), 20)} (set)")
        else:
            print(f"{var}: {val}")
    else:
        print(f"{var}: NOT SET ⚠️")
print()

# 6. Check recent log activity
print("6. RECENT LOG ACTIVITY")
print("-" * 80)
log_files = [
    ("run.jsonl", LOGS_DIR),
    ("signals.jsonl", LOGS_DIR),
    ("gate.jsonl", LOGS_DIR),
    ("decisions.jsonl", LOGS_DIR),
]

now = time.time()
cutoff_1h = now - 3600

for log_name, log_dir in log_files:
    log_file = log_dir / log_name
    if log_file.exists():
        try:
            mtime = log_file.stat().st_mtime
            age_min = (now - mtime) / 60
            if age_min < 60:
                print(f"{log_name}: Updated {age_min:.1f} min ago ✅")
            else:
                print(f"{log_name}: Updated {age_min:.1f} min ago ⚠️")
        except:
            print(f"{log_name}: Could not check")
    else:
        print(f"{log_name}: Does not exist")
print()

print("=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
print()
print("If no execution cycles, check:")
print("  1. Is the bot actually running the main loop?")
print("  2. Is there an exception preventing execution?")
print("  3. Is the bot stuck in a sleep/wait?")
print("  4. Check main.py logs for exceptions")
print()
