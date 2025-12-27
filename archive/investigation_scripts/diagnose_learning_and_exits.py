#!/usr/bin/env python3
"""
Diagnostic Script: Learning System & Exit Logic Verification

Checks:
1. Are weights being updated by learning system?
2. Are updated weights being applied to scoring?
3. Are exit stops and profit targets working?
"""

import json
from pathlib import Path

STATE_DIR = Path("state")
DATA_DIR = Path("data")
LOGS_DIR = Path("logs")

print("="*80)
print("LEARNING SYSTEM & EXIT LOGIC DIAGNOSTIC")
print("="*80)

# 1. Check if learning system has updated weights
print("\n1. LEARNING SYSTEM WEIGHT UPDATES")
print("-" * 80)

try:
    from adaptive_signal_optimizer import get_optimizer, SIGNAL_COMPONENTS
    
    optimizer = get_optimizer()
    if optimizer:
        has_learned = optimizer.has_learned_weights()
        print(f"OK: Optimizer loaded: has_learned_weights={has_learned}")
        
        # Get current weights
        effective_weights = optimizer.get_weights_for_composite()
        multipliers = optimizer.get_multipliers_only()
        
        if effective_weights:
            # Check which weights differ from defaults
            from uw_composite_v2 import WEIGHTS_V3
            
            adjusted = []
            for component in SIGNAL_COMPONENTS[:10]:  # Check first 10
                default = WEIGHTS_V3.get(component, 0.0)
                effective = effective_weights.get(component, default)
                mult = multipliers.get(component, 1.0) if multipliers else 1.0
                
                if mult != 1.0:
                    adjusted.append({
                        "component": component,
                        "default": default,
                        "effective": effective,
                        "multiplier": mult
                    })
            
            if adjusted:
                print(f"OK: Found {len(adjusted)} adjusted weights:")
                for adj in adjusted[:5]:
                    print(f"  - {adj['component']}: {adj['default']:.2f} -> {adj['effective']:.2f} (x{adj['multiplier']:.2f})")
            else:
                print("WARNING: No weights adjusted yet (all at 1.0x multiplier)")
                print("  This is normal if:")
                print("    - Not enough trades (< 30 per component)")
                print("    - Learning hasn't run daily batch yet")
                print("    - Less than 1 day since last update")
        else:
            print("⚠ No effective weights returned")
    else:
        print("FAIL: Optimizer not initialized")
except Exception as e:
    print(f"FAIL: Error checking optimizer: {e}")

# 2. Check if weights are being applied in composite scoring
print("\n2. WEIGHT APPLICATION IN SCORING")
print("-" * 80)

try:
    from uw_composite_v2 import get_adaptive_weights, WEIGHTS_V3, compute_composite_score_v3
    
    adaptive = get_adaptive_weights()
    if adaptive:
        print(f"OK: Adaptive weights loaded: {len(adaptive)} components")
        
        # Check if any differ from defaults
        different = False
        for comp in list(adaptive.keys())[:5]:
            default = WEIGHTS_V3.get(comp, 0.0)
            learned = adaptive.get(comp, default)
            if learned != default:
                different = True
                print(f"  - {comp}: default={default:.2f}, learned={learned:.2f}")
        
        if not different:
            print("WARNING: All weights match defaults (learning may not have updated yet)")
        
        # Test scoring
        test_data = {
            "sentiment": "BULLISH",
            "conviction": 0.75,
            "dark_pool": {"sentiment": "BULLISH", "total_premium": 2000000},
            "insider": {"sentiment": "BULLISH", "net_buys": 10}
        }
        result = compute_composite_score_v3("TEST", test_data, "NEUTRAL", use_adaptive_weights=True)
        if result:
            print(f"OK: Composite scoring works: score={result.get('score', 0):.2f}")
            print(f"  Adaptive weights active: {result.get('adaptive_weights_active', False)}")
    else:
        print("WARNING: No adaptive weights available (using defaults)")
        print("  This means learning system hasn't produced weights yet")
except Exception as e:
    print(f"FAIL: Error checking weight application: {e}")

# 3. Check exit logic
print("\n3. EXIT LOGIC VERIFICATION")
print("-" * 80)

try:
    from main import Config
    
    print(f"OK: Exit parameters configured:")
    print(f"  - Trailing stop: {Config.TRAILING_STOP_PCT*100:.1f}%")
    print(f"  - Time exit: {Config.TIME_EXIT_MINUTES} minutes ({Config.TIME_EXIT_MINUTES/60:.1f} hours)")
    print(f"  - Profit targets: {Config.PROFIT_TARGETS}")
    print(f"  - Scale-out fractions: {Config.SCALE_OUT_FRACTIONS}")
except Exception as e:
    print(f"FAIL: Error loading exit config: {e}")

# 4. Check recent exits
print("\n4. RECENT EXIT ANALYSIS")
print("-" * 80)

exit_file = LOGS_DIR / "exit.jsonl"
if exit_file.exists():
    try:
        from datetime import datetime, timezone, timedelta
        
        recent_exits = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        
        with exit_file.open("r") as f:
            for line in f.readlines()[-50:]:
                try:
                    exit_event = json.loads(line.strip())
                    ts_str = exit_event.get("ts", "")
                    if ts_str:
                        if isinstance(ts_str, (int, float)):
                            exit_time = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                        else:
                            exit_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            if exit_time.tzinfo is None:
                                exit_time = exit_time.replace(tzinfo=timezone.utc)
                        
                        if exit_time >= cutoff:
                            recent_exits.append(exit_event)
                except:
                    continue
        
        if recent_exits:
            reasons = {}
            for e in recent_exits:
                reason = e.get("reason", "unknown")
                reasons[reason] = reasons.get(reason, 0) + 1
            
            print(f"OK: Found {len(recent_exits)} recent exits")
            print(f"  Exit reasons:")
            for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"    - {reason}: {count}")
            
            # Check for profit targets and stops
            has_profit = any("profit" in str(r).lower() for r in reasons.keys())
            has_stop = any("stop" in str(r).lower() or "trail" in str(r).lower() for r in reasons.keys())
            has_time = any("time" in str(r).lower() for r in reasons.keys())
            
            print(f"\n  Exit mechanisms triggered:")
            print(f"    - Profit targets: {'OK' if has_profit else 'NOT FOUND'}")
            print(f"    - Trailing stops: {'OK' if has_stop else 'NOT FOUND'}")
            print(f"    - Time exits: {'OK' if has_time else 'NOT FOUND'}")
        else:
            print("WARNING: No recent exits found (last 7 days)")
    except Exception as e:
        print(f"FAIL: Error analyzing exits: {e}")
else:
    print("WARNING: Exit log file not found")

# 5. Check learning state
print("\n5. LEARNING SYSTEM STATE")
print("-" * 80)

try:
    from comprehensive_learning_orchestrator_v2 import load_learning_state
    
    state = load_learning_state()
    print(f"OK: Learning state loaded:")
    print(f"  - Trades processed: {state.get('total_trades_processed', 0)}")
    print(f"  - Trades learned from: {state.get('total_trades_learned_from', 0)}")
    print(f"  - Last processed: {state.get('last_processed_ts', 'never')}")
except Exception as e:
    print(f"FAIL: Error loading learning state: {e}")

# 6. Check weight state file
print("\n6. WEIGHT STATE FILE")
print("-" * 80)

weights_file = STATE_DIR / "signal_weights.json"
if weights_file.exists():
    try:
        with weights_file.open("r") as f:
            weights_data = json.load(f)
        
        if weights_data:
            print(f"OK: Weight state file exists")
            
            # Check for learned multipliers
            if "weight_bands" in weights_data:
                bands = weights_data["weight_bands"]
                adjusted = [k for k, v in bands.items() if isinstance(v, dict) and v.get("current", 1.0) != 1.0]
                if adjusted:
                    print(f"  ✓ Found {len(adjusted)} adjusted weight bands")
                    for comp in adjusted[:3]:
                        band = bands[comp]
                        print(f"    - {comp}: multiplier={band.get('current', 1.0):.2f}x, samples={band.get('sample_count', 0)}")
                else:
                    print("  WARNING: All multipliers at 1.0x (no learning yet)")
            else:
                print("  WARNING: No weight_bands in file")
        else:
            print("  WARNING: Weight file is empty")
    except Exception as e:
        print(f"FAIL: Error reading weight file: {e}")
else:
    print("WARNING: Weight state file not found")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
