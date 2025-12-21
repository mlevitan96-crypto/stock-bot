#!/usr/bin/env python3
"""Quick learning status check - copy/paste ready"""
import json
from pathlib import Path

print("=" * 60)
print("LEARNING SYSTEM STATUS CHECK")
print("=" * 60)
print()

# Check if optimizer is available
try:
    from adaptive_signal_optimizer import get_optimizer
    opt = get_optimizer()
    if opt:
        print("[OK] Adaptive optimizer initialized")
        
        report = opt.get_report()
        print(f"Learning samples: {report['learning_samples']}")
        print(f"Has learned weights: {opt.has_learned_weights()}")
        
        # Check component performance
        comp_perf = report.get('component_performance', {})
        components_with_samples = sum(1 for c in comp_perf.values() if c.get('samples', 0) > 0)
        print(f"Components with samples: {components_with_samples}")
        
        # Show top components
        if components_with_samples > 0:
            print("\nTop components by samples:")
            sorted_comps = sorted(comp_perf.items(), key=lambda x: x[1].get('samples', 0), reverse=True)
            for comp, perf in sorted_comps[:5]:
                samples = perf.get('samples', 0)
                if samples > 0:
                    mult = perf.get('multiplier', 1.0)
                    print(f"  {comp}: {samples} samples, multiplier={mult:.2f}")
    else:
        print("[ERROR] Optimizer not initialized")
except ImportError as e:
    print(f"[ERROR] Cannot import optimizer: {e}")
except Exception as e:
    print(f"[ERROR] Error checking optimizer: {e}")

print()

# Check logs
print("=" * 60)
print("LOG FILES CHECK")
print("=" * 60)
print()

attr_log = Path("logs/attribution.jsonl")
if attr_log.exists():
    with open(attr_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        print(f"[OK] Attribution log exists: {len(lines)} trades")
        if lines:
            try:
                last = json.loads(lines[-1])
                print(f"  Last trade: {last.get('symbol')} P&L: {last.get('pnl_pct', 0)}%")
            except:
                pass
else:
    print("[WARNING] No attribution log found (logs/attribution.jsonl)")

uw_attr_log = Path("data/uw_attribution.jsonl")
if uw_attr_log.exists():
    with open(uw_attr_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        print(f"[OK] UW attribution log exists: {len(lines)} records")
else:
    print("[INFO] No UW attribution log (data/uw_attribution.jsonl)")

print()

# Check learning state
print("=" * 60)
print("LEARNING STATE CHECK")
print("=" * 60)
print()

weights_file = Path("state/signal_weights.json")
if weights_file.exists():
    with open(weights_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
        learner = state.get("learner", {})
        history_count = learner.get("learning_history_count", 0)
        print(f"[OK] Learning state file exists")
        print(f"  Learning history: {history_count} trades")
        
        # Check component samples
        entry_weights = state.get("entry_weights", {})
        bands = entry_weights.get("weight_bands", {})
        components_with_data = sum(1 for b in bands.values() if isinstance(b, dict) and b.get("sample_count", 0) > 0)
        print(f"  Components with data: {components_with_data}")
        
        if components_with_data > 0:
            print("\n  Components with samples:")
            for comp, band in bands.items():
                if isinstance(band, dict):
                    samples = band.get("sample_count", 0)
                    if samples > 0:
                        mult = band.get("current", 1.0)
                        wins = band.get("wins", 0)
                        losses = band.get("losses", 0)
                        print(f"    {comp}: {samples} samples ({wins}W/{losses}L), mult={mult:.2f}")
else:
    print("[WARNING] No learning state file (state/signal_weights.json)")
    print("  Learning system hasn't processed any trades yet")

print()

# Check learning log
learning_log = Path("data/weight_learning.jsonl")
if learning_log.exists():
    with open(learning_log, 'r', encoding='utf-8') as f:
        lines = [l for l in f if l.strip()]
        print(f"[OK] Learning updates log: {len(lines)} updates")
        if lines:
            try:
                last_update = json.loads(lines[-1])
                adjustments = last_update.get("adjustments", [])
                print(f"  Last update: {len(adjustments)} components adjusted")
            except:
                pass
else:
    print("[INFO] No learning updates log yet (data/weight_learning.jsonl)")

print()
print("=" * 60)
print("SUMMARY")
print("=" * 60)
