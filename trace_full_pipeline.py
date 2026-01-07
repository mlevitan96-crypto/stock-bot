#!/usr/bin/env python3
"""Trace the FULL pipeline to find ALL blockers"""

import json
import sys
sys.path.insert(0, '/root/stock-bot')

print("="*80)
print("TRACING FULL PIPELINE - FINDING ALL BLOCKERS")
print("="*80)

# 1. Load cache and test multiple symbols
cache = json.load(open("data/uw_flow_cache.json"))
syms = [k for k in cache.keys() if not k.startswith("_")][:10]

import uw_enrichment_v2 as e
import uw_composite_v2 as c2
from v3_2_features import STAGE_CONFIGS, ExpectancyGate, get_system_stage

# Get MIN_EXEC_SCORE without importing main
MIN_EXEC_SCORE = 1.5  # Default from Config - check if overridden
try:
    import os
    MIN_EXEC_SCORE = float(os.getenv("MIN_EXEC_SCORE", "1.5"))
except:
    pass

print(f"\nTesting {len(syms)} symbols...")
print(f"Threshold: {c2.ENTRY_THRESHOLDS['base']}")
print(f"MIN_EXEC_SCORE: {MIN_EXEC_SCORE}")
print(f"Expectancy Floor: {STAGE_CONFIGS['bootstrap']['entry_ev_floor']}")

clusters_passing = []
clusters_blocked = []

for sym in syms:
    try:
        # Enrich
        en = e.enrich_signal(sym, cache, "mixed")
        if not en:
            continue
            
        # Apply freshness adjustment (CRITICAL)
        orig_fresh = en.get("freshness", 1.0)
        if orig_fresh < 0.5:
            en["freshness"] = 0.9
        elif orig_fresh < 0.8:
            en["freshness"] = 0.95
        
        # Score
        comp = c2.compute_composite_score_v3(sym, en, "mixed")
        if not comp:
            continue
            
        score = comp.get("score", 0)
        threshold = c2.get_threshold(sym, "base")
        
        # Test all gates
        gate1_result = c2.should_enter_v2(comp, sym, "base")
        
        # Calculate expectancy
        expectancy = ExpectancyGate.calculate_expectancy(
            composite_score=score,
            ticker_bayes_expectancy=0.0,
            regime_modifier=1.0,
            tca_modifier=0.0,
            theme_risk_penalty=0.0,
            toxicity_penalty=0.0
        )
        
        stage = get_system_stage()
        ev_floor = STAGE_CONFIGS[stage]["entry_ev_floor"]
        
        # Check expectancy gate
        gate2_result, gate2_reason = ExpectancyGate.should_enter(
            ticker=sym,
            expectancy=expectancy,
            composite_score=score,
            stage=stage,
            regime="mixed",
            tca_modifier=0.0,
            freeze_active=False,
            score_floor_breach=(score < MIN_EXEC_SCORE),
            broker_health_degraded=False
        )
        
        # Check MIN_EXEC_SCORE
        gate3_result = score >= Config.MIN_EXEC_SCORE
        
        all_gates = gate1_result and gate2_result and gate3_result
        
        result = {
            "symbol": sym,
            "score": round(score, 2),
            "threshold": threshold,
            "expectancy": round(expectancy, 4),
            "ev_floor": ev_floor,
            "min_exec": MIN_EXEC_SCORE,
            "gate1_should_enter": gate1_result,
            "gate2_expectancy": gate2_result,
            "gate3_min_exec": gate3_result,
            "all_pass": all_gates,
            "blockers": []
        }
        
        if not gate1_result:
            result["blockers"].append("should_enter_v2 failed")
            result["toxicity"] = comp.get("toxicity", 0)
            result["freshness"] = comp.get("freshness", 1.0)
        if not gate2_result:
            result["blockers"].append(f"expectancy gate: {gate2_reason}")
        if not gate3_result:
            result["blockers"].append(f"MIN_EXEC_SCORE: {score} < {MIN_EXEC_SCORE}")
        
        if all_gates:
            clusters_passing.append(result)
        else:
            clusters_blocked.append(result)
            
    except Exception as ex:
        print(f"Error testing {sym}: {ex}")
        continue

print("\n" + "="*80)
print(f"RESULTS: {len(clusters_passing)} PASSING, {len(clusters_blocked)} BLOCKED")
print("="*80)

if clusters_passing:
    print("\n✅ SYMBOLS PASSING ALL GATES:")
    for r in clusters_passing[:5]:
        print(f"  {r['symbol']}: score={r['score']}, expectancy={r['expectancy']}")
else:
    print("\n❌ NO SYMBOLS PASSING ALL GATES")
    print("\nBLOCKER ANALYSIS:")
    
    # Group by blocker type
    blocker_counts = {}
    for r in clusters_blocked:
        for b in r["blockers"]:
            blocker_counts[b] = blocker_counts.get(b, 0) + 1
    
    print("\nBlockers by frequency:")
    for blocker, count in sorted(blocker_counts.items(), key=lambda x: -x[1]):
        print(f"  {blocker}: {count} symbols")
    
    print("\nSample blocked symbols:")
    for r in clusters_blocked[:5]:
        print(f"\n  {r['symbol']}:")
        print(f"    Score: {r['score']} (threshold: {r['threshold']}, MIN_EXEC: {r['min_exec']})")
        print(f"    Expectancy: {r['expectancy']} (floor: {r['ev_floor']})")
        print(f"    Blockers: {', '.join(r['blockers'])}")
        if 'toxicity' in r:
            print(f"    Toxicity: {r['toxicity']}, Freshness: {r['freshness']}")

print("\n" + "="*80)
