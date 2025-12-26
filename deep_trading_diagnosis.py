#!/usr/bin/env python3
"""
Deep diagnosis of why trading activity is low
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except:
        return ""

print("=" * 80)
print("DEEP TRADING DIAGNOSIS")
print("=" * 80)

# 1. Check Alpaca positions directly
print("\n1. ALPACA POSITIONS (via API)")
print("-" * 80)
# This would require API access, but we can check if positions.json exists
positions_file = Path("state/positions.json")
if positions_file.exists():
    with positions_file.open() as f:
        positions = json.load(f)
    print(f"Positions file: {len(positions)} positions")
else:
    print("No positions.json - checking if positions tracked via Alpaca API directly")

# 2. Check if main.py is actually running and processing
print("\n2. MAIN.PY PROCESS STATUS")
print("-" * 80)
stdout = run_cmd("ps aux | grep 'python.*main.py' | grep -v grep")
if stdout:
    print("main.py is running")
    print(stdout[:200])
else:
    print("main.py NOT running!")

# 3. Check recent main.log for activity
print("\n3. RECENT MAIN.PY ACTIVITY (last 50 lines)")
print("-" * 80)
stdout = run_cmd("tail -50 logs/main.log 2>/dev/null")
if stdout:
    lines = stdout.split('\n')
    for line in lines[-20:]:
        if any(keyword in line.lower() for keyword in ['score', 'cluster', 'trade', 'execute', 'gate']):
            print(f"  {line[:120]}")
else:
    print("  No main.log or empty")

# 4. Check if signals are being generated
print("\n4. SIGNAL GENERATION")
print("-" * 80)
# Check if clusters are being created
stdout = run_cmd("tail -100 logs/main.log 2>/dev/null | grep -i 'cluster\\|signal' | tail -10")
if stdout:
    for line in stdout.split('\n')[:10]:
        print(f"  {line[:120]}")
else:
    print("  No signal/cluster entries in logs")

# 5. Check UW daemon
print("\n5. UW DAEMON STATUS")
print("-" * 80)
stdout = run_cmd("ps aux | grep 'uw_flow_daemon' | grep -v grep")
if stdout:
    print("UW daemon is running")
else:
    print("UW daemon NOT running!")

# 6. Check cache freshness
print("\n6. CACHE FRESHNESS")
print("-" * 80)
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    mtime = cache_file.stat().st_mtime
    age_minutes = (datetime.now().timestamp() - mtime) / 60
    print(f"Cache age: {age_minutes:.1f} minutes")
    if age_minutes > 10:
        print("  [WARN] Cache is stale (>10 minutes)")
    
    with cache_file.open() as f:
        cache = json.load(f)
    metadata = cache.get("_metadata", {})
    last_update = metadata.get("last_update", 0)
    if last_update:
        update_age = (datetime.now().timestamp() - last_update) / 60
        print(f"Last update: {update_age:.1f} minutes ago")

# 7. Check adaptive weights initialization
print("\n7. ADAPTIVE WEIGHTS INITIALIZATION")
print("-" * 80)
weights_file = Path("state/signal_weights.json")
if weights_file.exists():
    print("Weights file exists")
    with weights_file.open() as f:
        state = json.load(f)
    bands = state.get("weight_bands", {})
    print(f"Components: {len(bands)}")
    if len(bands) == 0:
        print("  [ERROR] No weight bands initialized!")
else:
    print("  [ERROR] Weights file does not exist!")
    print("  This means adaptive weights are not initialized")
    print("  The bot may be using default weights only")

# 8. Check if run_once is being called
print("\n8. EXECUTION CYCLE")
print("-" * 80)
stdout = run_cmd("tail -200 logs/main.log 2>/dev/null | grep -i 'run_once\\|cycle\\|decide_and_execute' | tail -10")
if stdout:
    for line in stdout.split('\n')[:10]:
        print(f"  {line[:120]}")
else:
    print("  No execution cycle entries")

# 9. Check for errors
print("\n9. RECENT ERRORS")
print("-" * 80)
stdout = run_cmd("tail -100 logs/main.log 2>/dev/null | grep -i 'error\\|exception\\|traceback' | tail -10")
if stdout:
    for line in stdout.split('\n')[:10]:
        print(f"  {line[:150]}")
else:
    print("  No errors found")

# 10. Check threshold and gates
print("\n10. THRESHOLD AND GATES")
print("-" * 80)
threshold_file = Path("state/self_healing_threshold.json")
if threshold_file.exists():
    with threshold_file.open() as f:
        state = json.load(f)
    adj = state.get("adjustment", 0.0)
    print(f"Self-healing threshold: {2.0 + adj:.2f}")
else:
    print("Base threshold: 2.0")

# Check MIN_EXEC_SCORE from env
stdout = run_cmd("grep MIN_EXEC_SCORE .env 2>/dev/null || echo 'Not in .env'")
print(f"MIN_EXEC_SCORE from env: {stdout}")

print("\n" + "=" * 80)
print("DIAGNOSIS SUMMARY")
print("=" * 80)
print("Key issues to check:")
print("1. Are signals being generated? (check logs for 'cluster' entries)")
print("2. Are scores being calculated? (check logs for 'composite_score')")
print("3. Are gates blocking trades? (check logs for 'gate' entries)")
print("4. Is adaptive weights file initialized?")
print("5. Is main.py actually running the trading loop?")

