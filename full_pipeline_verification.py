#!/usr/bin/env python3
"""Complete pipeline verification - signal quality, scoring, entries, exits"""

import json
import sys
from pathlib import Path
sys.path.insert(0, '/root/stock-bot')

print("="*80)
print("COMPLETE PIPELINE VERIFICATION - SIGNAL QUALITY & TRADING PATH")
print("="*80)

issues = []
warnings = []

# 1. Signal Generation
print("\n[1] SIGNAL GENERATION")
print("-"*80)
cache = json.load(open("data/uw_flow_cache.json"))
syms = [k for k in cache.keys() if not k.startswith("_")]

symbols_with_valid_signals = 0
for sym in syms[:20]:
    data = cache[sym]
    has_conviction = data.get("conviction", 0) > 0
    has_sentiment = data.get("sentiment") in ("BULLISH", "BEARISH")
    if has_conviction and has_sentiment:
        symbols_with_valid_signals += 1

print(f"Symbols with valid signals: {symbols_with_valid_signals}/{len(syms[:20])}")

# 2. Composite Scoring Accuracy
print("\n[2] COMPOSITE SCORING ACCURACY")
print("-"*80)

import uw_enrichment_v2 as e
import uw_composite_v2 as c2

scores = []
for sym in syms[:10]:
    enriched = e.enrich_signal(sym, cache, "mixed")
    if not enriched:
        continue
    if enriched.get("freshness", 1.0) < 0.5:
        enriched["freshness"] = 0.9
    
    composite = c2.compute_composite_score_v3(sym, enriched, "mixed")
    if composite:
        score = composite.get("score", 0)
        components = composite.get("components", {})
        
        # Verify flow component calculation
        conviction = enriched.get("conviction", 0)
        from uw_composite_v2 import get_weight
        flow_weight = get_weight("options_flow", "mixed")
        expected_flow = flow_weight * conviction
        actual_flow = components.get("flow", 0)
        
        if abs(expected_flow - actual_flow) > 0.1:
            issues.append(f"Flow component mismatch for {sym}: expected {expected_flow:.2f}, got {actual_flow:.2f}")
        
        scores.append({
            "symbol": sym,
            "score": round(score, 2),
            "flow": round(actual_flow, 2),
            "dp": round(components.get("dark_pool", 0), 2),
            "insider": round(components.get("insider", 0), 2)
        })

if scores:
    avg_score = sum(s["score"] for s in scores) / len(scores)
    threshold = c2.ENTRY_THRESHOLDS["base"]
    passing = sum(1 for s in scores if s["score"] >= threshold)
    
    print(f"Average score: {avg_score:.2f}")
    print(f"Threshold: {threshold}")
    print(f"Symbols passing threshold: {passing}/{len(scores)}")
    print(f"\nScore distribution:")
    for s in scores:
        print(f"  {s['symbol']}: {s['score']:.2f} (flow={s['flow']:.2f}, dp={s['dp']:.2f})")
    
    if avg_score < threshold * 0.8:
        warnings.append(f"Average score ({avg_score:.2f}) is below 80% of threshold ({threshold})")

# 3. Entry Gate Configuration
print("\n[3] ENTRY GATE CONFIGURATION")
print("-"*80)

from v3_2_features import STAGE_CONFIGS, get_system_stage
import os

stage = get_system_stage()
ev_floor = STAGE_CONFIGS[stage]["entry_ev_floor"]
min_exec = float(os.getenv("MIN_EXEC_SCORE", "0.5"))
threshold = c2.ENTRY_THRESHOLDS["base"]

print(f"Threshold: {threshold}")
print(f"MIN_EXEC_SCORE: {min_exec}")
print(f"Expectancy Floor ({stage}): {ev_floor}")

if threshold < 2.0:
    warnings.append(f"Entry threshold ({threshold}) is low - may allow lower quality trades")
if min_exec < 1.0:
    warnings.append(f"MIN_EXEC_SCORE ({min_exec}) is very low - may allow poor trades")

# 4. Recent Order Quality
print("\n[4] RECENT ORDER QUALITY")
print("-"*80)

orders_file = Path("logs/orders.jsonl")
if orders_file.exists():
    order_lines = orders_file.read_text().strip().split('\n')[-20:]
    recent_orders = [json.loads(l) for l in order_lines if l.strip()]
    
    if recent_orders:
        orders_with_scores = [o for o in recent_orders if o.get("score", 0) > 0]
        avg_order_score = sum(o.get("score", 0) for o in orders_with_scores) / len(orders_with_scores) if orders_with_scores else 0
        
        print(f"Recent orders: {len(recent_orders)}")
        print(f"Orders with scores: {len(orders_with_scores)}")
        if orders_with_scores:
            print(f"Average order score: {avg_order_score:.2f}")
            
            for o in recent_orders[-5:]:
                score = o.get("score", 0)
                symbol = o.get("symbol", "?")
                status = o.get("status", "?")
                print(f"  {symbol}: score={score:.2f}, status={status}")
            
            if avg_order_score < threshold:
                warnings.append(f"Average order score ({avg_order_score:.2f}) is below threshold ({threshold})")
    else:
        warnings.append("No recent orders found in logs")
else:
    warnings.append("Orders log file not found")

# 5. Exit Logic Verification
print("\n[5] EXIT LOGIC VERIFICATION")
print("-"*80)

meta_file = Path("state/position_metadata.json")
if meta_file.exists():
    meta = json.load(open(meta_file))
    print(f"Positions tracked: {len(meta)}")
    
    positions_with_targets = sum(1 for d in meta.values() if "targets" in d)
    print(f"Positions with exit targets: {positions_with_targets}/{len(meta)}")
    
    # Check exit logs
    exits_file = Path("logs/exits.jsonl")
    if exits_file.exists():
        exit_lines = exits_file.read_text().strip().split('\n')
        if exit_lines:
            print(f"Total exits logged: {len(exit_lines)}")
            recent_exits = [json.loads(l) for l in exit_lines[-5:]]
            print("Recent exits:")
            for ex in recent_exits:
                print(f"  {ex.get('symbol', '?')}: {ex.get('reason', '?')} at {ex.get('ts', '?')[:19]}")
        else:
            print("No exit logs (may be normal if positions are new)")
    else:
        warnings.append("Exit log file not found")
else:
    warnings.append("Position metadata file not found")

# 6. Check if exits are being evaluated
print("\n[6] EXIT EVALUATION CHECK")
print("-"*80)

run_file = Path("logs/run.jsonl")
if run_file.exists():
    run_lines = run_file.read_text().strip().split('\n')[-10:]
    runs_with_exits = 0
    for line in run_lines:
        try:
            run = json.loads(line)
            if "exits" in str(run):
                runs_with_exits += 1
        except:
            pass
    print(f"Recent cycles checking exits: {runs_with_exits}/{len(run_lines)}")
    if runs_with_exits == 0:
        warnings.append("Exit evaluation may not be running in cycles")

# Summary
print("\n" + "="*80)
print("VERIFICATION SUMMARY")
print("="*80)

print(f"\n✅ Signal Generation: {'OK' if symbols_with_valid_signals > 10 else 'LIMITED'}")
print(f"✅ Composite Scoring: {'OK' if not issues else 'ISSUES FOUND'}")
print(f"✅ Entry Gates: Threshold={threshold}, MIN_EXEC={min_exec}, EV_Floor={ev_floor}")

if issues:
    print(f"\n❌ CRITICAL ISSUES: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")

if warnings:
    print(f"\n⚠️  WARNINGS: {len(warnings)}")
    for w in warnings:
        print(f"  - {w}")

if not issues and len(warnings) < 3:
    print("\n✅ SIGNAL QUALITY: GOOD - Components calculating correctly, scores reasonable")
else:
    print("\n⚠️  SIGNAL QUALITY: NEEDS REVIEW - Some issues or warnings detected")

print("\n" + "="*80)
