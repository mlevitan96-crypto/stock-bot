#!/usr/bin/env python3
import json
import sys
sys.path.insert(0, '/root/stock-bot')

print("="*80)
print("VERIFYING ALL FIXES")
print("="*80)

# Load cache
cache = json.load(open("data/uw_flow_cache.json"))
syms = [k for k in cache.keys() if not k.startswith("_")][:1]
s = syms[0]

# Test with freshness adjustment
import uw_enrichment_v2 as e
import uw_composite_v2 as c2
from v3_2_features import STAGE_CONFIGS
from main import Config

en = e.enrich_signal(s, cache, "mixed")
if en.get("freshness", 1) < 0.5:
    en["freshness"] = 0.9

comp = c2.compute_composite_score_v3(s, en, "mixed")
score = comp.get("score", 0)
thresh = c2.get_threshold(s, "base")
ev_floor = STAGE_CONFIGS["bootstrap"]["entry_ev_floor"]
min_exec = Config.MIN_EXEC_SCORE

print(f"Symbol: {s}")
print(f"Score: {score:.2f}")
print(f"Threshold: {thresh}")
print(f"MIN_EXEC_SCORE: {min_exec}")
print(f"Expectancy Floor: {ev_floor}")
print(f"Score >= Threshold: {score >= thresh}")
print(f"Score >= MIN_EXEC: {score >= min_exec}")

gate_result = c2.should_enter_v2(comp, s, "base")
print(f"should_enter_v2: {gate_result}")

print("="*80)
