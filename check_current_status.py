#!/usr/bin/env python3
"""Check current bot status and diagnostics"""

import json
from pathlib import Path
from datetime import datetime

print("="*80)
print("CURRENT BOT STATUS CHECK")
print("="*80)

# 1. Check SRE Metrics
print("\n[1] SRE METRICS & WARNINGS")
print("-"*80)
sre_file = Path("state/sre_metrics.json")
if sre_file.exists():
    sre = json.load(open(sre_file))
    overall = sre.get("overall_health", "UNKNOWN")
    warnings = sre.get("warnings", [])
    critical = sre.get("critical_issues", [])
    
    print(f"Overall Health: {overall}")
    if critical:
        print(f"\nCRITICAL ISSUES ({len(critical)}):")
        for issue in critical:
            print(f"  - {issue}")
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    
    # Check signal components
    signals = sre.get("signal_components", {})
    if signals:
        print(f"\nSignal Components Status:")
        for name, data in list(signals.items())[:10]:
            status = data.get("status", "UNKNOWN")
            freshness = data.get("data_freshness_sec", 0)
            print(f"  {name}: {status} (freshness: {freshness/60:.1f}min)")
else:
    print("SRE metrics file not found")

# 2. Check Positions
print("\n[2] POSITIONS")
print("-"*80)
meta_file = Path("state/position_metadata.json")
if meta_file.exists():
    meta = json.load(open(meta_file))
    print(f"Positions in metadata: {len(meta)}")
    if meta:
        for sym, data in list(meta.items())[:10]:
            qty = data.get("qty", 0)
            price = data.get("entry_price", 0)
            print(f"  {sym}: {qty} @ ${price:.2f}")
    else:
        print("No positions in metadata")
else:
    print("Position metadata file not found")

# 3. Check Recent Gate Events
print("\n[3] RECENT GATE EVENTS")
print("-"*80)
gate_file = Path("logs/gate.jsonl")
if gate_file.exists():
    lines = gate_file.read_text().strip().split('\n')[-20:]
    events = [json.loads(l) for l in lines if l.strip()]
    
    # Group by reason
    by_reason = {}
    for e in events:
        reason = e.get("reason", "unknown")
        symbol = e.get("symbol", "?")
        if reason not in by_reason:
            by_reason[reason] = []
        by_reason[reason].append(symbol)
    
    print(f"Recent gate events (last 20):")
    for reason, syms in sorted(by_reason.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {reason}: {len(syms)} times ({', '.join(syms[:5])}{'...' if len(syms) > 5 else ''})")
else:
    print("Gate log file not found")

# 4. Check Recent Cycles
print("\n[4] RECENT CYCLES")
print("-"*80)
run_file = Path("logs/run.jsonl")
if run_file.exists():
    lines = run_file.read_text().strip().split('\n')[-3:]
    for line in lines:
        if line.strip():
            try:
                r = json.loads(line)
                clusters = r.get("clusters", 0)
                orders = r.get("orders", 0)
                ts = r.get("ts", r.get("_ts", "?"))[:19] if isinstance(r.get("ts", ""), str) else "?"
                print(f"  {ts}: clusters={clusters}, orders={orders}")
            except:
                pass
else:
    print("Run log file not found")

# 5. Check Alpaca Positions
print("\n[5] ALPACA POSITIONS")
print("-"*80)
try:
    from main import AlpacaExecutor, Config
    executor = AlpacaExecutor(Config.ALPACA_KEY, Config.ALPACA_SECRET, Config.ALPACA_BASE_URL)
    positions = executor.api.list_positions()
    print(f"Alpaca positions: {len(positions)}")
    if positions:
        for p in positions[:10]:
            print(f"  {p.symbol}: {p.qty} @ ${float(p.avg_entry_price):.2f}")
    else:
        print("No positions in Alpaca")
except Exception as e:
    print(f"Error checking Alpaca: {e}")

print("\n" + "="*80)
