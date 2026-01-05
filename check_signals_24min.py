#!/usr/bin/env python3
"""Check signals from last 24 minutes to verify if trading is possible"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter

signal_log = Path("logs/signals.jsonl")
cutoff_24min = datetime.now(timezone.utc) - timedelta(minutes=24)

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
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    if ts >= cutoff_24min:
                        recent_signals.append({
                            'timestamp': ts_str,
                            'symbol': cluster.get('ticker', 'N/A'),
                            'score': score,
                            'source': source,
                            'direction': cluster.get('direction', 'unknown')
                        })
            except:
                pass

print("="*70)
print("SIGNAL STATUS - LAST 24 MINUTES")
print("="*70)
print(f"\nTotal signals (last 24 min): {len(recent_signals)}")

if len(recent_signals) == 0:
    print("\n*** NO SIGNALS IN LAST 24 MINUTES ***")
    print("\nPossible reasons:")
    print("  1. Market is closed")
    print("  2. Bot is not running")
    print("  3. Composite scoring not creating clusters")
    print("\nTRADING STATUS: NOT POSSIBLE (no signals)")
else:
    scores = [s['score'] for s in recent_signals]
    sources = [s['source'] for s in recent_signals]
    
    print(f"\nScore Analysis:")
    print(f"  Max score: {max(scores):.2f}")
    print(f"  Min score: {min(scores):.2f}")
    print(f"  Avg score: {sum(scores)/len(scores):.2f}")
    print(f"  Scores > 0.0: {sum(1 for s in scores if s > 0.0)} ({sum(1 for s in scores if s > 0.0)/len(scores)*100:.1f}%)")
    print(f"  Scores = 0.0: {sum(1 for s in scores if s == 0.0)} ({sum(1 for s in scores if s == 0.0)/len(scores)*100:.1f}%)")
    
    print(f"\nSource Analysis:")
    source_counts = Counter(sources)
    for src, cnt in source_counts.most_common():
        print(f"  {src}: {cnt} ({cnt/len(sources)*100:.1f}%)")
    
    min_exec_score = 1.5
    tradeable = [s for s in recent_signals if s['score'] >= min_exec_score]
    
    print(f"\nTrading Capability (MIN_EXEC_SCORE = {min_exec_score}):")
    print(f"  Tradeable signals: {len(tradeable)} ({len(tradeable)/len(recent_signals)*100:.1f}%)")
    
    if len(tradeable) > 0:
        print(f"\n*** TRADING IS POSSIBLE ***")
        print(f"\nTop tradeable signals:")
        for s in sorted(tradeable, key=lambda x: x['score'], reverse=True)[:10]:
            print(f"  {s['timestamp'][:19]} | {s['symbol']:6} | score={s['score']:.2f} | source={s['source']:15} | {s['direction']}")
    else:
        print(f"\n*** TRADING IS NOT POSSIBLE ***")
        print(f"  No signals have score >= {min_exec_score}")
        
        if sum(1 for s in scores if s > 0.0) == 0:
            print(f"\n  CRITICAL: All signals have score=0.00 - scoring engine may be broken")
        if all(s == 'unknown' for s in sources):
            print(f"\n  CRITICAL: All signals have source=unknown - composite scoring not working")

print("\n" + "="*70)
