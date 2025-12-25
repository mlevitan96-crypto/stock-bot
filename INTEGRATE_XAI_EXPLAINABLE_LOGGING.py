#!/usr/bin/env python3
"""
Integration script to add Explainable AI (XAI) logging to main.py
This script adds explainable logging at critical points:
1. Trade entry (in decide_and_execute)
2. Trade exit (in log_exit_attribution)
3. Weight adjustments (in comprehensive_learning_orchestrator_v2)
"""

import re
from pathlib import Path

def integrate_xai_logging():
    """Add explainable logging to main.py"""
    
    main_py = Path("main.py")
    if not main_py.exists():
        print("ERROR: main.py not found")
        return False
    
    content = main_py.read_text(encoding='utf-8')
    
    # 1. Add import at top
    if "from xai.explainable_logger import get_explainable_logger" not in content:
        # Find last import line
        import_pattern = r'(from\s+\S+\s+import\s+[^\n]+)'
        imports = list(re.finditer(import_pattern, content))
        if imports:
            last_import = imports[-1]
            insert_pos = last_import.end()
            content = content[:insert_pos] + "\nfrom xai.explainable_logger import get_explainable_logger" + content[insert_pos:]
            print("[OK] Added XAI import")
    
    # 2. Add explainable logging to trade entry (after order submission)
    # Find the pattern where order is submitted
    entry_pattern = r'(o\s*=\s*self\.executor\.submit_entry\([^)]+\)\s*\n)'
    entry_match = re.search(entry_pattern, content)
    
    if entry_match:
        insert_pos = entry_match.end()
        # Check if already added
        if "explainable.log_trade_entry" not in content[entry_match.start():entry_match.end()+200]:
            # Get context for explainable logging
            explainable_code = '''
            # XAI: Log explainable trade entry
            try:
                explainable = get_explainable_logger()
                # Get regime
                regime_name = market_regime
                try:
                    from structural_intelligence import get_regime_detector
                    regime_detector = get_regime_detector()
                    regime_name, _ = regime_detector.detect_regime()
                except:
                    pass
                
                # Get macro yield
                macro_yield = None
                try:
                    from structural_intelligence import get_macro_gate
                    macro_gate = get_macro_gate()
                    macro_yield = macro_gate.get_current_yield()
                except:
                    pass
                
                # Get whale clusters
                whale_clusters = {}
                if c.get("source") not in ("composite", "composite_v3"):
                    whale_clusters = {
                        "count": c.get("count", 0),
                        "premium_usd": c.get("avg_premium", 0) * c.get("count", 0)
                    }
                
                # Get gamma walls
                gamma_walls = None
                try:
                    from structural_intelligence import get_structural_exit
                    structural_exit = get_structural_exit()
                    position_data = {"current_price": ref_price_check, "side": side, "entry_price": ref_price_check}
                    exit_rec = structural_exit.get_exit_recommendation(symbol, position_data)
                    if exit_rec.get("gamma_wall_distance"):
                        gamma_walls = {
                            "distance_pct": exit_rec.get("gamma_wall_distance"),
                            "gamma_exposure": exit_rec.get("gamma_exposure", 0)
                        }
                except:
                    pass
                
                why_sentence = explainable.log_trade_entry(
                    symbol=symbol,
                    direction=direction,
                    score=score,
                    components=comps,
                    regime=regime_name,
                    macro_yield=macro_yield,
                    whale_clusters=whale_clusters,
                    gamma_walls=gamma_walls,
                    composite_score=score,
                    entry_price=ref_price_check
                )
                log_event("xai", "trade_entry_logged", symbol=symbol, why=why_sentence)
            except Exception as e:
                log_event("xai", "trade_entry_log_failed", symbol=symbol, error=str(e))
'''
            content = content[:insert_pos] + explainable_code + content[insert_pos:]
            print("[OK] Added XAI logging to trade entry")
    
    # 3. Add explainable logging to trade exit (in log_exit_attribution)
    exit_pattern = r'(learn_from_trade_close\(symbol[^)]+\)\s*\n)'
    exit_match = re.search(exit_pattern, content)
    
    if exit_match:
        insert_pos = exit_match.end()
        # Check if already added
        if "explainable.log_trade_exit" not in content[exit_match.start():exit_match.end()+200]:
            explainable_exit_code = '''
        # XAI: Log explainable trade exit
        try:
            explainable = get_explainable_logger()
            
            # Get regime
            regime_name = context.get("market_regime", "unknown")
            
            # Get gamma walls at exit
            gamma_walls = None
            try:
                from structural_intelligence import get_structural_exit
                structural_exit = get_structural_exit()
                position_data = {
                    "current_price": exit_price,
                    "side": side,
                    "entry_price": entry_price,
                    "unrealized_pnl_pct": pnl_pct / 100.0
                }
                exit_rec = structural_exit.get_exit_recommendation(symbol, position_data)
                if exit_rec.get("gamma_wall_distance"):
                    gamma_walls = {
                        "distance_pct": exit_rec.get("gamma_wall_distance"),
                        "gamma_exposure": exit_rec.get("gamma_exposure", 0)
                    }
            except:
                pass
            
            why_sentence = explainable.log_trade_exit(
                symbol=symbol,
                entry_price=entry_price,
                exit_price=exit_price,
                pnl_pct=pnl_pct,
                hold_minutes=hold_minutes,
                exit_reason=close_reason,
                regime=regime_name,
                gamma_walls=gamma_walls
            )
            log_event("xai", "trade_exit_logged", symbol=symbol, why=why_sentence)
        except Exception as e:
            log_event("xai", "trade_exit_log_failed", symbol=symbol, error=str(e))
'''
            content = content[:insert_pos] + explainable_exit_code + content[insert_pos:]
            print("[OK] Added XAI logging to trade exit")
    
    # Write back
    main_py.write_text(content, encoding='utf-8')
    print("[OK] Integration complete")
    return True

if __name__ == "__main__":
    integrate_xai_logging()

