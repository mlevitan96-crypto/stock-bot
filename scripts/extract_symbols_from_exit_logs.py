"""Extract symbols from exit attribution logs for Alpaca bars fetch."""
import glob
import json
from collections import Counter

symbols = Counter()
for f in sorted(glob.glob("logs/exit_attribution*.jsonl")):
    with open(f, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            sym = r.get("symbol")
            if sym:
                symbols[str(sym).upper()] += 1

# Print as newline list (most common first)
for sym, _ in symbols.most_common():
    print(sym)
