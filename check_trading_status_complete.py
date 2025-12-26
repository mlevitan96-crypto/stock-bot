#!/usr/bin/env python3
"""
Complete trading status check - runs on droplet
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime

def run_command(cmd):
    """Run shell command"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), -1

print("=" * 80)
print("COMPLETE TRADING STATUS CHECK")
print("=" * 80)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 1. Bot status
print("1. BOT STATUS")
print("-" * 80)
stdout, stderr, code = run_command("systemctl is-active trading-bot.service")
print(f"Status: {stdout}")
if code != 0:
    print(f"Error: {stderr}")

# 2. Current positions
print("\n2. CURRENT POSITIONS")
print("-" * 80)
positions_file = Path("state/positions.json")
if positions_file.exists():
    with positions_file.open() as f:
        positions = json.load(f)
    print(f"Total: {len(positions)}")
    for sym, info in positions.items():
        print(f"  {sym}: {info.get('side', '?')} {info.get('qty', 0)} @ ${info.get('entry_price', 0):.2f}")
else:
    print("No positions file")

# 3. Max positions check
print("\n3. MAX POSITIONS CONFIG")
print("-" * 80)
stdout, _, _ = run_command("grep MAX_CONCURRENT_POSITIONS main.py | head -1")
print(f"Config: {stdout[:100]}")

# 4. Recent logs - scoring
print("\n4. RECENT SCORING (last 20 lines)")
print("-" * 80)
stdout, _, _ = run_command("tail -100 logs/main.log 2>/dev/null | grep -i 'composite_score\\|score:' | tail -10")
if stdout:
    for line in stdout.split('\n')[:10]:
        print(f"  {line[:120]}")
else:
    print("  No scoring entries found")

# 5. Recent logs - blocked
print("\n5. RECENT BLOCKED TRADES (last 10)")
print("-" * 80)
stdout, _, _ = run_command("tail -100 logs/main.log 2>/dev/null | grep -i 'blocked\\|gate' | tail -10")
if stdout:
    for line in stdout.split('\n')[:10]:
        print(f"  {line[:120]}")
else:
    print("  No blocked entries found")

# 6. Threshold state
print("\n6. SELF-HEALING THRESHOLD")
print("-" * 80)
threshold_file = Path("state/self_healing_threshold.json")
if threshold_file.exists():
    with threshold_file.open() as f:
        state = json.load(f)
    adj = state.get("adjustment", 0.0)
    print(f"Adjustment: +{adj:.2f}")
    print(f"Current Threshold: {2.0 + adj:.2f}")
    print(f"Activated: {adj > 0}")
else:
    print("Using base threshold: 2.0")

# 7. Adaptive weights
print("\n7. ADAPTIVE WEIGHTS")
print("-" * 80)
weights_file = Path("state/signal_weights.json")
if weights_file.exists():
    with weights_file.open() as f:
        state = json.load(f)
    bands = state.get("weight_bands", {})
    non_default = [(k, v.get("current", 1.0)) for k, v in bands.items() 
                   if isinstance(v, dict) and v.get("current", 1.0) != 1.0]
    print(f"Total components: {len(bands)}")
    print(f"Non-default multipliers: {len(non_default)}")
    if non_default:
        for comp, mult in non_default[:5]:
            print(f"  {comp}: {mult:.3f}")
else:
    print("No weights file")

# 8. UW Cache
print("\n8. UW CACHE")
print("-" * 80)
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    with cache_file.open() as f:
        cache = json.load(f)
    symbols = [k for k in cache.keys() if k != "_metadata"]
    print(f"Symbols: {len(symbols)}")
    if symbols:
        print(f"Sample: {', '.join(symbols[:5])}")
else:
    print("No cache file")

# 9. Recent trades
print("\n9. RECENT TRADES")
print("-" * 80)
attribution_file = Path("logs/attribution.jsonl")
if not attribution_file.exists():
    attribution_file = Path("data/attribution.jsonl")

if attribution_file.exists():
    trades = []
    with attribution_file.open() as f:
        for line in reversed(list(f)[-20:]):
            try:
                trade = json.loads(line.strip())
                if trade.get("type") == "attribution":
                    trades.append(trade)
            except:
                pass
    print(f"Last 20 trades: {len(trades)}")
    for t in trades[:5]:
        sym = t.get("symbol", "?")
        pnl = t.get("pnl_pct", 0) or t.get("context", {}).get("pnl_pct", 0)
        print(f"  {sym}: {pnl:.2f}%")
else:
    print("No attribution file")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
num_pos = len(positions) if positions_file.exists() else 0
print(f"Positions: {num_pos}/16 (max)")
print(f"Threshold: {2.0 + (state.get('adjustment', 0.0) if threshold_file.exists() else 0.0):.2f}")

if num_pos < 3:
    print("\n[WARN] Low position count - possible causes:")
    print("  1. Threshold too high")
    print("  2. Not enough signals meeting threshold")
    print("  3. Market conditions")
    print("  4. Gates blocking trades")

