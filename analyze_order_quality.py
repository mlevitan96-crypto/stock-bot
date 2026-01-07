#!/usr/bin/env python3
"""Analyze actual order quality and determine if thresholds should be restored"""

import json
from pathlib import Path

print("="*80)
print("ORDER QUALITY ANALYSIS")
print("="*80)

# Get recent orders with scores
orders_file = Path("logs/orders.jsonl")
if orders_file.exists():
    lines = orders_file.read_text().strip().split('\n')
    orders = [json.loads(l) for l in lines[-50:] if l.strip() and l.strip().startswith('{')]
    
    orders_with_scores = [o for o in orders if o.get("score", 0) > 0]
    
    if orders_with_scores:
        scores = [o.get("score", 0) for o in orders_with_scores]
        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)
        
        print(f"\nRecent orders with scores: {len(orders_with_scores)}")
        print(f"Score range: {min_score:.2f} - {max_score:.2f}")
        print(f"Average score: {avg_score:.2f}")
        print(f"\nScore distribution:")
        print(f"  >= 2.7 (original base): {sum(1 for s in scores if s >= 2.7)}")
        print(f"  >= 2.0 (registry default MIN_EXEC): {sum(1 for s in scores if s >= 2.0)}")
        print(f"  >= 1.5 (current threshold): {sum(1 for s in scores if s >= 1.5)}")
        print(f"  >= 1.0: {sum(1 for s in scores if s >= 1.0)}")
        print(f"  < 1.0: {sum(1 for s in scores if s < 1.0)}")
        
        print(f"\nOrder details:")
        for o in orders_with_scores[-10:]:
            symbol = o.get("symbol", "?")
            score = o.get("score", 0)
            status = o.get("status", "?")
            side = o.get("side", "?")
            print(f"  {symbol}: score={score:.2f}, {side}, status={status}")
        
        print(f"\nQuality Assessment:")
        if avg_score >= 2.0:
            print("  GOOD: Average score is >= 2.0 (original MIN_EXEC)")
            print("  Recommendation: Can restore MIN_EXEC_SCORE to 2.0")
        elif avg_score >= 1.5:
            print("  MODERATE: Average score is 1.5-2.0")
            print("  Recommendation: Keep threshold at 1.5, investigate why scores aren't higher")
        else:
            print("  LOW: Average score < 1.5")
            print("  Recommendation: Investigate scoring components - scores may be too low")
    else:
        print("No orders with scores found")

print("\n" + "="*80)
