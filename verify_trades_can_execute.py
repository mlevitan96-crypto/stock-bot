#!/usr/bin/env python3
"""COMPREHENSIVE TEST: Verify trades can actually execute"""

import json
import sys
from pathlib import Path
sys.path.insert(0, '/root/stock-bot')

print("=" * 80)
print("COMPREHENSIVE TRADING PIPELINE TEST")
print("=" * 80)

results = {
    "all_passed": True,
    "tests": []
}

def test(name, condition, details=""):
    passed = bool(condition)
    results["all_passed"] = results["all_passed"] and passed
    status = "✅ PASS" if passed else "❌ FAIL"
    results["tests"].append({"test": name, "passed": passed, "details": details})
    print(f"{status}: {name}")
    if details:
        print(f"     {details}")
    return passed

# 1. Check cache has symbols
print("\n[1] Checking cache...")
cache_file = Path("data/uw_flow_cache.json")
if cache_file.exists():
    cache = json.load(open(cache_file))
    syms = [k for k in cache.keys() if not k.startswith("_")]
    test("Cache has symbols", len(syms) > 0, f"Found {len(syms)} symbols")
    
    if syms:
        symbol = syms[0]
        data = cache[symbol]
        test("Symbol has sentiment", "sentiment" in data and data.get("sentiment"), f"{symbol}: {data.get('sentiment')}")
        test("Symbol has conviction", "conviction" in data and data.get("conviction", 0) > 0, f"{symbol}: {data.get('conviction')}")
else:
    test("Cache file exists", False, "Cache file missing!")

# 2. Test enrichment
print("\n[2] Testing enrichment...")
if syms:
    import uw_enrichment_v2 as uw_enrich
    enriched = uw_enrich.enrich_signal(symbol, cache, "mixed")
    test("Enrichment works", bool(enriched), f"Enriched {symbol}")
    test("Enriched has sentiment", enriched.get("sentiment"), f"Sentiment: {enriched.get('sentiment')}")
    test("Enriched has conviction", enriched.get("conviction", 0) > 0, f"Conviction: {enriched.get('conviction')}")
    
    # Check freshness adjustment
    original_freshness = enriched.get("freshness", 1.0)
    if original_freshness < 0.5:
        enriched["freshness"] = 0.9
    elif original_freshness < 0.8:
        enriched["freshness"] = 0.95
    
    final_freshness = enriched.get("freshness", 1.0)
    test("Freshness >= 0.9 after adjustment", final_freshness >= 0.9, f"Freshness: {final_freshness:.2f}")

# 3. Test composite scoring
print("\n[3] Testing composite scoring...")
if syms and enriched:
    import uw_composite_v2 as uw_v2
    
    # Check thresholds
    threshold = uw_v2.get_threshold(symbol, "base")
    test("Threshold is 1.5", threshold == 1.5, f"Threshold: {threshold}")
    
    composite = uw_v2.compute_composite_score_v3(symbol, enriched, "mixed")
    test("Composite scoring works", bool(composite), f"Got composite for {symbol}")
    
    if composite:
        score = composite.get("score", 0.0)
        components = composite.get("components", {})
        flow_comp = components.get("flow", 0)
        
        test("Score is calculated", score > 0, f"Score: {score:.2f}")
        test("Flow component > 0", flow_comp > 0, f"Flow: {flow_comp:.2f}")
        
        # Test gate
        gate_result = uw_v2.should_enter_v2(composite, symbol, "base")
        test("Gate would pass (score >= threshold)", score >= threshold, 
             f"Score {score:.2f} >= Threshold {threshold:.2f} = {score >= threshold}")
        
        toxicity = composite.get("toxicity", 0.0)
        freshness_gate = composite.get("freshness", 1.0)
        test("Toxicity OK (<= 0.90)", toxicity <= 0.90, f"Toxicity: {toxicity:.2f}")
        test("Freshness OK (>= 0.25)", freshness_gate >= 0.25, f"Freshness: {freshness_gate:.2f}")
        
        gate_actual = gate_result
        test("should_enter_v2 returns True", gate_actual, 
             f"Gate result: {gate_actual}, score={score:.2f}, threshold={threshold:.2f}")

# 4. Test expectancy gate
print("\n[4] Testing expectancy gate...")
if syms and composite:
    from v3_2_features import ExpectancyGate, get_system_stage, STAGE_CONFIGS
    
    stage = get_system_stage()
    test("System stage loaded", bool(stage), f"Stage: {stage}")
    
    stage_config = STAGE_CONFIGS.get(stage, STAGE_CONFIGS["bootstrap"])
    ev_floor = stage_config["entry_ev_floor"]
    test("Expectancy floor is -0.30", ev_floor == -0.30, f"EV floor: {ev_floor}")
    
    # Calculate expectancy
    expectancy = ExpectancyGate.calculate_expectancy(
        composite_score=score,
        ticker_bayes_expectancy=0.0,  # Use 0 as default
        regime_modifier=1.0,
        tca_modifier=0.0,
        theme_risk_penalty=0.0,
        toxicity_penalty=0.0
    )
    
    test(f"Expectancy calculated", expectancy is not None, f"Expectancy: {expectancy:.4f}")
    test(f"Expectancy >= floor ({ev_floor})", expectancy >= ev_floor, 
         f"Expectancy {expectancy:.4f} >= Floor {ev_floor}")
    
    should_enter, reason = ExpectancyGate.should_enter(
        ticker=symbol,
        expectancy=expectancy,
        composite_score=score,
        stage=stage,
        regime="mixed",
        tca_modifier=0.0,
        freeze_active=False,
        score_floor_breach=(score < 1.5),  # MIN_EXEC_SCORE
        broker_health_degraded=False
    )
    
    test("ExpectancyGate should_enter", should_enter, 
         f"Should enter: {should_enter}, reason: {reason}, expectancy: {expectancy:.4f}")

# 5. Test MIN_EXEC_SCORE
print("\n[5] Testing MIN_EXEC_SCORE...")
if syms and composite:
    from main import Config
    min_exec = Config.MIN_EXEC_SCORE
    test("MIN_EXEC_SCORE is 1.5", min_exec == 1.5, f"MIN_EXEC_SCORE: {min_exec}")
    test("Score >= MIN_EXEC_SCORE", score >= min_exec, 
         f"Score {score:.2f} >= MIN_EXEC {min_exec}")

# 6. Simulate full pipeline
print("\n[6] Simulating full pipeline...")
if syms:
    clusters_created = []
    for test_sym in syms[:5]:  # Test first 5 symbols
        try:
            enriched_test = uw_enrich.enrich_signal(test_sym, cache, "mixed")
            if not enriched_test:
                continue
                
            # Apply freshness adjustment (like main.py does)
            current_freshness = enriched_test.get("freshness", 1.0)
            if current_freshness < 0.5:
                enriched_test["freshness"] = 0.9
            elif current_freshness < 0.8:
                enriched_test["freshness"] = 0.95
            
            composite_test = uw_v2.compute_composite_score_v3(test_sym, enriched_test, "mixed")
            if not composite_test:
                continue
                
            score_test = composite_test.get("score", 0.0)
            threshold_test = uw_v2.get_threshold(test_sym, "base")
            
            if uw_v2.should_enter_v2(composite_test, test_sym, "base"):
                clusters_created.append({"symbol": test_sym, "score": score_test})
        except Exception as e:
            pass
    
    test("Pipeline creates clusters", len(clusters_created) > 0, 
         f"Created {len(clusters_created)} clusters from {min(5, len(syms))} symbols tested")
    if clusters_created:
        for c in clusters_created[:3]:
            print(f"     {c['symbol']}: score={c['score']:.2f}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

passed = sum(1 for t in results["tests"] if t["passed"])
total = len(results["tests"])
print(f"Tests Passed: {passed}/{total}")

if results["all_passed"]:
    print("\n✅ ALL TESTS PASSED - Trades SHOULD execute")
    print("\nExpected behavior when market opens:")
    print("  - Clusters will be created")
    print("  - Clusters will pass all gates")
    print("  - Orders should be submitted")
else:
    print("\n❌ SOME TESTS FAILED - Issues remain")
    print("\nFailed tests:")
    for t in results["tests"]:
        if not t["passed"]:
            print(f"  - {t['test']}: {t.get('details', '')}")

print("\n" + "=" * 80)
