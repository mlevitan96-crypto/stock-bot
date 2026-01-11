#!/usr/bin/env python3
"""Check recent signal scores to see if any exceed 4.0"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

def check_recent_signals(minutes: int = 30, min_score: float = 4.0):
    """Check signals in the last N minutes with scores above min_score"""
    signal_log = Path("logs/signals.jsonl")
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    all_signals = []
    recent_signals = []
    high_score_signals = []
    
    if signal_log.exists():
        with open(signal_log, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    cluster = data.get('cluster', {})
                    score = cluster.get('composite_score', 0.0)
                    ts_str = data.get('ts', '')
                    
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                            all_signals.append({
                                'timestamp': ts_str,
                                'symbol': cluster.get('ticker', 'N/A'),
                                'score': score,
                                'source': cluster.get('source', 'unknown'),
                                'direction': cluster.get('direction', 'unknown')
                            })
                            
                            if ts >= cutoff_time:
                                recent_signals.append({
                                    'timestamp': ts_str,
                                    'symbol': cluster.get('ticker', 'N/A'),
                                    'score': score,
                                    'source': cluster.get('source', 'unknown'),
                                    'direction': cluster.get('direction', 'unknown')
                                })
                                
                                if score > min_score:
                                    high_score_signals.append({
                                        'timestamp': ts_str,
                                        'symbol': cluster.get('ticker', 'N/A'),
                                        'score': score,
                                        'source': cluster.get('source', 'unknown'),
                                        'direction': cluster.get('direction', 'unknown')
                                    })
                        except Exception as e:
                            pass
                except:
                    pass
    
    print("="*80)
    print(f"SIGNAL SCORE ANALYSIS (Last {minutes} minutes)")
    print("="*80)
    print()
    
    print(f"Total signals (last {minutes} min): {len(recent_signals)}")
    print(f"Signals with score > {min_score}: {len(high_score_signals)}")
    print()
    
    if high_score_signals:
        print(f"Signals with score > {min_score}:")
        for sig in sorted(high_score_signals, key=lambda x: x['score'], reverse=True)[:20]:
            print(f"  {sig['timestamp'][:19]} | {sig['symbol']:6} | score={sig['score']:.2f} | source={sig['source']} | {sig['direction']}")
    else:
        print(f"No signals with score > {min_score}")
    
    print()
    
    if recent_signals:
        scores = [s['score'] for s in recent_signals]
        if scores:
            print(f"Score statistics (last {minutes} min):")
            print(f"  Max score: {max(scores):.2f}")
            print(f"  Min score: {min(scores):.2f}")
            print(f"  Avg score: {sum(scores)/len(scores):.2f}")
            print(f"  Scores > 3.0: {sum(1 for s in scores if s > 3.0)}")
            print(f"  Scores > 2.0: {sum(1 for s in scores if s > 2.0)}")
            print(f"  Scores > 1.0: {sum(1 for s in scores if s > 1.0)}")
            print(f"  Scores = 0.00: {sum(1 for s in scores if s == 0.0)}")
            
            # Show top 10 scores
            top_scores = sorted(recent_signals, key=lambda x: x['score'], reverse=True)[:10]
            print()
            print("Top 10 scores (last 30 min):")
            for sig in top_scores:
                print(f"  {sig['timestamp'][:19]} | {sig['symbol']:6} | score={sig['score']:.2f} | source={sig['source']}")
    
    print("="*80)

if __name__ == "__main__":
    check_recent_signals(minutes=30, min_score=4.0)
