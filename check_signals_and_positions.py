#!/usr/bin/env python3
"""Check signals generating and why bot has 0 positions"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def load_jsonl(path):
    """Load JSONL file, return list of records"""
    if not Path(path).exists():
        return []
    records = []
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except:
                        pass
    except Exception as e:
        print(f"Error loading {path}: {e}")
    return records

def main():
    print("=" * 80)
    print("SIGNAL GENERATION & POSITION DIAGNOSTICS")
    print("=" * 80)
    print()
    
    # 1. Check recent signals
    print("1. RECENT SIGNALS (last 20)")
    print("-" * 80)
    signals = load_jsonl("logs/signals.jsonl")
    recent_signals = signals[-20:] if len(signals) > 20 else signals
    print(f"Total signals in log: {len(signals)}")
    print(f"Recent signals: {len(recent_signals)}")
    if recent_signals:
        for sig in recent_signals[-5:]:
            cluster = sig.get("cluster", {})
            symbol = cluster.get("ticker", "UNKNOWN")
            score = cluster.get("composite_score", 0.0)
            source = cluster.get("source", "unknown")
            direction = cluster.get("direction", "unknown")
            print(f"  {symbol}: score={score:.2f}, source={source}, direction={direction}")
    else:
        print("  ⚠️  NO SIGNALS FOUND")
    print()
    
    # 2. Check gate events
    print("2. RECENT GATE EVENTS (last 30)")
    print("-" * 80)
    gate_events = load_jsonl("logs/gate.jsonl")
    recent_gates = gate_events[-30:] if len(gate_events) > 30 else gate_events
    print(f"Total gate events: {len(gate_events)}")
    
    # Count by type
    gate_types = {}
    for g in recent_gates:
        gtype = g.get("msg", "unknown")
        gate_types[gtype] = gate_types.get(gtype, 0) + 1
    
    print(f"Recent gate events by type:")
    for gtype, count in sorted(gate_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {gtype}: {count}")
    
    # Show recent rejections
    rejections = [g for g in recent_gates if "blocked" in g.get("msg", "").lower() or "rejected" in g.get("msg", "").lower()]
    if rejections:
        print(f"\nRecent rejections ({len(rejections)}):")
        for r in rejections[-10:]:
            symbol = r.get("symbol", "UNKNOWN")
            msg = r.get("msg", "")
            score = r.get("score", 0.0)
            print(f"  {symbol}: {msg}, score={score:.2f}")
    print()
    
    # 3. Check run cycles
    print("3. RECENT RUN CYCLES (last 10)")
    print("-" * 80)
    run_cycles = load_jsonl("logs/run.jsonl")
    recent_runs = run_cycles[-10:] if len(run_cycles) > 10 else run_cycles
    print(f"Total run cycles: {len(run_cycles)}")
    if recent_runs:
        for r in recent_runs:
            ts = r.get("ts", "")
            clusters = r.get("clusters", 0)
            orders = r.get("orders", 0)
            metrics = r.get("metrics", {})
            total_pnl = metrics.get("total_pnl", 0)
            trades = metrics.get("trades", 0)
            composite_enabled = metrics.get("composite_enabled", False)
            print(f"  {ts[:19]}: clusters={clusters}, orders={orders}, pnl={total_pnl:.2f}, trades={trades}, composite={composite_enabled}")
    print()
    
    # 4. Check attribution (scores)
    print("4. RECENT ATTRIBUTION (scores - last 30)")
    print("-" * 80)
    attribution = load_jsonl("data/uw_attribution.jsonl")
    recent_attr = attribution[-30:] if len(attribution) > 30 else attribution
    print(f"Total attribution records: {len(attribution)}")
    
    if recent_attr:
        # Score distribution
        scores = [a.get("score", 0.0) for a in recent_attr]
        decisions = [a.get("decision", "unknown") for a in recent_attr]
        
        signal_count = decisions.count("signal")
        rejected_count = decisions.count("rejected")
        
        print(f"Recent decisions: {signal_count} signals, {rejected_count} rejected")
        if scores:
            print(f"Score range: {min(scores):.2f} - {max(scores):.2f}, avg={sum(scores)/len(scores):.2f}")
        
        # Show recent signals vs rejections
        print(f"\nRecent records:")
        for a in recent_attr[-10:]:
            symbol = a.get("symbol", "UNKNOWN")
            score = a.get("score", 0.0)
            decision = a.get("decision", "unknown")
            threshold = a.get("threshold", 2.7)
            print(f"  {symbol}: score={score:.2f}, decision={decision}, threshold={threshold:.2f}")
    else:
        print("  ⚠️  NO ATTRIBUTION RECORDS")
    print()
    
    # 5. Check composite gate events
    print("5. COMPOSITE GATE EVENTS (last 20)")
    print("-" * 80)
    composite_gate = load_jsonl("logs/composite_gate.jsonl")
    recent_composite = composite_gate[-20:] if len(composite_gate) > 20 else composite_gate
    print(f"Total composite gate events: {len(composite_gate)}")
    
    accepted = [g for g in recent_composite if g.get("msg") == "accepted"]
    rejected = [g for g in recent_composite if g.get("msg") == "rejected"]
    
    print(f"Recent: {len(accepted)} accepted, {len(rejected)} rejected")
    if rejected:
        print(f"\nRecent rejections:")
        for r in rejected[-10:]:
            symbol = r.get("symbol", "UNKNOWN")
            score = r.get("score", 0.0)
            threshold = r.get("threshold", 2.7)
            reason = r.get("rejection_reason", "unknown")
            print(f"  {symbol}: score={score:.2f} < threshold={threshold:.2f}, reason={reason}")
    print()
    
    # 6. Check orders
    print("6. RECENT ORDERS (last 20)")
    print("-" * 80)
    orders = load_jsonl("logs/orders.jsonl")
    recent_orders = orders[-20:] if len(orders) > 20 else orders
    print(f"Total orders in log: {len(orders)}")
    if recent_orders:
        for o in recent_orders[-10:]:
            symbol = o.get("symbol", "UNKNOWN")
            side = o.get("side", "unknown")
            status = o.get("status", "unknown")
            qty = o.get("qty", 0)
            print(f"  {symbol}: {side} {qty} @ {status}")
    else:
        print("  ⚠️  NO ORDERS FOUND")
    print()
    
    # 7. Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Signals generated: {len(signals)}")
    print(f"Gate events: {len(gate_events)}")
    print(f"Run cycles: {len(run_cycles)}")
    print(f"Attribution records: {len(attribution)}")
    print(f"Orders placed: {len(orders)}")
    
    if recent_runs:
        latest = recent_runs[-1]
        print(f"\nLatest cycle:")
        print(f"  Clusters: {latest.get('clusters', 0)}")
        print(f"  Orders: {latest.get('orders', 0)}")
        print(f"  Composite enabled: {latest.get('metrics', {}).get('composite_enabled', False)}")
    
    if recent_attr:
        latest_scores = [a.get("score", 0.0) for a in recent_attr[-20:]]
        if latest_scores:
            print(f"\nRecent score distribution:")
            print(f"  Min: {min(latest_scores):.2f}")
            print(f"  Max: {max(latest_scores):.2f}")
            print(f"  Avg: {sum(latest_scores)/len(latest_scores):.2f}")
            print(f"  Above 2.7: {len([s for s in latest_scores if s >= 2.7])}/{len(latest_scores)}")
            print(f"  Above 3.5: {len([s for s in latest_scores if s >= 3.5])}/{len(latest_scores)}")

if __name__ == "__main__":
    main()
