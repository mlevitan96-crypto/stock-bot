#!/usr/bin/env python3
"""
Startup Contract Check - Runs BEFORE trading bot starts
Catches integration bugs between daemon and scoring BEFORE they cause runtime errors
"""

import sys
import json
from pathlib import Path
from datetime import datetime

def run_startup_contract_check() -> bool:
    """
    Run contract validation and composite scoring smoke test.
    Returns True if passed, False if failed.
    """
    print("=" * 70)
    print("  STARTUP CONTRACT CHECK")
    print("=" * 70)
    
    errors = []
    warnings = []
    
    try:
        # NOTE: internal_contract_validator is optional - if missing, validation is skipped
        from internal_contract_validator import run_preflight_validation, validate_enriched_signal
        passed, report = run_preflight_validation()
        
        if not passed:
            errors.append(f"Contract validation failed: {report['total_violations']} violations")
            for v in report.get("violations", [])[:5]:
                errors.append(f"  - {v['section']}.{v['field']}: expected {v['expected_type']}, got {v['actual_type']}")
        else:
            print("✅ Contract validation passed")
    except Exception as e:
        warnings.append(f"Contract validator not available: {e}")
    
    try:
        from uw_composite_v2 import compute_composite_score_v2
        
        test_signal = {
            "sentiment": "BULLISH",
            "conviction": 0.7,
            "dark_pool": {"sentiment": "BULLISH", "total_premium": 1000000},
            "insider": {"sentiment": "NEUTRAL", "conviction_modifier": 0.0},
            "calendar": {"has_earnings": False, "economic_events": 2},
            "congress": {"buys": 1, "sells": 0},
            "shorts": {"interest_pct": 10.0, "days_to_cover": 2.0},
            "greeks": {"gamma_exposure": 100000, "gamma_squeeze_setup": False},
            "ftd": {"ftd_count": 50000, "squeeze_pressure": False},
            "iv": {"iv_rank": 40, "iv_percentile": 45},
            "oi": {"net_oi_change": 10000, "oi_sentiment": "NEUTRAL"},
            "etf_flow": {"overall_sentiment": "NEUTRAL", "market_risk_on": False},
            "squeeze_score": {"signals": 0, "high_squeeze_potential": False}
        }
        
        result = compute_composite_score_v2("TEST", test_signal, "NEUTRAL")
        
        required_fields = ["score", "components", "features_for_learning"]
        missing = [f for f in required_fields if f not in result]
        if missing:
            errors.append(f"Composite scoring missing fields: {missing}")
        else:
            print(f"✅ Composite scoring smoke test passed (score: {result['score']:.3f})")
        
        v2_components = ["greeks_gamma", "ftd_pressure", "iv_rank", "oi_change", "etf_flow", "squeeze_score"]
        missing_v2 = [c for c in v2_components if c not in result.get("components", {})]
        if missing_v2:
            warnings.append(f"V2 components missing from output: {missing_v2}")
        else:
            print("✅ V2 components present in scoring output")
            
    except TypeError as e:
        errors.append(f"TYPE ERROR in composite scoring: {e}")
        errors.append("  This indicates a producer/consumer contract mismatch!")
    except Exception as e:
        errors.append(f"Composite scoring smoke test failed: {e}")
    
    try:
        cache_path = Path("data/uw_flow_cache.json")
        if cache_path.exists():
            with cache_path.open("r") as f:
                cache = json.load(f)
            
            if isinstance(cache, dict) and len(cache) > 0:
                sample_symbol = list(cache.keys())[0]
                sample_data = cache[sample_symbol]
                
                result = compute_composite_score_v2(sample_symbol, sample_data, "NEUTRAL")
                print(f"✅ Live cache smoke test passed ({sample_symbol}: {result['score']:.3f})")
            else:
                warnings.append("Cache is empty, skipping live test")
        else:
            warnings.append("Cache file not found, skipping live test")
    except TypeError as e:
        errors.append(f"LIVE DATA TYPE ERROR: {e}")
        errors.append("  Real cache data has contract violation!")
    except Exception as e:
        warnings.append(f"Live cache test skipped: {e}")
    
    print("\n" + "-" * 70)
    
    if warnings:
        print(f"⚠️  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"   {w}")
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for e in errors:
            print(f"   {e}")
        print("\n" + "=" * 70)
        print("  STARTUP CHECK FAILED - FIX ERRORS BEFORE TRADING")
        print("=" * 70)
        
        log_path = Path("data/startup_check_failures.jsonl")
        log_path.parent.mkdir(exist_ok=True, parents=True)
        with log_path.open("a") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "errors": errors,
                "warnings": warnings
            }) + "\n")
        
        return False
    
    print("\n" + "=" * 70)
    print("  ✅ STARTUP CHECK PASSED - READY TO TRADE")
    print("=" * 70)
    return True


if __name__ == "__main__":
    passed = run_startup_contract_check()
    sys.exit(0 if passed else 1)
