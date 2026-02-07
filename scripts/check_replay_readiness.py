"""Replay-readiness sanity check: ensure exit attribution rows have required fields."""
import glob
import json
from collections import Counter

required = ["mode", "strategy", "symbol", "side", "entry_ts", "entry_price", "qty"]
# Aliases: entry_timestamp satisfies entry_ts for replay
aliases = {"entry_ts": ["entry_ts", "entry_timestamp"]}

counts = Counter()
total = 0

for f in glob.glob("logs/exit_attribution*.jsonl"):
    for line in open(f):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        total += 1
        for k in required:
            keys_to_check = aliases.get(k, [k])
            if any(r.get(kk) is not None for kk in keys_to_check):
                counts[k] += 1

print("Replay readiness:")
print(f"Total exits: {total}")
for k in required:
    pct = (counts[k] / total * 100) if total else 0
    print(f"{k:12s}: {counts[k]:6d} ({pct:5.1f}%)")
