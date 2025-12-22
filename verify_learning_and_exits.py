#!/usr/bin/env python3
"""
Comprehensive Verification Script for Learning System and Exit Logic

Verifies:
1. Learning system is updating weights correctly
2. Adaptive weights are being loaded and applied
3. Exit logic (stops, profit targets) is working correctly
4. All components are properly connected
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

STATE_DIR = Path("state")
DATA_DIR = Path("data")
LOGS_DIR = Path("logs")

def check_learning_system():
    """Verify learning system is updating weights correctly"""
    print("\n" + "="*80)
    print("LEARNING SYSTEM VERIFICATION")
    print("="*80)
    
    issues = []
    successes = []
    
    # 1. Check if learning orchestrator exists and can be imported
    try:
        from comprehensive_learning_orchestrator_v2 import (
            load_learning_state,
            process_all_learning_sources
        )
        successes.append("✓ Learning orchestrator v2 imported successfully")
    except Exception as e:
        issues.append(f"✗ Failed to import learning orchestrator: {e}")
        return {"status": "FAILED", "issues": issues, "successes": successes}
    
    # 2. Check learning state file
    learning_state = load_learning_state()
    total_trades = learning_state.get("total_trades_processed", 0)
    total_learned = learning_state.get("total_trades_learned_from", 0)
    
    if total_trades > 0:
        successes.append(f"✓ Learning state found: {total_trades} trades processed, {total_learned} learned from")
    else:
        issues.append("⚠ No trades processed yet - learning system waiting for data")
    
    # 3. Check if adaptive optimizer exists
    try:
        from adaptive_signal_optimizer import get_optimizer, SIGNAL_COMPONENTS
        optimizer = get_optimizer()
        if optimizer:
            has_learned = optimizer.has_learned_weights()
            if has_learned:
                weights = optimizer.get_weights_for_composite()
                adjusted_count = sum(1 for w in weights.values() if w != 1.0) if weights else 0
                successes.append(f"✓ Adaptive optimizer loaded: {adjusted_count} weights adjusted from default")
            else:
                issues.append("⚠ Adaptive optimizer loaded but no weights learned yet (need more trades)")
        else:
            issues.append("⚠ Adaptive optimizer not initialized")
    except Exception as e:
        issues.append(f"✗ Failed to load adaptive optimizer: {e}")
    
    # 4. Check if weights are being applied in composite scoring
    try:
        from uw_composite_v2 import get_adaptive_weights, compute_composite_score_v3
        
        adaptive_weights = get_adaptive_weights()
        if adaptive_weights:
            successes.append(f"✓ Adaptive weights available: {len(adaptive_weights)} components")
            # Show sample weights
            sample = dict(list(adaptive_weights.items())[:3])
            successes.append(f"  Sample weights: {sample}")
        else:
            issues.append("⚠ No adaptive weights loaded (using defaults)")
        
        # Test composite scoring with adaptive weights
        test_data = {
            "sentiment": "BULLISH",
            "conviction": 0.7,
            "dark_pool": {"sentiment": "BULLISH", "total_premium": 1000000},
            "insider": {"sentiment": "BULLISH", "net_buys": 5}
        }
        result = compute_composite_score_v3("TEST", test_data, "NEUTRAL", use_adaptive_weights=True)
        if result and "score" in result:
            successes.append(f"✓ Composite scoring works with adaptive weights: score={result['score']:.2f}")
        else:
            issues.append("✗ Composite scoring failed")
            
    except Exception as e:
        issues.append(f"✗ Failed to verify weight application: {e}")
    
    # 5. Check weight update frequency
    try:
        from adaptive_signal_optimizer import LearningOrchestrator
        # Check MIN_DAYS_BETWEEN_UPDATES
        min_days = LearningOrchestrator.MIN_DAYS_BETWEEN_UPDATES
        successes.append(f"✓ Weight update frequency: {min_days} day(s) between updates")
    except:
        pass
    
    return {
        "status": "PASS" if len(issues) == 0 else "WARNINGS",
        "issues": issues,
        "successes": successes
    }


def check_exit_logic():
    """Verify exit logic (stops, profit targets) is working correctly"""
    print("\n" + "="*80)
    print("EXIT LOGIC VERIFICATION")
    print("="*80)
    
    issues = []
    successes = []
    
    # 1. Check Config for exit parameters
    try:
        from main import Config
        profit_targets = Config.PROFIT_TARGETS
        trailing_stop_pct = Config.TRAILING_STOP_PCT
        max_hold_hours = Config.MAX_HOLD_HOURS
        
        successes.append(f"✓ Exit parameters configured:")
        successes.append(f"  - Profit targets: {profit_targets}")
        successes.append(f"  - Trailing stop: {trailing_stop_pct}%")
        successes.append(f"  - Max hold time: {max_hold_hours}h")
    except Exception as e:
        issues.append(f"✗ Failed to load exit config: {e}")
        return {"status": "FAILED", "issues": issues, "successes": successes}
    
    # 2. Check if evaluate_exits method exists
    try:
        from main import AlpacaExecutor
        executor = AlpacaExecutor(None)  # Will fail, but we just want to check method exists
        if hasattr(executor, 'evaluate_exits'):
            successes.append("✓ evaluate_exits method exists")
        else:
            issues.append("✗ evaluate_exits method missing")
    except:
        # Expected to fail on initialization, but method should exist
        try:
            import inspect
            from main import AlpacaExecutor
            if 'evaluate_exits' in [m for m in dir(AlpacaExecutor) if not m.startswith('_')]:
                successes.append("✓ evaluate_exits method exists in AlpacaExecutor")
            else:
                issues.append("✗ evaluate_exits method missing from AlpacaExecutor")
        except Exception as e:
            issues.append(f"✗ Could not verify evaluate_exits: {e}")
    
    # 3. Check recent exits in logs
    exit_file = LOGS_DIR / "exit.jsonl"
    if exit_file.exists():
        try:
            recent_exits = []
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            
            with exit_file.open("r") as f:
                for line in f.readlines()[-100:]:
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
                # Analyze exit reasons
                reasons = {}
                for exit_event in recent_exits:
                    reason = exit_event.get("reason", "unknown")
                    reasons[reason] = reasons.get(reason, 0) + 1
                
                successes.append(f"✓ Found {len(recent_exits)} recent exits (last 7 days)")
                successes.append(f"  Exit reasons: {dict(list(reasons.items())[:5])}")
                
                # Check if profit targets and stops are being used
                has_profit_target = any("profit_target" in str(r).lower() for r in reasons.keys())
                has_trail_stop = any("trail" in str(r).lower() or "stop" in str(r).lower() for r in reasons.keys())
                has_time_exit = any("time" in str(r).lower() for r in reasons.keys())
                
                if has_profit_target:
                    successes.append("  ✓ Profit targets are being triggered")
                else:
                    issues.append("⚠ No profit target exits found (may be normal if no winners)")
                
                if has_trail_stop:
                    successes.append("  ✓ Trailing stops are being triggered")
                else:
                    issues.append("⚠ No trailing stop exits found")
                
                if has_time_exit:
                    successes.append("  ✓ Time-based exits are working")
                else:
                    issues.append("⚠ No time-based exits found")
            else:
                issues.append("⚠ No recent exits found (may be normal if no positions closed)")
        except Exception as e:
            issues.append(f"✗ Error reading exit logs: {e}")
    else:
        issues.append("⚠ Exit log file not found (no exits logged yet)")
    
    # 4. Check attribution logs for exit P&L
    attribution_file = LOGS_DIR / "attribution.jsonl"
    if attribution_file.exists():
        try:
            recent_closes = []
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            
            with attribution_file.open("r") as f:
                for line in f.readlines()[-100:]:
                    try:
                        trade = json.loads(line.strip())
                        if trade.get("type") != "attribution":
                            continue
                        
                        trade_id = trade.get("trade_id", "")
                        if trade_id.startswith("open_"):
                            continue  # Skip open trades
                        
                        ts_str = trade.get("ts", "")
                        if ts_str:
                            if isinstance(ts_str, (int, float)):
                                trade_time = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                            else:
                                trade_time = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                                if trade_time.tzinfo is None:
                                    trade_time = trade_time.replace(tzinfo=timezone.utc)
                            
                            if trade_time >= cutoff:
                                recent_closes.append(trade)
                    except:
                        continue
            
            if recent_closes:
                pnls = [float(t.get("pnl_usd", 0.0)) for t in recent_closes]
                wins = sum(1 for p in pnls if p > 0)
                losses = sum(1 for p in pnls if p < 0)
                
                successes.append(f"✓ Found {len(recent_closes)} recent closed trades")
                successes.append(f"  Wins: {wins}, Losses: {losses}, Win rate: {wins/len(recent_closes)*100:.1f}%")
                
                # Check if P&L is being calculated correctly
                if all(p == 0.0 for p in pnls):
                    issues.append("✗ CRITICAL: All P&L values are $0.00 - exit logic may not be calculating correctly")
                else:
                    successes.append(f"  ✓ P&L calculation working: avg=${sum(pnls)/len(pnls):.2f}")
            else:
                issues.append("⚠ No recent closed trades found")
        except Exception as e:
            issues.append(f"✗ Error reading attribution logs: {e}")
    
    # 5. Check position metadata for exit tracking
    metadata_file = STATE_DIR / "position_metadata.json"
    if metadata_file.exists():
        try:
            with metadata_file.open("r") as f:
                metadata = json.load(f)
            
            open_positions = len([s for s, m in metadata.items() if m.get("entry_ts")])
            successes.append(f"✓ Position metadata tracking {open_positions} positions")
        except Exception as e:
            issues.append(f"⚠ Error reading position metadata: {e}")
    
    return {
        "status": "PASS" if len(issues) == 0 else "WARNINGS",
        "issues": issues,
        "successes": successes
    }


def check_weight_application_flow():
    """Verify the complete flow: learning → weight update → application"""
    print("\n" + "="*80)
    print("WEIGHT APPLICATION FLOW VERIFICATION")
    print("="*80)
    
    issues = []
    successes = []
    
    # 1. Check if weights are saved after learning
    weights_file = STATE_DIR / "signal_weights.json"
    if weights_file.exists():
        try:
            with weights_file.open("r") as f:
                weights_data = json.load(f)
            
            if weights_data:
                successes.append("✓ Signal weights file exists")
                # Check if it has learned weights
                has_learned = any(
                    isinstance(v, dict) and v.get("current") != 1.0 
                    for v in weights_data.values()
                ) or any(
                    isinstance(v, (int, float)) and v != 1.0 
                    for v in weights_data.values()
                )
                
                if has_learned:
                    successes.append("  ✓ Contains learned weights (not all defaults)")
                else:
                    issues.append("⚠ All weights are at default (1.0) - learning may not have updated yet")
            else:
                issues.append("⚠ Signal weights file is empty")
        except Exception as e:
            issues.append(f"✗ Error reading weights file: {e}")
    else:
        issues.append("⚠ Signal weights file not found - weights may not be persisted")
    
    # 2. Verify weight loading in composite scoring
    try:
        from uw_composite_v2 import get_adaptive_weights, WEIGHTS_V3
        
        # Test weight loading
        adaptive = get_adaptive_weights()
        if adaptive:
            # Check if weights are different from defaults
            different = False
            for component, weight in list(adaptive.items())[:5]:
                default = WEIGHTS_V3.get(component, 0.0)
                if weight != default:
                    different = True
                    break
            
            if different:
                successes.append("✓ Adaptive weights differ from defaults (learning is working)")
            else:
                issues.append("⚠ Adaptive weights match defaults exactly (may need more learning)")
        else:
            issues.append("⚠ No adaptive weights returned")
    except Exception as e:
        issues.append(f"✗ Failed to verify weight loading: {e}")
    
    # 3. Check if main.py is calling learning system
    try:
        # Check if comprehensive_learning_orchestrator_v2 is imported
        import main
        if hasattr(main, 'comprehensive_learning_orchestrator_v2'):
            successes.append("✓ Learning orchestrator imported in main.py")
        else:
            # Check if it's called via learn_from_trade_close
            if 'learn_from_trade_close' in str(main.__file__):
                successes.append("✓ Learning system referenced in main.py")
            else:
                issues.append("⚠ Learning system may not be integrated in main.py")
    except:
        pass
    
    return {
        "status": "PASS" if len(issues) == 0 else "WARNINGS",
        "issues": issues,
        "successes": successes
    }


def main():
    """Run all verification checks"""
    print("\n" + "="*80)
    print("COMPREHENSIVE LEARNING & EXIT VERIFICATION")
    print("="*80)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    results = {}
    
    # 1. Learning system check
    results["learning"] = check_learning_system()
    
    # 2. Exit logic check
    results["exits"] = check_exit_logic()
    
    # 3. Weight application flow check
    results["weight_flow"] = check_weight_application_flow()
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    total_issues = 0
    total_successes = 0
    
    for check_name, result in results.items():
        status = result["status"]
        issues = result["issues"]
        successes = result["successes"]
        
        total_issues += len(issues)
        total_successes += len(successes)
        
        status_symbol = "✓" if status == "PASS" else "⚠" if status == "WARNINGS" else "✗"
        print(f"\n{status_symbol} {check_name.upper()}: {status}")
        print(f"  Successes: {len(successes)}, Issues: {len(issues)}")
        
        if issues:
            for issue in issues[:5]:  # Show first 5 issues
                print(f"    {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more issues")
    
    print("\n" + "="*80)
    print(f"OVERALL: {total_successes} checks passed, {total_issues} issues found")
    
    if total_issues == 0:
        print("✓ ALL SYSTEMS OPERATIONAL")
    elif total_issues < 5:
        print("⚠ MINOR ISSUES DETECTED - System functional but may need attention")
    else:
        print("✗ SIGNIFICANT ISSUES DETECTED - Review required")
    
    print("="*80 + "\n")
    
    # Save results
    results_file = DATA_DIR / "verification_results.json"
    results_file.parent.mkdir(exist_ok=True)
    with results_file.open("w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": results,
            "summary": {
                "total_issues": total_issues,
                "total_successes": total_successes
            }
        }, f, indent=2)
    
    print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    main()
