#!/usr/bin/env python3
"""Quick verification of signals from droplet"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

signal_log = Path("logs/signals.jsonl")
cutoff_24min = datetime.now(timezone.utc) - timedelta(minutes=24)
cutoff_30min = datetime.now(timezone.utc) - timedelta(minutes=30)

recent_24min = []
recent_30min = []

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
                        recent_24min.append({'score': score, 'source': source, 'symbol': cluster.get('ticker', 'N/A')})
                    if ts >= cutoff_30min:
                        recent_30min.append({'score': score, 'source': source, 'symbol': cluster.get('ticker', 'N/A')})
            except:
                pass

print("="*60)
print("SIGNAL STATUS CHECK")
print("="*60)
print(f"\nLast 30 minutes: {len(recent_30min)} signals")
print(f"Last 24 minutes: {len(recent_24min)} signals")

if recent_24min:
    scores = [s['score'] for s in recent_24min]
    sources = [s['source'] for s in recent_24min]
    print(f"\nScores (last 24 min):")
    print(f"  Max: {max(scores):.2f}")
    print(f"  Min: {min(scores):.2f}")
    print(f"  Avg: {sum(scores)/len(scores):.2f}")
    print(f"  > 0.0: {sum(1 for s in scores if s > 0.0)}")
    print(f"  = 0.0: {sum(1 for s in scores if s == 0.0)}")
    print(f"\nSources (last 24 min):")
    from collections import Counter
    for src, cnt in Counter(sources).most_common():
        print(f"  {src}: {cnt}")
    
    tradeable = [s for s in recent_24min if s['score'] >= 1.5]
    print(f"\nTradeable (score >= 1.5): {len(tradeable)}")
    if tradeable:
        print("  Top tradeable:")
        for s in sorted(tradeable, key=lambda x: x['score'], reverse=True)[:5]:
            print(f"    {s['symbol']:6} | {s['score']:.2f} | {s['source']}")
    print("\n" + "="*60)
