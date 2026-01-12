#!/usr/bin/env python3
"""
Investigate why scores are coming in so low.
This script will be run on the droplet to diagnose the issue.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

def load_cache() -> Dict:
    """Load the UW flow cache."""
    cache_path = Path("data/uw_flow_cache.json")
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR loading cache: {e}")
        return {}

def load_recent_logs(log_file: str = "logs/trading.log", lines: int = 100) -> List[str]:
    """Load recent log lines."""
    log_path = Path(log_file)
    if not log_path.exists():
        return []
    try:
        with open(log_path, 'r') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except Exception as e:
        print(f"ERROR loading logs: {e}")
        return []

def analyze_signal_data(symbol: str, data: Dict) -> Dict:
    """Analyze signal data for a symbol."""
    result = {
        "symbol": symbol,
        "has_flow": "sentiment" in data and "conviction" in data,
        "flow_sentiment": data.get("sentiment", "MISSING"),
        "flow_conviction": data.get("conviction", 0.0),
        "has_dark_pool": "dark_pool" in data,
        "dark_pool_sentiment": data.get("dark_pool", {}).get("sentiment", "MISSING") if isinstance(data.get("dark_pool"), dict) else "MISSING",
        "dark_pool_premium": data.get("dark_pool", {}).get("total_premium", 0.0) if isinstance(data.get("dark_pool"), dict) else 0.0,
        "has_insider": "insider" in data,
        "insider_sentiment": data.get("insider", {}).get("sentiment", "MISSING") if isinstance(data.get("insider"), dict) else "MISSING",
        "has_iv_skew": "iv_term_skew" in data,
        "iv_skew_value": data.get("iv_term_skew", 0.0),
        "has_smile_slope": "smile_slope" in data,
        "smile_slope_value": data.get("smile_slope", 0.0),
        "has_freshness": "freshness" in data,
        "freshness_value": data.get("freshness", 1.0),
        "has_expanded_intel": "expanded_intel" in data,
        "has_greeks": "greeks" in data,
        "has_shorts": "shorts" in data or "ftd" in data,
        "has_congress": "congress" in data,
        "has_calendar": "calendar" in data,
    }
    return result

def find_recent_scores() -> List[Dict]:
    """Find recent score calculations from logs."""
    logs = load_recent_logs("logs/trading.log", 500)
    scores = []
    
    for line in logs:
        if "composite_score" in line.lower() or "score=" in line.lower():
            # Try to extract score information
            if "score=" in line:
                try:
                    # Look for patterns like "score=0.45" or "composite_score: 0.45"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "score=" in part or "score:" in part:
                            score_str = part.split("=")[-1] if "=" in part else part.split(":")[-1]
                            score_val = float(score_str.strip())
                            scores.append({
                                "line": line.strip(),
                                "score": score_val,
                                "timestamp": line[:19] if len(line) > 19 else "unknown"
                            })
                            break
                except:
                    pass
    
    return scores[-20:]  # Last 20 scores

def main():
    print("=" * 80)
    print("LOW SCORES INVESTIGATION")
    print("=" * 80)
    print()
    
    # Load cache
    print("1. Loading UW Flow Cache...")
    cache = load_cache()
    print(f"   Cache contains {len([k for k in cache.keys() if not k.startswith('_')])} symbols")
    print()
    
    # Analyze top symbols
    print("2. Analyzing Signal Data for Top Symbols...")
    symbols_to_check = ["AAPL", "MSFT", "NVDA", "TSLA", "SPY", "QQQ", "META", "GOOGL"]
    signal_analysis = []
    
    for symbol in symbols_to_check:
        if symbol in cache:
            data = cache[symbol]
            if isinstance(data, dict):
                analysis = analyze_signal_data(symbol, data)
                signal_analysis.append(analysis)
    
    # Print analysis
    for analysis in signal_analysis[:10]:
        print(f"\n   {analysis['symbol']}:")
        print(f"      Flow: {analysis['flow_sentiment']} (conv={analysis['flow_conviction']:.3f})")
        print(f"      Dark Pool: {analysis['dark_pool_sentiment']} (premium={analysis['dark_pool_premium']:.0f})")
        print(f"      Insider: {analysis['insider_sentiment']}")
        print(f"      IV Skew: {analysis['iv_skew_value']:.4f}")
        print(f"      Smile Slope: {analysis['smile_slope_value']:.4f}")
        print(f"      Freshness: {analysis['freshness_value']:.3f}")
        print(f"      Has Expanded Intel: {analysis['has_expanded_intel']}")
        print(f"      Has Greeks: {analysis['has_greeks']}")
        print(f"      Has Shorts: {analysis['has_shorts']}")
    
    print()
    
    # Check recent scores from logs
    print("3. Checking Recent Scores from Logs...")
    recent_scores = find_recent_scores()
    if recent_scores:
        print(f"   Found {len(recent_scores)} recent scores:")
        for score_info in recent_scores[-10:]:
            print(f"      Score: {score_info['score']:.3f} - {score_info['timestamp']}")
        avg_score = sum(s['score'] for s in recent_scores) / len(recent_scores) if recent_scores else 0
        print(f"   Average score: {avg_score:.3f}")
    else:
        print("   No recent scores found in logs")
    
    print()
    
    # Check for component breakdowns
    print("4. Searching for Component Breakdowns in Logs...")
    logs = load_recent_logs("logs/trading.log", 200)
    component_lines = [line for line in logs if "components" in line.lower() or "flow_component" in line.lower()]
    if component_lines:
        print(f"   Found {len(component_lines)} component-related log lines:")
        for line in component_lines[-5:]:
            print(f"      {line.strip()[:100]}")
    else:
        print("   No component breakdowns found")
    
    print()
    
    # Check if composite scoring is being called
    print("5. Checking if Composite Scoring is Active...")
    logs = load_recent_logs("logs/trading.log", 100)
    composite_calls = [line for line in logs if "compute_composite_score" in line.lower() or "composite_v3" in line.lower()]
    if composite_calls:
        print(f"   Found {len(composite_calls)} composite scoring calls")
        print(f"   Last call: {composite_calls[-1].strip()[:150]}")
    else:
        print("   ⚠️  WARNING: No composite scoring calls found!")
    
    print()
    
    # Check weights
    print("6. Checking Weight Configuration...")
    try:
        from uw_composite_v2 import WEIGHTS_V3
        print(f"   Loaded WEIGHTS_V3 with {len(WEIGHTS_V3)} components:")
        for comp, weight in sorted(WEIGHTS_V3.items(), key=lambda x: abs(x[1]), reverse=True)[:10]:
            print(f"      {comp}: {weight:.3f}")
    except Exception as e:
        print(f"   ERROR loading weights: {e}")
    
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    # Check for common issues
    issues = []
    
    if not signal_analysis:
        issues.append("❌ No signal data found in cache")
    else:
        missing_flow = sum(1 for a in signal_analysis if not a['has_flow'])
        if missing_flow > 0:
            issues.append(f"⚠️  {missing_flow} symbols missing flow data")
        
        low_conviction = sum(1 for a in signal_analysis if a['flow_conviction'] < 0.1)
        if low_conviction > 0:
            issues.append(f"⚠️  {low_conviction} symbols have very low conviction (<0.1)")
        
        low_freshness = sum(1 for a in signal_analysis if a['freshness_value'] < 0.5)
        if low_freshness > 0:
            issues.append(f"⚠️  {low_freshness} symbols have low freshness (<0.5)")
    
    if recent_scores:
        avg_score = sum(s['score'] for s in recent_scores) / len(recent_scores)
        if avg_score < 1.0:
            issues.append(f"❌ Average score is very low: {avg_score:.3f}")
        if avg_score < 2.0:
            issues.append(f"⚠️  Average score is below threshold: {avg_score:.3f}")
    
    if not composite_calls:
        issues.append("❌ Composite scoring may not be running!")
    
    if issues:
        print("\nISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ No obvious issues found - need deeper investigation")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
