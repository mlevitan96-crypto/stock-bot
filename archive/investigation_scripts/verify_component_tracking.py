#!/usr/bin/env python3
"""
Verify Component Tracking - Ensure ALL components are being tracked

Checks if all 21 signal components are included in learning,
even if they have 0 value in some trades.
"""

import json
from pathlib import Path
from adaptive_signal_optimizer import get_optimizer, SIGNAL_COMPONENTS
from comprehensive_learning_orchestrator_v2 import load_learning_state

def verify_component_tracking():
    """Verify all components are being tracked"""
    print("=" * 80)
    print("COMPONENT TRACKING VERIFICATION")
    print("=" * 80)
    print()
    
    optimizer = get_optimizer()
    if not optimizer:
        print("❌ Optimizer not available")
        return
    
    learner = optimizer.learner
    
    print("SIGNAL COMPONENTS (21 total):")
    print()
    
    components_tracked = 0
    components_with_samples = 0
    components_missing = []
    
    for component in SIGNAL_COMPONENTS:
        perf = learner.component_performance.get(component, {})
        wins = perf.get("wins", 0)
        losses = perf.get("losses", 0)
        total = wins + losses
        
        if component in learner.component_performance:
            components_tracked += 1
            if total > 0:
                components_with_samples += 1
                status = f"✓ {total} samples"
            else:
                status = "⚠ Tracked but 0 samples"
        else:
            components_missing.append(component)
            status = "❌ NOT TRACKED"
        
        print(f"  {component:25s}: {status}")
    
    print()
    print("SUMMARY:")
    print(f"  Components in tracking system: {components_tracked}/{len(SIGNAL_COMPONENTS)}")
    print(f"  Components with samples: {components_with_samples}/{len(SIGNAL_COMPONENTS)}")
    print(f"  Components missing from tracking: {len(components_missing)}")
    
    if components_missing:
        print()
        print("⚠ WARNING: Missing components:")
        for comp in components_missing:
            print(f"    - {comp}")
        print()
        print("These components are NOT being tracked for learning!")
        print("They need to be included in the feature_vector when trades are recorded.")
    else:
        print()
        print("✓ All components are in the tracking system")
    
    print()
    
    # Check a sample trade to see what components are being passed
    print("CHECKING SAMPLE TRADES:")
    print()
    
    attr_log = Path("logs/attribution.jsonl")
    if attr_log.exists():
        sample_trades = []
        with open(attr_log, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 5:  # Check first 5 trades
                    break
                if line.strip():
                    try:
                        rec = json.loads(line)
                        if rec.get("type") == "attribution":
                            ctx = rec.get("context", {})
                            comps = ctx.get("components", {}) or rec.get("components", {})
                            if comps:
                                sample_trades.append({
                                    "symbol": rec.get("symbol"),
                                    "components": list(comps.keys()),
                                    "component_count": len(comps)
                                })
                    except:
                        pass
        
        if sample_trades:
            print("Sample trades and their components:")
            for trade in sample_trades[:3]:
                print(f"  {trade['symbol']}: {trade['component_count']} components")
                print(f"    Components: {', '.join(trade['components'][:10])}")
                if len(trade['components']) > 10:
                    print(f"    ... and {len(trade['components']) - 10} more")
                print()
            
            # Check if all SIGNAL_COMPONENTS appear in any trade
            all_components_found = set()
            for trade in sample_trades:
                all_components_found.update(trade['components'])
            
            missing_in_trades = set(SIGNAL_COMPONENTS) - all_components_found
            if missing_in_trades:
                print(f"⚠ Components never seen in trades ({len(missing_in_trades)}):")
                for comp in sorted(missing_in_trades):
                    print(f"    - {comp}")
                print()
                print("These components are defined but never appear in trade data.")
                print("They may need to be included even when value is 0.")
            else:
                print("✓ All components appear in at least one trade")
        else:
            print("⚠ No trades with components found in sample")
    else:
        print("⚠ attribution.jsonl not found")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    verify_component_tracking()
