#!/usr/bin/env python3
"""Diagnose current bot issues"""

import json
from pathlib import Path
import sys
sys.path.insert(0, '/root/stock-bot')

print("="*80)
print("DIAGNOSING CURRENT ISSUES")
print("="*80)

# 1. Check SRE metrics generation
print("\n[1] SRE METRICS STATUS")
print("-"*80)
sre_file = Path("state/sre_metrics.json")
if sre_file.exists():
    sre = json.load(open(sre_file))
    overall = sre.get("overall_health", "UNKNOWN")
    print(f"SRE Metrics File: EXISTS")
    print(f"Overall Health: {overall}")
    if overall == "UNKNOWN":
        print("ISSUE: SRE metrics show UNKNOWN health")
        print("Likely cause: Metrics not being generated/updated properly")
else:
    print("SRE Metrics File: MISSING")
    print("ISSUE: sre_metrics.json not found")
    print("Likely cause: SRE monitoring not running or not saving metrics")

# 2. Check portfolio delta calculation
print("\n[2] PORTFOLIO DELTA CALCULATION")
print("-"*80)
try:
    from main import AlpacaExecutor, Config
    executor = AlpacaExecutor(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
    positions = executor.api.list_positions()
    print(f"Alpaca positions: {len(positions)}")
    
    # Try to find where net_delta_pct is calculated
    # Check if it's incorrectly calculating delta when positions are 0
    print(f"Portfolio delta gate blocking despite {len(positions)} positions")
    print("ISSUE: portfolio_already_70pct_long_delta gate blocking with 0 positions")
    print("Likely cause: net_delta_pct calculation bug - may be defaulting to high value")
except Exception as e:
    print(f"Error checking positions: {e}")

# 3. Check gate events detail
print("\n[3] RECENT GATE EVENTS DETAIL")
print("-"*80)
gate_file = Path("logs/gate.jsonl")
if gate_file.exists():
    lines = gate_file.read_text().strip().split('\n')[-5:]
    events = [json.loads(l) for l in lines if l.strip()]
    
    for e in events:
        if e.get("reason") == "portfolio_already_70pct_long_delta":
            net_delta = e.get("net_delta_pct", "N/A")
            symbol = e.get("symbol", "?")
            print(f"  {symbol}: net_delta_pct={net_delta}")
            if net_delta != "N/A" and net_delta > 70:
                print(f"    BUG: net_delta_pct={net_delta} but should be 0% with no positions")

# 4. Check if SRE monitoring is running
print("\n[4] SRE MONITORING STATUS")
print("-"*80)
try:
    from sre_monitoring import get_sre_health
    health = get_sre_health()
    overall = health.get("overall_health", "UNKNOWN")
    print(f"get_sre_health() returns: {overall}")
    if overall == "UNKNOWN":
        print("ISSUE: SRE health check returning UNKNOWN")
        warnings = health.get("warnings", [])
        critical = health.get("critical_issues", [])
        print(f"  Warnings: {warnings}")
        print(f"  Critical: {critical}")
except Exception as e:
    print(f"Error calling get_sre_health(): {e}")

print("\n" + "="*80)
print("SUMMARY OF ISSUES")
print("="*80)
print("1. SRE Health: UNKNOWN - Metrics may not be updating")
print("2. Portfolio Delta Gate: Blocking despite 0 positions (calculation bug)")
print("3. 0 clusters, 0 orders: Likely due to portfolio delta gate blocking all signals")
