#!/usr/bin/env python3
"""
Statistical Significance Audit - Are we making decisions on noise?

This script answers:
1. Do we have enough data for reliable patterns?
2. Are we at risk of overfitting?
3. What's the statistical significance of our findings?
4. Should we adjust weights or wait for more data?
5. What's the reasoning behind the patterns we see?

Key Principles:
- Small sample sizes = high variance = unreliable patterns
- Overfitting = adjusting to noise, not signal
- Whipsaw = constantly changing weights based on small samples
- Statistical significance = patterns that are likely real, not random
"""

import json
from pathlib import Path
from collections import defaultdict
import math
from datetime import datetime, timezone

LOGS_DIR = Path("logs")
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"
BLOCKED_TRADES_LOG = Path("state/blocked_trades.jsonl")
UW_ATTRIBUTION_LOG = Path("data/uw_attribution.jsonl")

def calculate_confidence_interval(successes, total, confidence=0.95):
    """Calculate confidence interval for a proportion"""
    if total == 0:
        return (0.0, 0.0, 0.0)
    
    p = successes / total
    z = 1.96  # 95% confidence
    margin = z * math.sqrt((p * (1 - p)) / total)
    lower = max(0.0, p - margin)
    upper = min(1.0, p + margin)
    return (p, lower, upper)

def calculate_minimum_sample_size(expected_win_rate, margin_of_error=0.05):
    """Calculate minimum sample size needed for reliable estimates"""
    z = 1.96  # 95% confidence
    p = expected_win_rate
    n = (z ** 2 * p * (1 - p)) / (margin_of_error ** 2)
    return int(math.ceil(n))

def assess_statistical_significance(wins, total, baseline=0.5):
    """Assess if a win rate is statistically significantly different from baseline"""
    if total < 30:
        return {
            "significant": False,
            "reason": "Sample size too small (need at least 30 for basic significance)",
            "sample_size": total,
            "minimum_needed": 30
        }
    
    p = wins / total
    z = (p - baseline) / math.sqrt((baseline * (1 - baseline)) / total)
    
    # Two-tailed test, 95% confidence
    is_significant = abs(z) > 1.96
    
    return {
        "significant": is_significant,
        "z_score": z,
        "win_rate": p,
        "sample_size": total,
        "baseline": baseline,
        "interpretation": "Statistically significant" if is_significant else "Not statistically significant - could be random variation"
    }

def analyze_data_quality():
    """Check if we're actually capturing all the data we need"""
    print("="*80)
    print("DATA QUALITY AUDIT")
    print("="*80)
    
    issues = []
    
    # Check attribution log
    if ATTRIBUTION_LOG.exists():
        with ATTRIBUTION_LOG.open("r") as f:
            lines = [l for l in f if l.strip()]
        print(f"\n✓ Attribution log exists: {len(lines)} records")
    else:
        issues.append("❌ Attribution log missing")
        print("\n❌ Attribution log missing")
    
    # Check blocked trades
    if BLOCKED_TRADES_LOG.exists():
        with BLOCKED_TRADES_LOG.open("r") as f:
            lines = [l for l in f if l.strip()]
        if lines:
            print(f"✓ Blocked trades log exists: {len(lines)} records")
        else:
            issues.append("⚠️  Blocked trades log is empty - not capturing blocked signals")
            print(f"⚠️  Blocked trades log exists but is EMPTY - not capturing blocked signals")
    else:
        issues.append("❌ Blocked trades log missing")
        print("❌ Blocked trades log missing")
    
    # Check UW attribution
    if UW_ATTRIBUTION_LOG.exists():
        with UW_ATTRIBUTION_LOG.open("r") as f:
            lines = [l for l in f if l.strip()]
        blocked_count = 0
        for line in lines:
            try:
                rec = json.loads(line)
                if rec.get("decision", "").upper() in ["REJECTED", "BLOCKED"]:
                    blocked_count += 1
            except:
                pass
        if blocked_count > 0:
            print(f"✓ UW attribution log exists: {len(lines)} records, {blocked_count} blocked")
        else:
            issues.append("⚠️  UW attribution log has no blocked entries")
            print(f"⚠️  UW attribution log exists: {len(lines)} records, but NO BLOCKED ENTRIES")
    else:
        issues.append("❌ UW attribution log missing")
        print("❌ UW attribution log missing")
    
    if issues:
        print("\n" + "="*80)
        print("DATA CAPTURE ISSUES FOUND:")
        print("="*80)
        for issue in issues:
            print(f"  {issue}")
        print("\n⚠️  CRITICAL: We can't analyze what we're not capturing!")
        print("   Need to fix logging before we can do meaningful analysis.")
    
    return len(issues) == 0

def analyze_trade_statistics():
    """Analyze if we have enough data for reliable patterns"""
    print("\n" + "="*80)
    print("STATISTICAL SIGNIFICANCE ANALYSIS")
    print("="*80)
    
    if not ATTRIBUTION_LOG.exists():
        print("\n❌ No attribution data to analyze")
        return
    
    trades = []
    with ATTRIBUTION_LOG.open("r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                trade = json.loads(line)
                if trade.get("type") != "attribution":
                    continue
                trade_id = trade.get("trade_id", "")
                if not trade_id or trade_id.startswith("open_"):
                    continue
                
                pnl_usd = trade.get("pnl_usd", 0.0)
                pnl_pct = trade.get("pnl_pct", 0.0)
                win = pnl_usd > 0 or pnl_pct > 0
                trades.append({
                    "win": win,
                    "pnl_pct": pnl_pct,
                    "symbol": trade.get("symbol", ""),
                })
            except:
                continue
    
    total = len(trades)
    if total == 0:
        print("\n❌ No closed trades to analyze")
        return
    
    wins = sum(1 for t in trades if t["win"])
    win_rate = wins / total
    
    print(f"\nTrade Statistics:")
    print(f"  Total trades: {total}")
    print(f"  Wins: {wins}")
    print(f"  Win rate: {win_rate*100:.1f}%")
    
    # Statistical significance check
    sig_check = assess_statistical_significance(wins, total, baseline=0.5)
    print(f"\nStatistical Significance Check (vs 50% baseline):")
    print(f"  Sample size: {sig_check['sample_size']}")
    print(f"  Win rate: {sig_check['win_rate']*100:.1f}%")
    print(f"  Z-score: {sig_check['z_score']:.2f}")
    print(f"  Result: {sig_check['interpretation']}")
    
    if not sig_check["significant"]:
        print(f"\n  ⚠️  WARNING: Win rate difference is NOT statistically significant")
        print(f"     This could be random variation, not a real pattern")
        print(f"     Minimum sample size needed: {sig_check.get('minimum_needed', 30)}")
    
    # Confidence interval
    p, lower, upper = calculate_confidence_interval(wins, total)
    print(f"\n95% Confidence Interval:")
    print(f"  Win rate: {p*100:.1f}%")
    print(f"  Range: {lower*100:.1f}% to {upper*100:.1f}%")
    print(f"  Margin of error: ±{(upper-lower)/2*100:.1f}%")
    
    if (upper - lower) > 0.2:
        margin = (upper - lower) * 100
        print(f"\n  ⚠️  WARNING: Wide confidence interval ({margin:.1f}%)")
        print(f"     This means we're very uncertain about the true win rate")
        print(f"     Need more data to narrow the range")
    
    # Minimum sample size calculation
    min_samples = calculate_minimum_sample_size(win_rate, margin_of_error=0.05)
    print(f"\nMinimum Sample Size Needed:")
    print(f"  For ±5% margin of error: {min_samples} trades")
    print(f"  Current: {total} trades")
    print(f"  Need: {max(0, min_samples - total)} more trades")
    
    if total < min_samples:
        print(f"\n  ⚠️  WARNING: Sample size is too small for reliable estimates")
        print(f"     Adjusting weights now risks overfitting to noise")
    
    # Symbol-level analysis
    print("\n" + "="*80)
    print("SYMBOL-LEVEL STATISTICAL SIGNIFICANCE")
    print("="*80)
    
    symbol_stats = defaultdict(lambda: {"wins": 0, "total": 0})
    for t in trades:
        symbol_stats[t["symbol"]]["total"] += 1
        if t["win"]:
            symbol_stats[t["symbol"]]["wins"] += 1
    
    print("\nSymbol Performance (with significance checks):")
    for symbol in sorted(symbol_stats.keys(), key=lambda s: symbol_stats[s]["total"], reverse=True)[:10]:
        stats = symbol_stats[symbol]
        if stats["total"] < 5:
            continue  # Skip symbols with too few trades
        
        sig_check = assess_statistical_significance(stats["wins"], stats["total"], baseline=0.5)
        win_rate = stats["wins"] / stats["total"]
        
        significance_marker = "✓" if sig_check["significant"] else "⚠️"
        print(f"  {significance_marker} {symbol}: {win_rate*100:.1f}% ({stats['wins']}W/{stats['total']}L)")
        if not sig_check["significant"]:
            print(f"      ⚠️  Not statistically significant (sample too small)")
    
    return {
        "total_trades": total,
        "win_rate": win_rate,
        "statistically_significant": sig_check["significant"],
        "min_samples_needed": min_samples,
        "has_enough_data": total >= min_samples
    }

def analyze_overfitting_risk():
    """Assess risk of overfitting"""
    print("\n" + "="*80)
    print("OVERFITTING RISK ASSESSMENT")
    print("="*80)
    
    # Load current weights
    weight_file = Path("state/signal_weights.json")
    if not weight_file.exists():
        print("\n⚠️  No weight file found - cannot assess overfitting risk")
        return
    
    with weight_file.open("r") as f:
        weights = json.load(f)
    
    weight_bands = weights.get("weight_bands", {})
    if not weight_bands:
        print("\n⚠️  No weight bands found - cannot assess overfitting risk")
        return
    
    print("\nWeight Adjustment Analysis:")
    overfitting_risks = []
    
    for component, band in weight_bands.items():
        current = band.get("current", 1.0)
        neutral = band.get("neutral", 1.0)
        adjustment = abs(current - neutral) / neutral if neutral > 0 else 0
        
        if adjustment > 0.3:  # More than 30% adjustment
            overfitting_risks.append({
                "component": component,
                "adjustment": adjustment,
                "current": current,
                "neutral": neutral
            })
    
    if overfitting_risks:
        print("\n⚠️  LARGE WEIGHT ADJUSTMENTS DETECTED:")
        for risk in sorted(overfitting_risks, key=lambda x: x["adjustment"], reverse=True):
            print(f"  {risk['component']}: {risk['neutral']:.2f} → {risk['current']:.2f} ({risk['adjustment']*100:.0f}% change)")
        
        print("\n  ⚠️  RISK: Large adjustments on small samples = overfitting")
        print("     If sample size is small, these adjustments may be to noise, not signal")
        print("     This can cause whipsaw (constantly changing weights)")
    else:
        print("\n✓ Weight adjustments are conservative (all < 30%)")
    
    return len(overfitting_risks) > 0

def provide_recommendations(stats_result, overfitting_risk):
    """Provide actionable recommendations"""
    print("\n" + "="*80)
    print("RECOMMENDATIONS & REASONING")
    print("="*80)
    
    print("\n1. DATA QUALITY:")
    if not stats_result or stats_result.get("total_trades", 0) < 30:
        print("   ❌ CRITICAL: Not enough data for reliable analysis")
        print("      - Need at least 30 trades for basic statistical significance")
        print("      - Current: {} trades".format(stats_result.get("total_trades", 0) if stats_result else 0))
        print("      - Recommendation: Continue trading, don't adjust weights yet")
    else:
        print("   ✓ Have minimum data for basic analysis")
    
    print("\n2. STATISTICAL SIGNIFICANCE:")
    if stats_result and not stats_result.get("statistically_significant", False):
        print("   ⚠️  Win rate differences are NOT statistically significant")
        print("      - Patterns could be random variation, not real")
        print("      - Recommendation: Wait for more data before making adjustments")
    elif stats_result and stats_result.get("statistically_significant", False):
        print("   ✓ Patterns are statistically significant")
        print("      - Can make adjustments with confidence")
    
    print("\n3. OVERFITTING RISK:")
    if overfitting_risk:
        print("   ⚠️  HIGH RISK: Large weight adjustments detected")
        print("      - Risk of overfitting to noise")
        print("      - Risk of whipsaw (constantly changing weights)")
        print("      - Recommendation: Use smaller adjustment factors, wait for more data")
    else:
        print("   ✓ Low overfitting risk (conservative adjustments)")
    
    print("\n4. REASONING BEHIND PATTERNS:")
    print("   ⚠️  CRITICAL: We need to understand WHY patterns exist")
    print("      - Not just 'SPY wins 62.5%' but 'WHY does SPY win more?'")
    print("      - Is it market regime? Time of day? Component combinations?")
    print("      - Without understanding WHY, we risk overfitting to spurious correlations")
    print("      - Recommendation: Use causal_analysis_engine.py to understand WHY")
    
    print("\n5. WHIPSAW PREVENTION:")
    print("   ⚠️  If we adjust weights on every small sample, we'll whipsaw")
    print("      - Solution: Only adjust when statistically significant AND")
    print("      - Solution: Use Bayesian priors to prevent extreme adjustments")
    print("      - Solution: Require minimum sample sizes before adjusting")
    print("      - Current system should have these safeguards - verify they're working")
    
    print("\n6. WHAT THIS ALL MEANS:")
    print("   - Numbers alone aren't enough - need statistical significance")
    print("   - Small samples = high variance = unreliable patterns")
    print("   - Overfitting = adjusting to noise, not signal")
    print("   - Whipsaw = constantly changing based on small samples")
    print("   - Need to understand WHY patterns exist, not just that they exist")
    print("   - More data = more reliable patterns = better decisions")

if __name__ == "__main__":
    print("="*80)
    print("STATISTICAL SIGNIFICANCE AUDIT")
    print("Are we making decisions on noise or signal?")
    print("="*80)
    
    # 1. Data quality check
    data_quality_ok = analyze_data_quality()
    
    # 2. Statistical significance analysis
    stats_result = analyze_trade_statistics()
    
    # 3. Overfitting risk assessment
    overfitting_risk = analyze_overfitting_risk()
    
    # 4. Recommendations
    provide_recommendations(stats_result, overfitting_risk)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if not data_quality_ok:
        print("\n❌ DATA QUALITY ISSUES: Fix logging before analysis")
    elif stats_result and not stats_result.get("has_enough_data", False):
        print("\n⚠️  NEED MORE DATA: Current sample too small for reliable patterns")
        print("   Recommendation: Continue trading, don't adjust weights yet")
    elif overfitting_risk:
        print("\n⚠️  OVERFITTING RISK: Large adjustments on potentially small samples")
        print("   Recommendation: Use more conservative adjustment factors")
    else:
        print("\n✓ Data quality OK, have enough data, low overfitting risk")
        print("   Can proceed with analysis and adjustments")
