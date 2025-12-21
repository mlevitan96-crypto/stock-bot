#!/usr/bin/env python3
"""
Analyze Learning System Effectiveness

Diagnoses why weights aren't updating and provides recommendations.
"""

import json
from pathlib import Path
from adaptive_signal_optimizer import get_optimizer, SIGNAL_COMPONENTS

def analyze_learning_effectiveness():
    """Analyze why learning isn't updating weights"""
    print("=" * 80)
    print("LEARNING SYSTEM EFFECTIVENESS ANALYSIS")
    print("=" * 80)
    print()
    
    optimizer = get_optimizer()
    if not optimizer:
        print("❌ Optimizer not available")
        return
    
    learner = optimizer.learner
    
    print("OVERFITTING SAFEGUARDS:")
    print(f"  MIN_SAMPLES: {learner.MIN_SAMPLES}")
    print(f"  MIN_DAYS_BETWEEN_UPDATES: {learner.MIN_DAYS_BETWEEN_UPDATES}")
    print(f"  Last weight update: {learner.last_weight_update_ts}")
    print()
    
    print("COMPONENT PERFORMANCE:")
    print()
    
    total_samples = 0
    components_with_enough_samples = 0
    components_ready_for_update = []
    
    for component in SIGNAL_COMPONENTS:
        perf = learner.component_performance.get(component, {})
        wins = perf.get("wins", 0)
        losses = perf.get("losses", 0)
        total = wins + losses
        total_samples += total
        
        ewma_wr = perf.get("ewma_win_rate", 0.5)
        ewma_pnl = perf.get("ewma_pnl", 0.0)
        
        has_enough = total >= learner.MIN_SAMPLES
        if has_enough:
            components_with_enough_samples += 1
            components_ready_for_update.append(component)
        
        status = "✓ READY" if has_enough else f"⚠ NEEDS {learner.MIN_SAMPLES - total} MORE"
        
        print(f"  {component:25s}: {total:3d} samples ({wins}W/{losses}L, {ewma_wr:.1%} WR, {ewma_pnl:+.2%} P&L) {status}")
    
    print()
    print("SUMMARY:")
    print(f"  Total samples across all components: {total_samples}")
    print(f"  Components with enough samples ({learner.MIN_SAMPLES}+): {components_with_enough_samples}/{len(SIGNAL_COMPONENTS)}")
    print(f"  Components ready for update: {len(components_ready_for_update)}")
    print()
    
    # Check if update would be blocked
    if learner.last_weight_update_ts:
        from datetime import datetime, timezone
        import time
        now_ts = int(time.time())
        days_since = (now_ts - learner.last_weight_update_ts) / 86400
        if days_since < learner.MIN_DAYS_BETWEEN_UPDATES:
            print(f"⚠ WEIGHT UPDATE BLOCKED: Only {days_since:.1f} days since last update")
            print(f"   Need to wait {learner.MIN_DAYS_BETWEEN_UPDATES - days_since:.1f} more days")
        else:
            print(f"✓ Time check passed: {days_since:.1f} days since last update")
    else:
        print("✓ No previous update (first time)")
    
    print()
    
    # Recommendations
    print("RECOMMENDATIONS:")
    print()
    
    if components_with_enough_samples == 0:
        print("❌ CRITICAL: No components have enough samples for weight updates")
        print("   - Current MIN_SAMPLES: 50")
        print("   - Total samples: {total_samples}")
        print("   - Recommendation: Lower MIN_SAMPLES temporarily OR wait for more trades")
        print()
        print("   Options:")
        print("   1. Lower MIN_SAMPLES to 30 (still statistically sound)")
        print("   2. Lower MIN_SAMPLES to 20 (for faster learning with less data)")
        print("   3. Keep at 50 and wait for more trades (most conservative)")
    elif components_with_enough_samples < len(SIGNAL_COMPONENTS) / 2:
        print("⚠ WARNING: Less than half of components have enough samples")
        print(f"   - {components_with_enough_samples}/{len(SIGNAL_COMPONENTS)} components ready")
        print("   - Recommendation: Consider lowering MIN_SAMPLES OR wait for more trades")
    else:
        print("✓ Good: Most components have enough samples")
        print(f"   - {components_with_enough_samples}/{len(SIGNAL_COMPONENTS)} components ready")
    
    print()
    
    # Check win rate
    if total_samples > 0:
        total_wins = sum(p.get("wins", 0) for p in learner.component_performance.values())
        total_losses = sum(p.get("losses", 0) for p in learner.component_performance.values())
        overall_wr = total_wins / (total_wins + total_losses) if (total_wins + total_losses) > 0 else 0
        
        print("OVERALL PERFORMANCE:")
        print(f"  Total wins: {total_wins}")
        print(f"  Total losses: {total_losses}")
        print(f"  Overall win rate: {overall_wr:.1%}")
        print()
        
        if overall_wr < 0.5:
            print("⚠ WARNING: Win rate below 50%")
            print("   - System is learning from losing trades")
            print("   - This is actually GOOD - it will learn what NOT to do")
            print("   - Weights will adjust to reduce emphasis on losing patterns")
        elif overall_wr < 0.6:
            print("⚠ WARNING: Win rate below 60% target")
            print("   - System needs improvement")
            print("   - Learning will help identify better patterns")
        else:
            print("✓ Win rate above 60% target")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    analyze_learning_effectiveness()
