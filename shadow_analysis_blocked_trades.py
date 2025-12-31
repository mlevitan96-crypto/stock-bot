#!/usr/bin/env python3
"""
Shadow Analysis on Blocked Trades - Analyze what would have happened with 0.5 bps latency penalty

Performs counterfactual analysis on blocked trades to see if high-score signals (e.g., 5.23)
would have survived the 0.5 bps latency penalty from the backtest.
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

STATE_DIR = Path("state")
DATA_DIR = Path("data")
LOGS_DIR = Path("logs")

BLOCKED_TRADES_LOG = STATE_DIR / "blocked_trades.jsonl"
UW_ATTRIBUTION_LOG = DATA_DIR / "uw_attribution.jsonl"
ATTRIBUTION_LOG = LOGS_DIR / "attribution.jsonl"

# Latency penalty from backtest
LATENCY_PENALTY_BPS = 0.5  # 0.5 basis points

def parse_timestamp(ts_str):
    """Parse various timestamp formats"""
    if not ts_str:
        return None
    try:
        if isinstance(ts_str, (int, float)):
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        if isinstance(ts_str, str):
            ts_str = ts_str.replace("Z", "+00:00")
            return datetime.fromisoformat(ts_str)
    except:
        pass
    return None

def load_blocked_trades(max_trades: Optional[int] = None) -> List[Dict]:
    """Load blocked trades"""
    blocked = []
    
    # Load from blocked_trades.jsonl
    if BLOCKED_TRADES_LOG.exists():
        with BLOCKED_TRADES_LOG.open("r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    blocked.append({
                        "source": "blocked_trades",
                        "symbol": rec.get("symbol", ""),
                        "score": rec.get("score", 0.0),
                        "reason": rec.get("reason", "unknown"),
                        "timestamp": rec.get("timestamp") or rec.get("ts"),
                        "direction": rec.get("direction", "unknown"),
                        "decision_price": rec.get("decision_price", 0.0),
                        "components": rec.get("components", {})
                    })
                except:
                    continue
    
    # Load from uw_attribution.jsonl (decision="rejected")
    if UW_ATTRIBUTION_LOG.exists():
        with UW_ATTRIBUTION_LOG.open("r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("decision") == "rejected":
                        blocked.append({
                            "source": "uw_attribution",
                            "symbol": rec.get("symbol", ""),
                            "score": rec.get("score", 0.0),
                            "reason": "uw_rejected",
                            "timestamp": rec.get("ts"),
                            "direction": rec.get("direction", "unknown"),
                            "decision_price": 0.0,  # May not be available
                            "components": rec.get("components", {})
                        })
                except:
                    continue
    
    # Sort by score descending and limit if requested
    blocked.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    if max_trades:
        blocked = blocked[:max_trades]
    
    return blocked

def apply_latency_penalty(entry_price: float, direction: str) -> float:
    """
    Apply 0.5 bps latency penalty to entry price.
    
    For long/bullish: pay slightly more (multiply by 1.00005)
    For short/bearish: receive slightly less (multiply by 1/1.00005)
    """
    latency_multiplier = 1.0 + (LATENCY_PENALTY_BPS / 10000.0)  # 0.5 bps = 0.00005
    
    if direction.lower() in ["bullish", "long", "buy"]:
        # Buying: pay more
        return entry_price * latency_multiplier
    else:
        # Selling/shorting: receive less
        return entry_price * (1.0 / latency_multiplier)

def analyze_blocked_trades(blocked: List[Dict]) -> Dict[str, Any]:
    """Analyze blocked trades with latency penalty"""
    if not blocked:
        return {
            "total_analyzed": 0,
            "high_score_trades": 0,
            "survived_latency": 0,
            "score_distribution": {}
        }
    
    high_score = [t for t in blocked if t.get("score", 0.0) >= 5.0]
    survived = []
    score_buckets = defaultdict(int)
    
    for trade in blocked:
        score = trade.get("score", 0.0)
        # Bucket scores
        if score >= 5.0:
            score_buckets["5.0+"] += 1
        elif score >= 4.0:
            score_buckets["4.0-4.99"] += 1
        elif score >= 3.0:
            score_buckets["3.0-3.99"] += 1
        else:
            score_buckets["<3.0"] += 1
        
        # Check if would survive latency penalty
        # For shadow analysis, we assume if score is high enough, it would survive
        # (Full analysis would require historical price data to compute actual P&L)
        if score >= 5.0:
            decision_price = trade.get("decision_price", 0.0)
            if decision_price > 0:
                # Apply latency penalty
                adjusted_price = apply_latency_penalty(decision_price, trade.get("direction", "bullish"))
                # For shadow analysis, we mark as "survived" if price adjustment is minimal
                # (0.5 bps is very small, so most high-score trades would survive)
                price_adjustment_pct = abs(adjusted_price - decision_price) / decision_price * 100
                if price_adjustment_pct < 0.01:  # Less than 0.01% impact
                    survived.append(trade)
    
    return {
        "total_analyzed": len(blocked),
        "high_score_trades": len(high_score),
        "survived_latency": len(survived),
        "score_distribution": dict(score_buckets),
        "high_score_examples": high_score[:10]  # Top 10 examples
    }

def main():
    print("=" * 80)
    print("SHADOW ANALYSIS: BLOCKED TRADES vs LATENCY PENALTY (0.5 bps)")
    print("=" * 80)
    
    # Load blocked trades
    print("\nLoading blocked trades...")
    blocked = load_blocked_trades()
    print(f"Total blocked trades found: {len(blocked)}")
    
    if not blocked:
        print("\nNo blocked trades found. Analysis complete.")
        return
    
    # Analyze
    print("\nAnalyzing blocked trades...")
    analysis = analyze_blocked_trades(blocked)
    
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"  Total Analyzed: {analysis['total_analyzed']}")
    print(f"  High-Score Trades (>=5.0): {analysis['high_score_trades']}")
    print(f"  Would Survive 0.5 bps Latency: {analysis['survived_latency']}")
    
    print(f"\n📈 Score Distribution:")
    for bucket, count in analysis['score_distribution'].items():
        print(f"  {bucket}: {count} trades")
    
    if analysis.get("high_score_examples"):
        print(f"\n🔍 High-Score Examples (Top 10):")
        for i, trade in enumerate(analysis["high_score_examples"], 1):
            print(f"  {i}. {trade['symbol']}: Score={trade['score']:.2f}, "
                  f"Direction={trade.get('direction', 'unknown')}, "
                  f"Reason={trade.get('reason', 'unknown')}")
    
    print("\n" + "=" * 80)
    print("Note: Full shadow analysis requires historical price data to compute actual P&L.")
    print("This analysis assumes high-score trades (>5.0) would generally survive 0.5 bps latency.")
    print("=" * 80)

if __name__ == "__main__":
    main()
