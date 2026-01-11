#!/usr/bin/env python3
"""Check current trading status after fixes"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

def check_recent_scores():
    """Check recent composite scores"""
    print("=" * 80)
    print("1. RECENT COMPOSITE SCORES")
    print("=" * 80)
    
    attr_path = Path("data/uw_attribution.jsonl")
    if not attr_path.exists():
        print("No attribution file")
        return
    
    records = []
    with open(attr_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except:
                    pass
    
    if not records:
        print("No attribution records")
        return
    
    recent = records[-30:]
    print(f"Total records: {len(records)}")
    print(f"Recent (last 30):")
    
    scores = [r.get("score", 0.0) for r in recent]
    decisions = [r.get("decision", "unknown") for r in recent]
    
    signals = decisions.count("signal")
    rejected = decisions.count("rejected")
    
    print(f"  Signals: {signals}, Rejected: {rejected}")
    if scores:
        print(f"  Score range: {min(scores):.3f} - {max(scores):.3f}")
        print(f"  Average: {sum(scores)/len(scores):.3f}")
        print(f"  >= 2.7: {len([s for s in scores if s >= 2.7])}/{len(scores)}")
        print(f"  >= 3.5: {len([s for s in scores if s >= 3.5])}/{len(scores)}")
        
        print(f"\n  Recent scores:")
        for r in recent[-10:]:
            symbol = r.get("symbol", "UNKNOWN")
            score = r.get("score", 0.0)
            decision = r.get("decision", "unknown")
            threshold = r.get("threshold", 2.7)
            components = r.get("components", {})
            flow = components.get("flow", 0.0)
            freshness = components.get("freshness_factor", 1.0)
            print(f"    {symbol}: score={score:.3f}, flow={flow:.3f}, freshness={freshness:.3f}, decision={decision}, threshold={threshold:.2f}")

def check_run_cycles():
    """Check recent run cycles"""
    print("\n" + "=" * 80)
    print("2. RECENT RUN CYCLES")
    print("=" * 80)
    
    run_path = Path("logs/run.jsonl")
    if not run_path.exists():
        print("No run log")
        return
    
    cycles = []
    with open(run_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    cycles.append(json.loads(line))
                except:
                    pass
    
    if not cycles:
        print("No run cycles")
        return
    
    recent = cycles[-10:]
    print(f"Total cycles: {len(cycles)}")
    print(f"Recent (last 10):")
    
    for c in recent:
        ts = c.get("ts", "")[:19]
        clusters = c.get("clusters", 0)
        orders = c.get("orders", 0)
        metrics = c.get("metrics", {})
        composite = metrics.get("composite_enabled", False)
        print(f"  {ts}: clusters={clusters}, orders={orders}, composite={composite}")

def check_gate_events():
    """Check recent gate events"""
    print("\n" + "=" * 80)
    print("3. RECENT GATE EVENTS")
    print("=" * 80)
    
    gate_path = Path("logs/composite_gate.jsonl")
    if not gate_path.exists():
        print("No composite gate log")
        return
    
    events = []
    with open(gate_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except:
                    pass
    
    if not events:
        print("No gate events")
        return
    
    recent = events[-30:]
    accepted = [e for e in recent if e.get("msg") == "accepted"]
    rejected = [e for e in recent if e.get("msg") == "rejected"]
    
    print(f"Total events: {len(events)}")
    print(f"Recent (last 30): {len(accepted)} accepted, {len(rejected)} rejected")
    
    if accepted:
        print(f"\n  Recent accepted:")
        for e in accepted[-5:]:
            symbol = e.get("symbol", "UNKNOWN")
            score = e.get("score", 0.0)
            print(f"    {symbol}: score={score:.3f}")
    
    if rejected:
        print(f"\n  Recent rejections:")
        for e in rejected[-10:]:
            symbol = e.get("symbol", "UNKNOWN")
            score = e.get("score", 0.0)
            threshold = e.get("threshold", 2.7)
            reason = e.get("rejection_reason", "unknown")
            print(f"    {symbol}: score={score:.3f} < threshold={threshold:.2f}, reason={reason}")

def check_thresholds():
    """Check current thresholds"""
    print("\n" + "=" * 80)
    print("4. CURRENT THRESHOLDS")
    print("=" * 80)
    
    try:
        import uw_composite_v2
        thresholds = uw_composite_v2.ENTRY_THRESHOLDS
        print(f"Entry thresholds: {thresholds}")
        if thresholds.get("base") > 3.0:
            print("  WARNING: Base threshold is too high!")
        else:
            print("  OK: Thresholds look reasonable")
    except Exception as e:
        print(f"  Error: {e}")

def check_freshness_fix():
    """Check if freshness fix is in main.py"""
    print("\n" + "=" * 80)
    print("5. FRESHNESS FIX VERIFICATION")
    print("=" * 80)
    
    try:
        with open("main.py") as f:
            content = f.read()
            if 'enriched["freshness"] = 0.9' in content:
                print("  OK: Freshness fix present (minimum 0.9)")
            else:
                print("  WARNING: Freshness fix may be missing")
    except Exception as e:
        print(f"  Error: {e}")

def check_cache_sample():
    """Check cache data quality"""
    print("\n" + "=" * 80)
    print("6. CACHE DATA SAMPLE")
    print("=" * 80)
    
    cache_path = Path("data/uw_flow_cache.json")
    if not cache_path.exists():
        print("  Cache file not found")
        return
    
    cache = json.load(open(cache_path))
    symbols = [k for k in cache.keys() if not k.startswith("_")]
    
    print(f"  Total symbols: {len(symbols)}")
    
    if symbols:
        sample = symbols[0]
        data = cache[sample]
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                pass
        
        print(f"  Sample ({sample}):")
        print(f"    sentiment: {data.get('sentiment')}")
        print(f"    conviction: {data.get('conviction')}")
        print(f"    has_dark_pool: {bool(data.get('dark_pool'))}")
        print(f"    has_insider: {bool(data.get('insider'))}")

if __name__ == "__main__":
    check_recent_scores()
    check_run_cycles()
    check_gate_events()
    check_thresholds()
    check_freshness_fix()
    check_cache_sample()
