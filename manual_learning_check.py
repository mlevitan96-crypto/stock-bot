#!/usr/bin/env python3
"""Manual learning system check"""
from adaptive_signal_optimizer import get_optimizer

opt = get_optimizer()
if not opt:
    print("ERROR: Optimizer not available")
    exit(1)

print("Learning System Report:")
print("=" * 60)
report = opt.get_report()

print(f"Total learning samples: {report['learning_samples']}")
print(f"Has learned weights: {opt.has_learned_weights()}")
print()

print("Component Performance:")
print("-" * 60)
comp_perf = report.get('component_performance', {})
for comp, perf in sorted(comp_perf.items()):
    samples = perf.get('samples', 0)
    if samples > 0:
        mult = perf.get('multiplier', 1.0)
        wins = perf.get('wins', 0)
        losses = perf.get('losses', 0)
        wr = wins / (wins + losses) if (wins + losses) > 0 else 0
        print(f"{comp:25s} samples={samples:3d} wins={wins:2d} losses={losses:2d} wr={wr:.2f} mult={mult:.2f}")

print()
print("Multipliers (non-default):")
print("-" * 60)
mults = opt.get_multipliers_only()
non_default = {k: v for k, v in mults.items() if v != 1.0}
if non_default:
    for comp, mult in sorted(non_default.items(), key=lambda x: abs(x[1] - 1.0), reverse=True):
        print(f"{comp:25s} multiplier={mult:.2f}")
else:
    print("All multipliers at default (1.0) - learning hasn't adjusted yet")
