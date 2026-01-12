#!/usr/bin/env python3
"""
Comprehensive Score Stagnation Investigation Script
Run this on the droplet to investigate every aspect of why scores are low.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def load_json_file(filepath: Path) -> Any:
    """Safely load JSON file."""
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def check_adaptive_weights():
    """Check adaptive weights state."""
    print_section("ADAPTIVE WEIGHTS ANALYSIS")
    
    from uw_composite_v2 import get_weight, WEIGHTS_V3
    
    weights_file = Path("state/signal_weights.json")
    weights_data = load_json_file(weights_file)
    
    print(f"\nWeights file exists: {weights_file.exists()}")
    if weights_data:
        if "error" in weights_data:
            print(f"❌ Error loading weights: {weights_data['error']}")
        else:
            print(f"✅ Loaded weights data (keys: {list(weights_data.keys())})")
            
            # Check entry_model
            if "entry_model" in weights_data:
                entry_model = weights_data["entry_model"]
                print(f"\nEntry model found:")
                if "regime_beta_distributions" in entry_model:
                    regimes = entry_model["regime_beta_distributions"]
                    print(f"  Regime distributions for {len(regimes)} components")
                    for comp, regimes_data in list(regimes.items())[:5]:
                        print(f"    {comp}: {len(regimes_data)} regimes")
                
                if "weight_bands" in entry_model:
                    bands = entry_model["weight_bands"]
                    print(f"  Weight bands for {len(bands)} components")
                    for comp, band_data in list(bands.items())[:5]:
                        current = band_data.get("current", 1.0)
                        print(f"    {comp}: multiplier={current:.3f}")
    
    # Check current effective weights
    print(f"\nCurrent Effective Weights (checking against defaults):")
    print(f"{'Component':<25} {'Default':<10} {'RISK_ON':<10} {'RISK_OFF':<10} {'NEUTRAL':<10} {'mixed':<10}")
    print("-" * 80)
    
    issues = []
    regimes_to_check = ["RISK_ON", "RISK_OFF", "NEUTRAL", "mixed"]
    
    for component in sorted(WEIGHTS_V3.keys()):
        default = WEIGHTS_V3[component]
        weights_by_regime = {}
        has_issue = False
        
        for regime in regimes_to_check:
            current = get_weight(component, regime)
            weights_by_regime[regime] = current
            # Check if weight is significantly reduced (>20% reduction)
            if current < default * 0.8:
                has_issue = True
        
        if has_issue:
            issues.append({
                "component": component,
                "default": default,
                "weights": weights_by_regime
            })
        
        # Print if there's an issue or if it's a major component
        if has_issue or component in ["options_flow", "dark_pool", "iv_term_skew", "whale_persistence"]:
            print(f"{component:<25} {default:<10.3f} ", end="")
            for regime in regimes_to_check:
                current = weights_by_regime[regime]
                diff_pct = ((current - default) / default * 100) if default > 0 else 0
                marker = "⚠️" if current < default * 0.8 else "✅"
                print(f"{marker} {current:<8.3f}", end="")
            print()
    
    if issues:
        print(f"\n⚠️  Found {len(issues)} components with reduced weights:")
        for issue in issues:
            print(f"\n  {issue['component']}:")
            print(f"    Default: {issue['default']:.3f}")
            for regime, weight in issue['weights'].items():
                diff_pct = ((weight - issue['default']) / issue['default'] * 100) if issue['default'] > 0 else 0
                if weight < issue['default'] * 0.8:
                    print(f"    {regime}: {weight:.3f} ({diff_pct:+.1f}%) ⚠️")
    else:
        print("\n✅ All weights appear to be at or near default values")

def check_stagnation_detector():
    """Check stagnation detector state."""
    print_section("STAGNATION DETECTOR STATE")
    
    state_file = Path("state/logic_stagnation_state.json")
    state = load_json_file(state_file)
    
    if state:
        if "error" in state:
            print(f"❌ Error loading state: {state['error']}")
        else:
            print(f"✅ Loaded stagnation state")
            print(f"\nKey Metrics:")
            print(f"  Zero score detections: {state.get('zero_score_detections', 0)}")
            print(f"  Momentum block detections: {state.get('momentum_block_detections', 0)}")
            print(f"  Funnel stagnation detections: {state.get('funnel_stagnation_detections', 0)}")
            print(f"  Soft reset count: {state.get('soft_reset_count', 0)}")
            
            last_reset = state.get('last_soft_reset_ts', 0)
            if last_reset > 0:
                reset_dt = datetime.fromtimestamp(last_reset)
                print(f"  Last soft reset: {reset_dt.isoformat()}")
            else:
                print(f"  Last soft reset: Never")
    else:
        print("⚠️  No stagnation state file found")
    
    # Check logs
    log_file = Path("logs/logic_stagnation.jsonl")
    if log_file.exists():
        print(f"\n📋 Recent stagnation events (last 5):")
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    event = json.loads(line.strip())
                    event_type = event.get('event', 'unknown')
                    timestamp = event.get('timestamp', 'unknown')
                    print(f"  {timestamp}: {event_type}")
        except Exception as e:
            print(f"  ❌ Error reading log: {e}")

def check_recent_scores():
    """Check recent scores from logs and cache."""
    print_section("RECENT SCORES ANALYSIS")
    
    # Load cache
    cache_file = Path("data/uw_flow_cache.json")
    cache = load_json_file(cache_file)
    
    if cache and "error" not in cache:
        symbols = [s for s in cache.keys() if not s.startswith("_")]
        print(f"✅ Loaded cache with {len(symbols)} symbols")
        
        # Test score calculation for recent symbols
        try:
            from uw_composite_v2 import compute_composite_score_v3
            from uw_enrichment_v2 import enrich_signal
            
            print(f"\nTesting scores for first 10 symbols:")
            print(f"{'Symbol':<10} {'Score':<8} {'Flow':<8} {'Fresh':<8} {'Conv':<8} {'Components':<10}")
            print("-" * 70)
            
            scores_found = []
            for symbol in symbols[:10]:
                symbol_data = cache.get(symbol, {})
                if not isinstance(symbol_data, dict):
                    continue
                
                try:
                    enriched = enrich_signal(symbol, cache, "NEUTRAL")
                    result = compute_composite_score_v3(symbol, enriched, "NEUTRAL")
                    
                    if result:
                        score = result.get('score', 0.0)
                        scores_found.append(score)
                        components = result.get('components', {})
                        flow_comp = components.get('flow_component', 0.0)
                        freshness = components.get('freshness_factor', 1.0)
                        conviction = enriched.get('conviction', 0.0)
                        comp_count = sum(1 for v in components.values() if abs(v) > 0.01)
                        
                        marker = "⚠️" if score < 1.0 else "✅" if score >= 2.7 else "⚡"
                        print(f"{marker} {symbol:<8} {score:<8.3f} {flow_comp:<8.3f} {freshness:<8.3f} {conviction:<8.3f} {comp_count:<10}")
                except Exception as e:
                    print(f"❌ {symbol}: Error - {e}")
            
            if scores_found:
                print(f"\nScore Statistics:")
                print(f"  Count: {len(scores_found)}")
                print(f"  Min: {min(scores_found):.3f}")
                print(f"  Max: {max(scores_found):.3f}")
                print(f"  Avg: {sum(scores_found)/len(scores_found):.3f}")
                print(f"  Median: {sorted(scores_found)[len(scores_found)//2]:.3f}")
                print(f"  Below 1.0: {sum(1 for s in scores_found if s < 1.0)}")
                print(f"  Below 2.7: {sum(1 for s in scores_found if s < 2.7)}")
                print(f"  Zero scores: {sum(1 for s in scores_found if s == 0.0)}")
        except ImportError as e:
            print(f"❌ Could not import scoring modules: {e}")
    else:
        print("⚠️  Could not load cache file")

def check_signal_funnel():
    """Check signal funnel metrics."""
    print_section("SIGNAL FUNNEL ANALYSIS")
    
    state_file = Path("state/signal_funnel_state.json")
    state = load_json_file(state_file)
    
    if state:
        print(f"✅ Loaded funnel state")
        print(f"\nTotal Metrics:")
        print(f"  Total alerts: {state.get('total_alerts', 0)}")
        print(f"  Total parsed: {state.get('total_parsed', 0)}")
        print(f"  Total scored: {state.get('total_scored', 0)}")
        print(f"  Total orders: {state.get('total_orders', 0)}")
        
        # Calculate conversion rates
        alerts = state.get('total_alerts', 0)
        if alerts > 0:
            parse_rate = (state.get('total_parsed', 0) / alerts) * 100
            score_rate = (state.get('total_scored', 0) / alerts) * 100
            order_rate = (state.get('total_orders', 0) / alerts) * 100
            print(f"\nConversion Rates:")
            print(f"  Alerts → Parsed: {parse_rate:.1f}%")
            print(f"  Alerts → Scored: {score_rate:.1f}%")
            print(f"  Alerts → Orders: {order_rate:.1f}%")
    
    # Try to get recent funnel metrics
    try:
        from signal_funnel_tracker import get_funnel_tracker
        funnel = get_funnel_tracker()
        metrics = funnel.get_funnel_metrics(window_sec=1800)  # 30 minutes
        
        print(f"\nLast 30 Minutes:")
        print(f"  Alerts: {metrics.get('alerts', 0)}")
        print(f"  Parsed: {metrics.get('parsed', 0)}")
        print(f"  Scored above threshold: {metrics.get('scored_above_threshold', 0)}")
        print(f"  Orders sent: {metrics.get('orders_sent', 0)}")
        
        # Check for stagnation
        stagnation = funnel.check_stagnation("mixed")
        if stagnation and stagnation.get('detected'):
            print(f"\n⚠️  STAGNATION DETECTED:")
            print(f"  Reason: {stagnation.get('reason')}")
            print(f"  Alerts (30m): {stagnation.get('alerts_30m', 0)}")
            print(f"  Orders (30m): {stagnation.get('orders_30m', 0)}")
    except Exception as e:
        print(f"⚠️  Could not load funnel tracker: {e}")

def check_component_contributions():
    """Check component contribution patterns."""
    print_section("COMPONENT CONTRIBUTION ANALYSIS")
    
    cache_file = Path("data/uw_flow_cache.json")
    cache = load_json_file(cache_file)
    
    if not cache or "error" in cache:
        print("⚠️  Could not load cache")
        return
    
    symbols = [s for s in cache.keys() if not s.startswith("_")][:20]
    
    try:
        from uw_composite_v2 import compute_composite_score_v3
        from uw_enrichment_v2 import enrich_signal
        
        component_stats = {}
        
        for symbol in symbols:
            try:
                enriched = enrich_signal(symbol, cache, "NEUTRAL")
                result = compute_composite_score_v3(symbol, enriched, "NEUTRAL")
                
                if result:
                    components = result.get('components', {})
                    for comp_name, comp_value in components.items():
                        if comp_name not in component_stats:
                            component_stats[comp_name] = {
                                "count": 0,
                                "zero_count": 0,
                                "total": 0.0,
                                "min": float('inf'),
                                "max": float('-inf')
                            }
                        
                        stats = component_stats[comp_name]
                        stats["count"] += 1
                        stats["total"] += comp_value
                        if abs(comp_value) < 0.001:
                            stats["zero_count"] += 1
                        stats["min"] = min(stats["min"], comp_value)
                        stats["max"] = max(stats["max"], comp_value)
            except:
                continue
        
        print(f"\nComponent Statistics (from {len(symbols)} symbols):")
        print(f"{'Component':<25} {'Avg':<10} {'Zero%':<10} {'Min':<10} {'Max':<10}")
        print("-" * 70)
        
        for comp_name in sorted(component_stats.keys()):
            stats = component_stats[comp_name]
            avg = stats["total"] / stats["count"] if stats["count"] > 0 else 0.0
            zero_pct = (stats["zero_count"] / stats["count"] * 100) if stats["count"] > 0 else 0.0
            
            marker = "⚠️" if zero_pct > 50 else "✅"
            print(f"{marker} {comp_name:<23} {avg:<10.3f} {zero_pct:<9.1f}% {stats['min']:<10.3f} {stats['max']:<10.3f}")
        
    except Exception as e:
        print(f"❌ Error analyzing components: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all diagnostics."""
    print("=" * 80)
    print("COMPREHENSIVE SCORE STAGNATION INVESTIGATION")
    print("=" * 80)
    print(f"Run at: {datetime.now().isoformat()}")
    print(f"Working directory: {Path.cwd()}")
    
    # Run all checks
    check_adaptive_weights()
    check_stagnation_detector()
    check_recent_scores()
    check_signal_funnel()
    check_component_contributions()
    
    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
