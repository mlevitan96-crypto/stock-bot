#!/usr/bin/env python3
"""Check recent signals in detail to see if scoring is working"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter

def check_recent_signals_detailed(minutes: int = 30):
    """Check signals in the last N minutes with detailed analysis"""
    signal_log = Path("logs/signals.jsonl")
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    recent_signals = []
    
    if signal_log.exists():
        with open(signal_log, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    cluster = data.get('cluster', {})
                    score = cluster.get('composite_score', 0.0)
                    source = cluster.get('source', 'unknown')
                    ts_str = data.get('ts', '')
                    
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            if ts >= cutoff_time:
                                recent_signals.append({
                                    'timestamp': ts_str,
                                    'symbol': cluster.get('ticker', 'N/A'),
                                    'score': score,
                                    'source': source,
                                    'direction': cluster.get('direction', 'unknown')
                                })
                        except Exception as e:
                            pass
                except:
                    pass
    
    print("="*80)
    print(f"DETAILED SIGNAL ANALYSIS (Last {minutes} minutes)")
    print("="*80)
    print()
    
    if not recent_signals:
        print(f"No signals found in the last {minutes} minutes")
        return
    
    print(f"Total signals: {len(recent_signals)}")
    print()
    
    # Score analysis
    scores = [s['score'] for s in recent_signals]
    sources = [s['source'] for s in recent_signals]
    
    print("SCORE ANALYSIS:")
    print(f"  Max score: {max(scores):.2f}")
    print(f"  Min score: {min(scores):.2f}")
    print(f"  Avg score: {sum(scores)/len(scores):.2f}")
    print(f"  Scores > 4.0: {sum(1 for s in scores if s > 4.0)}")
    print(f"  Scores > 3.0: {sum(1 for s in scores if s > 3.0)}")
    print(f"  Scores > 2.0: {sum(1 for s in scores if s > 2.0)}")
    print(f"  Scores > 1.5: {sum(1 for s in scores if s > 1.5)}")
    print(f"  Scores > 0.0: {sum(1 for s in scores if s > 0.0)}")
    print(f"  Scores = 0.00: {sum(1 for s in scores if s == 0.0)}")
    print()
    
    # Source analysis
    source_counts = Counter(sources)
    print("SOURCE ANALYSIS:")
    for source, count in source_counts.most_common():
        print(f"  {source}: {count} ({count/len(sources)*100:.1f}%)")
    print()
    
    # Recent signals (last 10)
    print("MOST RECENT SIGNALS (Last 10):")
    for sig in sorted(recent_signals, key=lambda x: x['timestamp'], reverse=True)[:10]:
        score_color = "✓" if sig['score'] > 0.0 else "✗"
        print(f"  {score_color} {sig['timestamp'][:19]} | {sig['symbol']:6} | score={sig['score']:.2f} | source={sig['source']:15} | {sig['direction']}")
    print()
    
    # Top scores
    top_scores = sorted(recent_signals, key=lambda x: x['score'], reverse=True)[:10]
    if top_scores and top_scores[0]['score'] > 0.0:
        print("TOP SCORES (Last 10):")
        for sig in top_scores:
            print(f"  {sig['timestamp'][:19]} | {sig['symbol']:6} | score={sig['score']:.2f} | source={sig['source']:15} | {sig['direction']}")
    print()
    
    # Trading capability assessment
    print("TRADING CAPABILITY:")
    min_exec_score = 1.5  # From Config.MIN_EXEC_SCORE
    tradeable_signals = [s for s in recent_signals if s['score'] >= min_exec_score]
    print(f"  Signals >= MIN_EXEC_SCORE ({min_exec_score}): {len(tradeable_signals)}")
    print(f"  Percentage tradeable: {len(tradeable_signals)/len(recent_signals)*100:.1f}%")
    
    if len(tradeable_signals) > 0:
        print(f"  ✓ TRADING IS POSSIBLE")
        print(f"  Top tradeable signals:")
        for sig in sorted(tradeable_signals, key=lambda x: x['score'], reverse=True)[:5]:
            print(f"    {sig['symbol']:6} | score={sig['score']:.2f} | {sig['direction']}")
    else:
        print(f"  ✗ NO TRADEABLE SIGNALS (all scores < {min_exec_score})")
    
    print("="*80)

if __name__ == "__main__":
    check_recent_signals_detailed(minutes=30)
