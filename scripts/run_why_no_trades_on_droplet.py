#!/usr/bin/env python3
"""
Run ON THE DROPLET. Loads cache, runs composite for sample symbols, prints score vs threshold and why gate fails.
Output: one line per symbol with score, threshold, pass/fail, reason. Use to find root cause of 0 clusters.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

def main():
    cache_path = REPO / "data" / "uw_flow_cache.json"
    if not cache_path.exists():
        print("ERROR: data/uw_flow_cache.json not found", file=sys.stderr)
        return 1
    with open(cache_path, "r", encoding="utf-8") as f:
        cache = json.load(f)
    symbols = [k for k in cache.keys() if not k.startswith("_") and isinstance(cache.get(k), dict)][:50]
    if not symbols:
        print("ERROR: no symbol keys in cache", file=sys.stderr)
        return 1

    import uw_enrichment_v2 as uw_enrich
    import uw_composite_v2 as uw_v2

    threshold_base = float(os.environ.get("ENTRY_THRESHOLD_BASE", "2.7"))
    results = []
    for ticker in symbols:
        try:
            enriched = uw_enrich.enrich_signal(ticker, cache, "mixed")
            if not enriched:
                results.append((ticker, 0.0, threshold_base, False, "enrich_empty"))
                continue
            composite = uw_v2.compute_composite_score_v2(ticker, enriched, "mixed")
            if not composite:
                results.append((ticker, 0.0, threshold_base, False, "composite_none"))
                continue
            score = float(composite.get("score", 0.0))
            threshold = uw_v2.get_threshold(ticker, "base")
            toxicity = float(composite.get("toxicity", 0.0))
            freshness = float(composite.get("freshness", 1.0))
            if score < threshold:
                results.append((ticker, score, threshold, False, f"score_gate({score:.2f}<{threshold:.2f})"))
            elif toxicity > 0.90:
                results.append((ticker, score, threshold, False, f"toxicity_gate({toxicity:.2f})"))
            elif freshness < 0.25:
                results.append((ticker, score, threshold, False, f"freshness_gate({freshness:.2f})"))
            else:
                results.append((ticker, score, threshold, True, "pass"))
        except Exception as e:
            results.append((ticker, 0.0, threshold_base, False, f"error:{type(e).__name__}"))

    # Sort by score descending
    results.sort(key=lambda x: -x[1])
    print("symbol\tscore\tthreshold\tpass\treason")
    for ticker, score, thresh, pass_, reason in results[:40]:
        print(f"{ticker}\t{score:.3f}\t{thresh}\t{pass_}\t{reason}")
    passed = sum(1 for r in results if r[3])
    print(f"\n# Passed: {passed}/{len(results)}. Threshold base: {threshold_base}")
    if passed == 0 and results:
        best = results[0]
        print(f"# Best: {best[0]} score={best[1]:.3f} need={best[2]} gap={best[2]-best[1]:.3f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
