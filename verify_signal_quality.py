#!/usr/bin/env python3
"""Verify signal quality and full trading pipeline"""

import json
import sys
from pathlib import Path
sys.path.insert(0, '/root/stock-bot')

print("="*80)
print("COMPREHENSIVE SIGNAL QUALITY & TRADING PIPELINE VERIFICATION")
print("="*80)

results = {
    "signal_generation": {},
    "composite_scoring": {},
    "entry_gates": {},
    "exit_logic": {},
    "issues_found": []
}

# 1. Check signal generation
print("\n[1] SIGNAL GENERATION VERIFICATION")
print("-"*80)

cache = json.load(open("data/uw_flow_cache.json"))
syms = [k for k in cache.keys() if not k.startswith("_")]

results["signal_generation"]["total_symbols"] = len(syms)
results["signal_generation"]["symbols_with_data"] = 0
results["signal_generation"]["symbols_with_conviction"] = 0
results["signal_generation"]["symbols_with_sentiment"] = 0

for sym in syms[:20]:
    data = cache[sym]
    has_data = bool(data)
    has_conviction = data.get("conviction", 0) > 0
    has_sentiment = data.get("sentiment") in ("BULLISH", "BEARISH")
    
    if has_data:
        results["signal_generation"]["symbols_with_data"] += 1
    if has_conviction:
        results["signal_generation"]["symbols_with_conviction"] += 1
    if has_sentiment:
        results["signal_generation"]["symbols_with_sentiment"] += 1

print(f"Total symbols in cache: {results['signal_generation']['total_symbols']}")
print(f"Symbols with data: {results['signal_generation']['symbols_with_data']}")
print(f"Symbols with conviction > 0: {results['signal_generation']['symbols_with_conviction']}")
print(f"Symbols with BULLISH/BEARISH sentiment: {results['signal_generation']['symbols_with_sentiment']}")

# 2. Verify composite scoring accuracy
print("\n[2] COMPOSITE SCORING VERIFICATION")
print("-"*80)

import uw_enrichment_v2 as e
import uw_composite_v2 as c2

test_symbols = syms[:10]
scores_calculated = []
scores_passing = 0
scores_failing = 0

for sym in test_symbols:
    # Enrich with freshness adjustment (like main.py does)
    enriched = e.enrich_signal(sym, cache, "mixed")
    if not enriched:
        continue
        
    original_freshness = enriched.get("freshness", 1.0)
    if original_freshness < 0.5:
        enriched["freshness"] = 0.9
    elif original_freshness < 0.8:
        enriched["freshness"] = 0.95
    
    # Score
    composite = c2.compute_composite_score_v3(sym, enriched, "mixed")
    if not composite:
        continue
        
    score = composite.get("score", 0)
    threshold = c2.get_threshold(sym, "base")
    components = composite.get("components", {})
    
    scores_calculated.append({
        "symbol": sym,
        "score": round(score, 2),
        "threshold": threshold,
        "flow": components.get("flow", 0),
        "dark_pool": components.get("dark_pool", 0),
        "insider": components.get("insider", 0),
        "freshness": enriched.get("freshness", 1.0),
        "passes_gate": score >= threshold
    })
    
    if score >= threshold:
        scores_passing += 1
    else:
        scores_failing += 1

results["composite_scoring"]["total_tested"] = len(scores_calculated)
results["composite_scoring"]["passing_threshold"] = scores_passing
results["composite_scoring"]["failing_threshold"] = scores_failing

print(f"Symbols tested: {len(scores_calculated)}")
print(f"Passing threshold (>= {threshold}): {scores_passing}")
print(f"Failing threshold: {scores_failing}")

if scores_calculated:
    avg_score = sum(s["score"] for s in scores_calculated) / len(scores_calculated)
    max_score = max(s["score"] for s in scores_calculated)
    min_score = min(s["score"] for s in scores_calculated)
    print(f"Score range: {min_score:.2f} - {max_score:.2f}, avg: {avg_score:.2f}")
    
    print("\nSample scores:")
    for s in scores_calculated[:5]:
        print(f"  {s['symbol']}: score={s['score']:.2f}, flow={s['flow']:.2f}, dp={s['dark_pool']:.2f}, passes={s['passes_gate']}")

# 3. Verify component calculations
print("\n[3] COMPONENT CALCULATION VERIFICATION")
print("-"*80)

# Check if flow component is correct
sample = scores_calculated[0] if scores_calculated else None
if sample:
    sym = sample["symbol"]
    enriched = e.enrich_signal(sym, cache, "mixed")
    if enriched.get("freshness", 1.0) < 0.5:
        enriched["freshness"] = 0.9
    
    composite = c2.compute_composite_score_v3(sym, enriched, "mixed")
    if composite:
        comps = composite.get("components", {})
        flow_comp = comps.get("flow", 0)
        conviction = enriched.get("conviction", 0)
        
        # Check flow weight
        from uw_composite_v2 import get_weight
        flow_weight = get_weight("options_flow", "mixed")
        expected_flow = flow_weight * conviction
        
        print(f"Testing {sym}:")
        print(f"  Conviction: {conviction:.3f}")
        print(f"  Flow weight: {flow_weight:.2f}")
        print(f"  Expected flow component: {expected_flow:.2f}")
        print(f"  Actual flow component: {flow_comp:.2f}")
        print(f"  Match: {abs(flow_comp - expected_flow) < 0.1}")
        
        if abs(flow_comp - expected_flow) > 0.1:
            results["issues_found"].append(f"Flow component mismatch for {sym}: expected {expected_flow:.2f}, got {flow_comp:.2f}")

# 4. Check entry gates
print("\n[4] ENTRY GATE VERIFICATION")
print("-"*80)

from v3_2_features import ExpectancyGate, get_system_stage, STAGE_CONFIGS
from main import Config

stage = get_system_stage()
ev_floor = STAGE_CONFIGS[stage]["entry_ev_floor"]
min_exec = Config.MIN_EXEC_SCORE
threshold = c2.ENTRY_THRESHOLDS["base"]

results["entry_gates"]["threshold"] = threshold
results["entry_gates"]["min_exec_score"] = min_exec
results["entry_gates"]["expectancy_floor"] = ev_floor
results["entry_gates"]["stage"] = stage

print(f"Entry Threshold: {threshold}")
print(f"MIN_EXEC_SCORE: {min_exec}")
print(f"Expectancy Floor ({stage}): {ev_floor}")
print(f"Current Stage: {stage}")

# Test expectancy calculation
if scores_calculated:
    sample = scores_calculated[0]
    sym = sample["symbol"]
    score = sample["score"]
    
    expectancy = ExpectancyGate.calculate_expectancy(
        composite_score=score,
        ticker_bayes_expectancy=0.0,
        regime_modifier=1.0,
        tca_modifier=0.0,
        theme_risk_penalty=0.0,
        toxicity_penalty=0.0
    )
    
    print(f"\nSample expectancy calculation for {sym}:")
    print(f"  Score: {score:.2f}")
    print(f"  Expectancy: {expectancy:.4f}")
    print(f"  Expectancy >= Floor: {expectancy >= ev_floor}")
    print(f"  Score >= MIN_EXEC: {score >= min_exec}")
    
    should_enter, reason = ExpectancyGate.should_enter(
        ticker=sym,
        expectancy=expectancy,
        composite_score=score,
        stage=stage,
        regime="mixed",
        tca_modifier=0.0,
        freeze_active=False,
        score_floor_breach=(score < min_exec),
        broker_health_degraded=False
    )
    
    print(f"  ExpectancyGate should_enter: {should_enter} ({reason})")

# 5. Check recent orders and exits
print("\n[5] ORDER & EXIT VERIFICATION")
print("-"*80)

# Check recent orders
orders_file = Path("logs/orders.jsonl")
if orders_file.exists():
    order_lines = orders_file.read_text().strip().split('\n')
    recent_orders = [json.loads(l) for l in order_lines[-20:] if l.strip()]
    results["entry_gates"]["recent_orders"] = len(recent_orders)
    
    if recent_orders:
        print(f"Recent orders: {len(recent_orders)}")
        for o in recent_orders[-5:]:
            print(f"  {o.get('symbol', '?')}: {o.get('side', '?')} {o.get('qty', 0)} @ {o.get('price', 0)}")
    else:
        print("No recent orders found")
        results["issues_found"].append("No orders in logs despite cycles showing orders")

# Check exits
exits_file = Path("logs/exits.jsonl")
if exits_file.exists():
    exit_lines = exits_file.read_text().strip().split('\n')
    recent_exits = [json.loads(l) for l in exit_lines[-10:] if l.strip()]
    results["exit_logic"]["recent_exits"] = len(recent_exits)
    
    if recent_exits:
        print(f"\nRecent exits: {len(recent_exits)}")
        for ex in recent_exits[-5:]:
            print(f"  {ex.get('symbol', '?')}: {ex.get('reason', '?')}")
    else:
        print("No recent exits (may be normal if positions are new)")

# 6. Check position metadata
print("\n[6] POSITION TRACKING VERIFICATION")
print("-"*80)

meta_file = Path("state/position_metadata.json")
if meta_file.exists():
    meta = json.load(open(meta_file))
    results["entry_gates"]["positions_tracked"] = len(meta)
    print(f"Positions in metadata: {len(meta)}")
    
    if meta:
        for sym, data in list(meta.items())[:5]:
            entry_score = data.get("entry_score", 0)
            entry_price = data.get("entry_price", 0)
            qty = data.get("qty", 0)
            print(f"  {sym}: {qty} @ ${entry_price:.2f}, score={entry_score:.2f}")
else:
    print("No position metadata file found")

# Summary
print("\n" + "="*80)
print("VERIFICATION SUMMARY")
print("="*80)

print(f"\nSignal Generation: {'✅ OK' if results['signal_generation']['symbols_with_conviction'] > 0 else '❌ ISSUES'}")
print(f"Composite Scoring: {'✅ OK' if results['composite_scoring']['passing_threshold'] > 0 else '❌ ISSUES'}")
print(f"Entry Gates: Threshold={results['entry_gates'].get('threshold', '?')}, MIN_EXEC={results['entry_gates'].get('min_exec_score', '?')}")

if results["issues_found"]:
    print(f"\n⚠️  ISSUES FOUND: {len(results['issues_found'])}")
    for issue in results["issues_found"]:
        print(f"  - {issue}")
else:
    print("\n✅ No critical issues found")

print("\n" + "="*80)
