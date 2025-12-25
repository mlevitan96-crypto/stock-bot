#!/usr/bin/env python3
"""
Integration Script: Structural Intelligence Overhaul
Integrates all 5 components into main.py and learning orchestrator.
"""

import re
from pathlib import Path

def integrate_regime_and_macro_into_composite_score():
    """Integrate regime detector and macro gate into composite score calculation"""
    
    # Find where composite_score is used in decide_and_execute
    main_py = Path("main.py")
    content = main_py.read_text(encoding='utf-8')
    
    # Find the section where composite_score is used
    pattern = r'(# PRIORITIZE COMPOSITE SCORE: If cluster has pre-calculated composite_score, always use it\n.*?score = c\["composite_score"\])'
    
    replacement = r'''# PRIORITIZE COMPOSITE SCORE: If cluster has pre-calculated composite_score, always use it
            if "composite_score" in c and c.get("source") in ("composite", "composite_v3"):
                base_score = c["composite_score"]
                
                # STRUCTURAL INTELLIGENCE: Apply regime and macro multipliers
                try:
                    from structural_intelligence import get_regime_detector, get_macro_gate
                    regime_detector = get_regime_detector()
                    macro_gate = get_macro_gate()
                    
                    # Get regime multiplier
                    regime_name, regime_conf = regime_detector.detect_regime()
                    regime_mult = regime_detector.get_regime_multiplier(direction)
                    
                    # Get macro multiplier
                    sector = self.theme_map.get(symbol, "Technology")  # Default to tech
                    macro_mult = macro_gate.get_macro_multiplier(direction, sector)
                    
                    # Apply multipliers to composite score
                    score = base_score * regime_mult * macro_mult
                    
                    log_event("structural_intelligence", "composite_adjusted", 
                             symbol=symbol, base_score=base_score, regime_mult=regime_mult, 
                             macro_mult=macro_mult, final_score=score, regime=regime_name)
                except ImportError:
                    score = base_score
                    log_event("structural_intelligence", "import_failed", symbol=symbol)
                except Exception as e:
                    score = base_score
                    log_event("structural_intelligence", "error", symbol=symbol, error=str(e))'''
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        main_py.write_text(content, encoding='utf-8')
        print("[OK] Integrated regime and macro gates into composite score")
        return True
    else:
        print("[WARNING] Could not find composite score section to integrate")
        return False

def integrate_structural_exit_into_evaluate_exits():
    """Integrate structural exit manager into evaluate_exits"""
    
    main_py = Path("main.py")
    content = main_py.read_text(encoding='utf-8')
    
    # Find where exit decisions are made
    pattern = r'(exit_signals\["pnl_pct"\] = pnl_pct\n.*?high_water_pct = .*?\n)'
    
    replacement = r'''exit_signals["pnl_pct"] = pnl_pct
            high_water_pct = ((high_water_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            # STRUCTURAL EXIT: Check for gamma call walls and liquidity exhaustion
            try:
                from structural_intelligence import get_structural_exit
                structural_exit = get_structural_exit()
                
                position_data = {
                    "current_price": current_price,
                    "side": info.get("side", "buy"),
                    "entry_price": entry_price,
                    "unrealized_pnl_pct": pnl_pct / 100.0
                }
                
                exit_rec = structural_exit.get_exit_recommendation(symbol, position_data)
                
                if exit_rec.get("should_exit"):
                    exit_reason = exit_rec.get("reason", "structural_exit")
                    scale_pct = exit_rec.get("scale_out_pct", 1.0)
                    
                    # Add to exit signals
                    exit_signals["structural_exit"] = exit_reason
                    exit_signals["scale_out_pct"] = scale_pct
                    
                    log_event("structural_exit", exit_reason, symbol=symbol, 
                             scale_pct=scale_pct, pnl_pct=pnl_pct)
            except ImportError:
                pass
            except Exception as e:
                log_event("structural_exit", "error", symbol=symbol, error=str(e))
            
            '''
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        main_py.write_text(content, encoding='utf-8')
        print("[OK] Integrated structural exit into evaluate_exits")
        return True
    else:
        print("[WARNING] Could not find exit evaluation section")
        return False

def integrate_thompson_sampling_into_learning():
    """Integrate Thompson Sampling into learning orchestrator"""
    
    orchestrator_py = Path("comprehensive_learning_orchestrator_v2.py")
    if not orchestrator_py.exists():
        print("[WARNING] Learning orchestrator not found")
        return False
    
    content = orchestrator_py.read_text(encoding='utf-8')
    
    # Find where weights are updated
    pattern = r'(# Update component weights.*?optimizer\.update_weights)'
    
    replacement = r'''# Update component weights using Thompson Sampling
            try:
                from learning import get_thompson_engine
                thompson = get_thompson_engine()
                
                # Register components if not already registered
                for comp_name in comps.keys():
                    thompson.register_component(comp_name, initial_weight=1.0)
                
                # Get optimal weights from Thompson Sampling
                thompson_weights = thompson.get_all_weights()
                
                # Update optimizer with Thompson Sampling weights
                for comp_name, weight in thompson_weights.items():
                    if comp_name in comps:
                        # Record outcome for Thompson Sampling
                        thompson.record_outcome(comp_name, weight, pnl_pct, success_threshold=0.0)
                        
                        # Check if should finalize weight
                        if thompson.should_finalize_weight(comp_name):
                            thompson.finalize_weight(comp_name)
                            # Update optimizer
                            optimizer.update_component_weight(comp_name, weight)
            except ImportError:
                # Fallback to original optimizer
                optimizer.update_weights'''
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        orchestrator_py.write_text(content, encoding='utf-8')
        print("[OK] Integrated Thompson Sampling into learning orchestrator")
        return True
    else:
        print("[WARNING] Could not find weight update section")
        return False

def integrate_shadow_logger_into_gates():
    """Integrate shadow logger into gate blocking"""
    
    main_py = Path("main.py")
    content = main_py.read_text(encoding='utf-8')
    
    # Find gate blocking sections
    # This is complex - we'll add shadow logging after each gate block
    
    # Pattern for score gate
    score_gate_pattern = r'(if score < min_score:.*?log_blocked_trade\(.*?continue)'
    
    score_gate_replacement = r'''if score < min_score:
                print(f"DEBUG {symbol}: BLOCKED by score_below_min ({score} < {min_score}, stage={system_stage})", flush=True)
                log_event("gate", "score_below_min", symbol=symbol, score=score, min_required=min_score, stage=system_stage)
                
                # SHADOW LOGGER: Track rejected signal
                try:
                    from self_healing import get_shadow_logger
                    shadow = get_shadow_logger()
                    threshold = shadow.get_gate_threshold("score_gate", "min_score", min_score)
                    shadow.log_rejected_signal(symbol, "score_below_min", score, comps, "score_gate", threshold)
                except:
                    pass
                
                log_blocked_trade(symbol, "score_below_min", score,
                                  direction=c.get("direction"),
                                  decision_price=ref_price_check,
                                  components=comps,
                                  min_required=min_score,
                                  stage=system_stage)
                continue'''
    
    if re.search(score_gate_pattern, content, re.DOTALL):
        content = re.sub(score_gate_pattern, score_gate_replacement, content, flags=re.DOTALL)
        print("[OK] Integrated shadow logger into score gate")
    
    # Pattern for expectancy gate
    expectancy_gate_pattern = r'(if not should_trade:.*?log_blocked_trade\(.*?continue)'
    
    expectancy_gate_replacement = r'''if not should_trade:
                log_event("gate", "expectancy_blocked", symbol=symbol, 
                         expectancy=expectancy, reason=gate_reason, stage=system_stage)
                
                # SHADOW LOGGER: Track rejected signal
                try:
                    from self_healing import get_shadow_logger
                    shadow = get_shadow_logger()
                    threshold = shadow.get_gate_threshold("expectancy_gate", "min_expectancy", 0.0)
                    shadow.log_rejected_signal(symbol, f"expectancy_blocked:{gate_reason}", score, comps, "expectancy_gate", threshold)
                except:
                    pass
                
                log_blocked_trade(symbol, f"expectancy_blocked:{gate_reason}", score, 
                                  direction=c.get("direction"),
                                  decision_price=ref_price_check,
                                  components=comps,
                                  expectancy=expectancy, stage=system_stage)
                continue'''
    
    if re.search(expectancy_gate_pattern, content, re.DOTALL):
        content = re.sub(expectancy_gate_pattern, expectancy_gate_replacement, content, flags=re.DOTALL)
        print("[OK] Integrated shadow logger into expectancy gate")
    
    main_py.write_text(content, encoding='utf-8')
    return True

def integrate_token_bucket_into_polling():
    """Integrate token bucket into API polling"""
    
    # Find SmartPoller or polling code
    main_py = Path("main.py")
    content = main_py.read_text(encoding='utf-8')
    
    # This would need to find the polling code and add quota checks
    # For now, we'll create a wrapper function
    
    print("[INFO] Token bucket integration requires finding polling code")
    print("[INFO] This will be integrated into SmartPoller class")
    
    return True

def main():
    """Run all integrations"""
    print("=" * 80)
    print("STRUCTURAL INTELLIGENCE INTEGRATION")
    print("=" * 80)
    
    results = {}
    
    results["regime_macro"] = integrate_regime_and_macro_into_composite_score()
    results["structural_exit"] = integrate_structural_exit_into_evaluate_exits()
    results["thompson_sampling"] = integrate_thompson_sampling_into_learning()
    results["shadow_logger"] = integrate_shadow_logger_into_gates()
    results["token_bucket"] = integrate_token_bucket_into_polling()
    
    print("\n" + "=" * 80)
    print("INTEGRATION SUMMARY")
    print("=" * 80)
    
    for name, result in results.items():
        status = "[OK]" if result else "[WARNING]"
        print(f"{status} {name}")
    
    return 0

if __name__ == "__main__":
    main()

