#!/usr/bin/env python3
"""
Comprehensive Score Diagnostic - Run this on the droplet to diagnose low scores.
This script will:
1. Check signal data quality
2. Check component calculations
3. Check weights
4. Check freshness calculations
5. Test actual score computation
6. Identify root causes
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def load_cache() -> Dict:
    """Load UW flow cache."""
    cache_path = Path("data/uw_flow_cache.json")
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR loading cache: {e}")
        return {}

def test_composite_scoring():
    """Test composite scoring with actual data."""
    print("\n" + "=" * 80)
    print("TESTING COMPOSITE SCORING")
    print("=" * 80)
    
    try:
        from uw_composite_v2 import compute_composite_score_v3, WEIGHTS_V3
        from uw_enrichment_v2 import enrich_signal
        
        print(f"\nLoaded WEIGHTS_V3: {len(WEIGHTS_V3)} components")
        print("Top weights:")
        for comp, weight in sorted(WEIGHTS_V3.items(), key=lambda x: abs(x[1]), reverse=True)[:10]:
            print(f"  {comp}: {weight:.3f}")
        
        # Load cache
        cache = load_cache()
        symbols = [s for s in cache.keys() if not s.startswith("_")][:5]
        
        if not symbols:
            print("\n❌ No symbols in cache to test!")
            return
        
        print(f"\nTesting with {len(symbols)} symbols...")
        
        for symbol in symbols:
            print(f"\n--- {symbol} ---")
            symbol_data = cache.get(symbol, {})
            
            if not symbol_data:
                print("  ❌ No data for symbol")
                continue
            
            # Enrich signal
            try:
                enriched = enrich_signal(symbol, cache, "NEUTRAL")
                print(f"  Enriched: sentiment={enriched.get('sentiment')}, conviction={enriched.get('conviction', 0):.3f}, freshness={enriched.get('freshness', 1.0):.3f}")
                
                # Compute composite score
                result = compute_composite_score_v3(symbol, enriched, "NEUTRAL")
                
                if result:
                    score = result.get('score', 0.0)
                    components = result.get('components', {})
                    
                    print(f"  ✅ Composite Score: {score:.3f}")
                    print(f"  Components breakdown:")
                    for comp_name, comp_value in sorted(components.items(), key=lambda x: abs(x[1]), reverse=True):
                        if abs(comp_value) > 0.001:  # Only show non-zero
                            print(f"    {comp_name}: {comp_value:.3f}")
                    
                    # Check for issues
                    if score < 1.0:
                        print(f"  ⚠️  WARNING: Score is very low!")
                        # Check which components are contributing
                        total_positive = sum(v for v in components.values() if v > 0)
                        total_negative = sum(v for v in components.values() if v < 0)
                        print(f"    Total positive contributions: {total_positive:.3f}")
                        print(f"    Total negative contributions: {total_negative:.3f}")
                        print(f"    Freshness factor: {components.get('freshness_factor', 1.0):.3f}")
                else:
                    print("  ❌ compute_composite_score_v3 returned None")
                    
            except Exception as e:
                print(f"  ❌ Error computing score: {e}")
                import traceback
                traceback.print_exc()
                
    except ImportError as e:
        print(f"❌ Could not import scoring modules: {e}")
        import traceback
        traceback.print_exc()

def analyze_signal_data():
    """Analyze signal data quality."""
    print("\n" + "=" * 80)
    print("ANALYZING SIGNAL DATA QUALITY")
    print("=" * 80)
    
    cache = load_cache()
    symbols = [s for s in cache.keys() if not s.startswith("_")]
    
    print(f"\nTotal symbols in cache: {len(symbols)}")
    
    if not symbols:
        print("❌ No symbols found in cache!")
        return
    
    # Analyze each symbol
    issues = []
    stats = {
        "has_flow": 0,
        "has_dark_pool": 0,
        "has_insider": 0,
        "has_iv_skew": 0,
        "has_smile_slope": 0,
        "has_freshness": 0,
        "low_conviction": 0,
        "low_freshness": 0,
        "missing_expanded_intel": 0,
    }
    
    for symbol in symbols[:20]:  # Check first 20
        data = cache.get(symbol, {})
        if not isinstance(data, dict):
            continue
        
        if "sentiment" in data and "conviction" in data:
            stats["has_flow"] += 1
            conv = data.get("conviction", 0.0)
            if conv < 0.1:
                stats["low_conviction"] += 1
                issues.append(f"{symbol}: Very low conviction ({conv:.3f})")
        else:
            issues.append(f"{symbol}: Missing flow data")
        
        if "dark_pool" in data:
            stats["has_dark_pool"] += 1
        else:
            issues.append(f"{symbol}: Missing dark_pool")
        
        if "insider" in data:
            stats["has_insider"] += 1
        else:
            issues.append(f"{symbol}: Missing insider")
        
        if "iv_term_skew" in data:
            stats["has_iv_skew"] += 1
        else:
            issues.append(f"{symbol}: Missing iv_term_skew")
        
        if "smile_slope" in data:
            stats["has_smile_slope"] += 1
        else:
            issues.append(f"{symbol}: Missing smile_slope")
        
        if "freshness" in data:
            stats["has_freshness"] += 1
            fresh = data.get("freshness", 1.0)
            if fresh < 0.5:
                stats["low_freshness"] += 1
                issues.append(f"{symbol}: Low freshness ({fresh:.3f})")
        else:
            issues.append(f"{symbol}: Missing freshness")
        
        if "expanded_intel" not in data:
            stats["missing_expanded_intel"] += 1
    
    print(f"\nStatistics (out of {min(20, len(symbols))} symbols checked):")
    print(f"  Has flow: {stats['has_flow']}/{min(20, len(symbols))}")
    print(f"  Has dark_pool: {stats['has_dark_pool']}/{min(20, len(symbols))}")
    print(f"  Has insider: {stats['has_insider']}/{min(20, len(symbols))}")
    print(f"  Has iv_skew: {stats['has_iv_skew']}/{min(20, len(symbols))}")
    print(f"  Has smile_slope: {stats['has_smile_slope']}/{min(20, len(symbols))}")
    print(f"  Has freshness: {stats['has_freshness']}/{min(20, len(symbols))}")
    print(f"  Low conviction (<0.1): {stats['low_conviction']}")
    print(f"  Low freshness (<0.5): {stats['low_freshness']}")
    print(f"  Missing expanded_intel: {stats['missing_expanded_intel']}")
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} issues (showing first 10):")
        for issue in issues[:10]:
            print(f"  - {issue}")

def check_weights():
    """Check weight configuration."""
    print("\n" + "=" * 80)
    print("CHECKING WEIGHT CONFIGURATION")
    print("=" * 80)
    
    try:
        from uw_composite_v2 import WEIGHTS_V3, get_weight
        
        print(f"\nWEIGHTS_V3 contains {len(WEIGHTS_V3)} components:")
        total_weight = sum(abs(w) for w in WEIGHTS_V3.values())
        print(f"Total absolute weight: {total_weight:.3f}")
        
        print("\nAll weights:")
        for comp, weight in sorted(WEIGHTS_V3.items(), key=lambda x: abs(x[1]), reverse=True):
            print(f"  {comp:25s}: {weight:7.3f}")
        
        # Test get_weight function
        print("\nTesting get_weight function:")
        regimes = ["RISK_ON", "RISK_OFF", "NEUTRAL", "mixed"]
        for regime in regimes:
            flow_weight = get_weight("options_flow", regime)
            print(f"  options_flow in {regime}: {flow_weight:.3f}")
        
    except Exception as e:
        print(f"❌ Error checking weights: {e}")
        import traceback
        traceback.print_exc()

def check_recent_scores():
    """Check recent scores from logs."""
    print("\n" + "=" * 80)
    print("CHECKING RECENT SCORES FROM LOGS")
    print("=" * 80)
    
    log_path = Path("logs/trading.log")
    if not log_path.exists():
        print("❌ Trading log not found")
        return
    
    try:
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        # Look for score patterns
        score_lines = []
        for line in lines[-500:]:  # Last 500 lines
            if "composite_score" in line.lower() or "score=" in line.lower():
                score_lines.append(line.strip())
        
        print(f"\nFound {len(score_lines)} score-related log lines (last 10):")
        for line in score_lines[-10:]:
            print(f"  {line[:150]}")
        
        # Try to extract actual scores
        scores = []
        for line in score_lines:
            # Look for patterns like "score=0.45" or "score: 0.45"
            import re
            matches = re.findall(r'score[=:]\s*([0-9.]+)', line, re.IGNORECASE)
            for match in matches:
                try:
                    scores.append(float(match))
                except:
                    pass
        
        if scores:
            print(f"\nExtracted {len(scores)} scores:")
            print(f"  Min: {min(scores):.3f}")
            print(f"  Max: {max(scores):.3f}")
            print(f"  Avg: {sum(scores)/len(scores):.3f}")
            print(f"  Last 5: {[f'{s:.3f}' for s in scores[-5:]]}")
        else:
            print("\n⚠️  Could not extract numeric scores from logs")
            
    except Exception as e:
        print(f"❌ Error reading logs: {e}")

def main():
    print("=" * 80)
    print("COMPREHENSIVE SCORE DIAGNOSTIC")
    print("=" * 80)
    print(f"Run at: {datetime.now().isoformat()}")
    
    # Run all diagnostics
    analyze_signal_data()
    check_weights()
    test_composite_scoring()
    check_recent_scores()
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
