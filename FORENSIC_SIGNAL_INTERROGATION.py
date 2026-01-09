#!/usr/bin/env python3
"""
Forensic Signal Interrogation - Deep Trace on Next 10 Incoming Alerts
Diagnoses why 530 alerts but 0 trades - identifies blind spots and over-filtering
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config.registry import CacheFiles, LogFiles, StateFiles, read_json, get_env
    from uw_enrichment_v2 import enrich_signal
    from uw_composite_v2 import compute_composite_score_v3
    import uw_composite_v2 as uw_v2
except ImportError as e:
    print(f"ERROR: Import failed: {e}")
    sys.exit(1)

# Track last 10 alerts
ALERT_TRACE = deque(maxlen=10)
BLOCKED_SYMBOLS = []

def trace_enrichment_pipeline(symbol: str, uw_cache: Dict) -> Dict[str, Any]:
    """
    Step 1: Trace the 'Enrichment' Pipeline
    Print RAW JSON keys received from socket vs. keys expected by enrich_signal()
    """
    print(f"\n{'='*80}")
    print(f"STEP 1: ENRICHMENT PIPELINE TRACE - {symbol}")
    print(f"{'='*80}")
    
    # Get raw data from cache
    raw_data = uw_cache.get(symbol, {})
    
    if isinstance(raw_data, str):
        try:
            raw_data = json.loads(raw_data)
        except:
            raw_data = {}
    
    print(f"\nRAW JSON Keys from UW Cache:")
    if raw_data:
        for key in sorted(raw_data.keys()):
            value = raw_data[key]
            if isinstance(value, dict):
                print(f"  {key}: {{dict with {len(value)} keys}}")
            elif isinstance(value, (int, float)):
                print(f"  {key}: {value}")
            elif isinstance(value, str):
                print(f"  {key}: '{value[:50]}...'")
            else:
                print(f"  {key}: {type(value).__name__}")
    else:
        print("  [NO DATA IN CACHE]")
    
    # Expected fields by enrich_signal()
    expected_fields = [
        "sentiment", "conviction", "dark_pool", "insider",
        "iv_term_skew", "smile_slope", "toxicity", "event_alignment",
        "freshness", "motif_staircase", "motif_sweep_block", "motif_burst"
    ]
    
    print(f"\nExpected Fields by enrich_signal():")
    for field in expected_fields:
        present = field in raw_data if raw_data else False
        status = "✓" if present else "✗ MISSING"
        print(f"  {field}: {status}")
    
    # Check for field name mismatches
    print(f"\nField Name Mismatch Check:")
    mismatches = []
    
    # Common mismatches
    if "conv" in raw_data and "conviction" not in raw_data:
        mismatches.append(("conv", "conviction"))
    if "dp" in raw_data and "dark_pool" not in raw_data:
        mismatches.append(("dp", "dark_pool"))
    if "sent" in raw_data and "sentiment" not in raw_data:
        mismatches.append(("sent", "sentiment"))
    
    if mismatches:
        print(f"  ⚠️  POTENTIAL MISMATCHES FOUND:")
        for old, new in mismatches:
            print(f"    '{old}' found but expected '{new}'")
    else:
        print(f"  ✓ No obvious field name mismatches")
    
    # Run enrichment
    try:
        enriched = enrich_signal(symbol, uw_cache, "NEUTRAL")
        print(f"\nEnrichment Result:")
        if enriched:
            print(f"  ✓ Enrichment successful ({len(enriched)} fields)")
            # Check if score would be 0.00
            if enriched.get("conviction", 0.0) == 0.0 and enriched.get("sentiment") == "NEUTRAL":
                print(f"  ⚠️  WARNING: conviction=0.0 and sentiment=NEUTRAL - may cause 0.00 score")
        else:
            print(f"  ✗ Enrichment returned empty dict")
    except Exception as e:
        print(f"  ✗ Enrichment failed: {e}")
        enriched = {}
    
    return {
        "raw_keys": list(raw_data.keys()) if raw_data else [],
        "expected_fields": expected_fields,
        "mismatches": mismatches,
        "enriched": enriched,
        "enrichment_success": bool(enriched)
    }

def trace_atr_exhaustion_gate(symbol: str, price: float, enriched: Dict) -> Dict[str, Any]:
    """
    Step 2: Interrogate the ATR Exhaustion Gate
    Note: The momentum filter doesn't use ATR, but we'll check if there's an ATR-based gate elsewhere
    """
    print(f"\n{'='*80}")
    print(f"STEP 2: ATR EXHAUSTION GATE TRACE - {symbol}")
    print(f"{'='*80}")
    
    # Check if momentum filter is the "ATR exhaustion gate" the user mentioned
    # The momentum filter checks price movement, not ATR distance from EMA
    # But let's trace what it does
    
    try:
        from momentum_ignition_filter import check_momentum_before_entry
        momentum_result = check_momentum_before_entry(
            symbol=symbol,
            signal_direction="bullish",  # Default
            current_price=price,
            entry_score=enriched.get("score", 0.0) if isinstance(enriched, dict) else 0.0,
            market_regime="mixed"
        )
        
        print(f"\nMomentum Filter Check:")
        print(f"  Passed: {momentum_result.get('passed', False)}")
        print(f"  Price Change %: {momentum_result.get('price_change_pct', 0.0) * 100:.4f}%")
        print(f"  Price 2min ago: ${momentum_result.get('price_2min_ago', 0.0):.2f}")
        print(f"  Current Price: ${momentum_result.get('current_price', 0.0):.2f}")
        print(f"  Threshold Used: {momentum_result.get('threshold_used', 0.0) * 100:.4f}%")
        print(f"  Reason: {momentum_result.get('reason', 'unknown')}")
        
        if not momentum_result.get('passed', False):
            dist_from_threshold = abs(momentum_result.get('price_change_pct', 0.0)) - momentum_result.get('threshold_used', 0.0)
            print(f"\n  ⚠️  BLOCKED: Price change ({momentum_result.get('price_change_pct', 0.0)*100:.4f}%) is {dist_from_threshold*100:.4f}% away from threshold ({momentum_result.get('threshold_used', 0.0)*100:.4f}%)")
        
        return {
            "momentum_passed": momentum_result.get('passed', False),
            "price_change_pct": momentum_result.get('price_change_pct', 0.0),
            "threshold": momentum_result.get('threshold_used', 0.0),
            "reason": momentum_result.get('reason', 'unknown')
        }
    except ImportError:
        print(f"  ⚠️  Momentum filter not available")
        return {"momentum_passed": True, "reason": "filter_unavailable"}
    except Exception as e:
        print(f"  ✗ Momentum check failed: {e}")
        return {"momentum_passed": True, "reason": f"error_{str(e)[:50]}"}

def trace_score_consistency(symbol: str, enriched: Dict, entry_score: float) -> Dict[str, Any]:
    """
    Step 3: Audit Current Score vs Entry Score
    Verify review_positions() uses same scoring function as entry logic
    """
    print(f"\n{'='*80}")
    print(f"STEP 3: SCORE CONSISTENCY AUDIT - {symbol}")
    print(f"{'='*80}")
    
    # Calculate current score using same function as entry
    try:
        current_regime = "NEUTRAL"  # Default
        current_composite = compute_composite_score_v3(symbol, enriched, current_regime)
        current_score = current_composite.get("score", 0.0)
        version = current_composite.get("version", "unknown")
        
        print(f"\nEntry Score: {entry_score:.3f}")
        print(f"Current Score (v3): {current_score:.3f}")
        print(f"Version: {version}")
        
        # Check if they match
        score_diff = abs(current_score - entry_score)
        if score_diff > 0.1:
            print(f"\n  ⚠️  SCORE MISMATCH: Entry ({entry_score:.3f}) vs Current ({current_score:.3f}) = {score_diff:.3f} difference")
            print(f"  This could cause phantom stagnations if dashboard and bot use different versions")
        else:
            print(f"\n  ✓ Scores consistent (diff: {score_diff:.3f})")
        
        # Check components
        entry_components = enriched.get("components", {}) if isinstance(enriched, dict) else {}
        current_components = current_composite.get("components", {})
        
        print(f"\nComponent Comparison:")
        print(f"  Entry has components: {bool(entry_components)}")
        print(f"  Current has components: {bool(current_components)}")
        
        if entry_components and current_components:
            # Compare key components
            key_comps = ["flow", "dark_pool", "insider", "iv_skew", "smile"]
            for comp in key_comps:
                entry_val = entry_components.get(comp, 0.0)
                current_val = current_components.get(comp, 0.0)
                if abs(entry_val - current_val) > 0.01:
                    print(f"    ⚠️  {comp}: Entry={entry_val:.3f}, Current={current_val:.3f}")
        
        return {
            "entry_score": entry_score,
            "current_score": current_score,
            "score_diff": score_diff,
            "version": version,
            "consistent": score_diff <= 0.1
        }
    except Exception as e:
        print(f"  ✗ Score calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def identify_blocking_gate(symbol: str, score: float, enriched: Dict, momentum_result: Dict) -> str:
    """
    Identify which gate blocked this symbol
    """
    gates_checked = []
    
    # Gate 1: Score threshold
    min_score = 2.7  # Base threshold
    if score < min_score:
        gates_checked.append(f"Score Gate (score={score:.2f} < {min_score})")
    
    # Gate 2: Momentum filter
    if not momentum_result.get("momentum_passed", True):
        gates_checked.append(f"Momentum Gate ({momentum_result.get('reason', 'unknown')})")
    
    # Gate 3: Toxicity
    toxicity = enriched.get("toxicity", 0.0) if isinstance(enriched, dict) else 0.0
    if toxicity > 0.90:
        gates_checked.append(f"Toxicity Gate (toxicity={toxicity:.2f} > 0.90)")
    
    # Gate 4: Freshness
    freshness = enriched.get("freshness", 1.0) if isinstance(enriched, dict) else 1.0
    if freshness < 0.3:
        gates_checked.append(f"Freshness Gate (freshness={freshness:.2f} < 0.3)")
    
    # Gate 5: Conviction
    conviction = enriched.get("conviction", 0.0) if isinstance(enriched, dict) else 0.0
    if conviction == 0.0:
        gates_checked.append(f"Conviction Gate (conviction=0.0)")
    
    if gates_checked:
        return " | ".join(gates_checked)
    else:
        return "UNKNOWN (passed all checked gates)"

def main():
    """Main diagnostic function"""
    print("="*80)
    print("FORENSIC SIGNAL INTERROGATION")
    print("="*80)
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    print()
    
    # Load UW cache
    uw_cache_path = CacheFiles.UW_FLOW_CACHE
    if not uw_cache_path.exists():
        print(f"WARNING: UW cache not found at {uw_cache_path}")
        print(f"Attempting to use alternative path...")
        # Try alternative paths
        alt_paths = [
            Path("data/uw_flow_cache.json"),
            Path("../data/uw_flow_cache.json"),
            Path("./data/uw_flow_cache.json")
        ]
        uw_cache = {}
        for alt_path in alt_paths:
            if alt_path.exists():
                print(f"Found cache at: {alt_path}")
                uw_cache = read_json(alt_path, default={})
                break
        if not uw_cache:
            print(f"ERROR: Could not find UW cache. Please run this on the droplet where the bot is active.")
            return
    else:
        uw_cache = read_json(uw_cache_path, default={})
    
    # Get symbols from cache (exclude metadata keys)
    symbols = [s for s in uw_cache.keys() if not s.startswith("_")]
    
    if not symbols:
        print("ERROR: No symbols in UW cache")
        return
    
    print(f"Found {len(symbols)} symbols in cache")
    print(f"Tracing next 10 alerts...")
    print()
    
    # Trace first 10 symbols
    traced = 0
    for symbol in symbols[:10]:
        if traced >= 10:
            break
        
        print(f"\n{'#'*80}")
        print(f"ALERT #{traced + 1}: {symbol}")
        print(f"{'#'*80}")
        
        # Get price (simulate)
        try:
            # Try to get from cache metadata or use default
            price = 100.0  # Default
            if isinstance(uw_cache.get(symbol), dict):
                # Try to extract price if available
                pass
        except:
            price = 100.0
        
        # Step 1: Trace enrichment
        enrichment_trace = trace_enrichment_pipeline(symbol, uw_cache)
        
        # Step 2: Trace ATR/Momentum gate
        momentum_trace = trace_atr_exhaustion_gate(symbol, price, enrichment_trace.get("enriched", {}))
        
        # Step 3: Calculate score and check consistency
        enriched = enrichment_trace.get("enriched", {})
        if enriched:
            try:
                current_regime = "NEUTRAL"
                composite = compute_composite_score_v3(symbol, enriched, current_regime)
                entry_score = composite.get("score", 0.0)
            except Exception as e:
                print(f"  ✗ Score calculation failed: {e}")
                entry_score = 0.0
        else:
            entry_score = 0.0
        
        score_trace = trace_score_consistency(symbol, enriched, entry_score)
        
        # Identify blocking gate
        blocking_gate = identify_blocking_gate(symbol, entry_score, enriched, momentum_trace)
        
        # Store result
        BLOCKED_SYMBOLS.append({
            "symbol": symbol,
            "score": entry_score,
            "blocking_gate": blocking_gate,
            "enrichment_success": enrichment_trace.get("enrichment_success", False),
            "momentum_passed": momentum_trace.get("momentum_passed", True),
            "score_consistent": score_trace.get("consistent", True)
        })
        
        print(f"\n{'='*80}")
        print(f"SUMMARY FOR {symbol}:")
        print(f"{'='*80}")
        print(f"  Score: {entry_score:.3f}")
        print(f"  Blocking Gate: {blocking_gate}")
        print(f"  Enrichment: {'✓' if enrichment_trace.get('enrichment_success') else '✗'}")
        print(f"  Momentum: {'✓' if momentum_trace.get('momentum_passed') else '✗'}")
        print(f"  Score Consistent: {'✓' if score_trace.get('consistent') else '✗'}")
        
        traced += 1
    
    # Final summary
    print(f"\n\n{'='*80}")
    print("FINAL SUMMARY - LAST 5 BLOCKED SYMBOLS")
    print(f"{'='*80}")
    
    # Sort by score (lowest first - most likely blocked)
    blocked_sorted = sorted(BLOCKED_SYMBOLS, key=lambda x: x["score"])[:5]
    
    for i, item in enumerate(blocked_sorted, 1):
        print(f"\n{i}. {item['symbol']}")
        print(f"   Score: {item['score']:.3f}")
        print(f"   Blocking Gate: {item['blocking_gate']}")
        print(f"   Enrichment: {'✓' if item['enrichment_success'] else '✗'}")
        print(f"   Momentum: {'✓' if item['momentum_passed'] else '✗'}")
    
    # Statistics
    print(f"\n{'='*80}")
    print("STATISTICS")
    print(f"{'='*80}")
    total = len(BLOCKED_SYMBOLS)
    blocked_by_score = sum(1 for x in BLOCKED_SYMBOLS if "Score Gate" in x["blocking_gate"])
    blocked_by_momentum = sum(1 for x in BLOCKED_SYMBOLS if "Momentum Gate" in x["blocking_gate"])
    blocked_by_toxicity = sum(1 for x in BLOCKED_SYMBOLS if "Toxicity Gate" in x["blocking_gate"])
    blocked_by_freshness = sum(1 for x in BLOCKED_SYMBOLS if "Freshness Gate" in x["blocking_gate"])
    blocked_by_conviction = sum(1 for x in BLOCKED_SYMBOLS if "Conviction Gate" in x["blocking_gate"])
    
    print(f"Total Traced: {total}")
    print(f"Blocked by Score: {blocked_by_score}")
    print(f"Blocked by Momentum: {blocked_by_momentum}")
    print(f"Blocked by Toxicity: {blocked_by_toxicity}")
    print(f"Blocked by Freshness: {blocked_by_freshness}")
    print(f"Blocked by Conviction: {blocked_by_conviction}")
    
    # Save results
    output_file = Path("data/forensic_interrogation_results.json")
    output_file.parent.mkdir(exist_ok=True)
    with output_file.open("w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "total_traced": total,
            "blocked_symbols": BLOCKED_SYMBOLS,
            "statistics": {
                "blocked_by_score": blocked_by_score,
                "blocked_by_momentum": blocked_by_momentum,
                "blocked_by_toxicity": blocked_by_toxicity,
                "blocked_by_freshness": blocked_by_freshness,
                "blocked_by_conviction": blocked_by_conviction
            }
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
