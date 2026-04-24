#!/usr/bin/env python3
"""
Run on droplet to print composite score breakdown for a few symbols.
Usage: python3 scripts/run_score_breakdown_on_droplet.py [--symbols AAPL,SPY,NVDA] [--limit 5]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="AAPL,SPY,NVDA,TSLA,QQQ", help="Comma-separated symbols")
    ap.add_argument("--limit", type=int, default=8, help="Max symbols to print")
    args = ap.parse_args()
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()][: args.limit]

    # Load cache
    cache_path = REPO / "data" / "uw_flow_cache.json"
    if not cache_path.exists():
        print("data/uw_flow_cache.json not found", file=sys.stderr)
        return 1
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Failed to load cache: {e}", file=sys.stderr)
        return 1

    # Skip metadata keys
    symbol_keys = [k for k in cache.keys() if not k.startswith("_")]
    if not symbol_keys:
        print("No symbol keys in cache", file=sys.stderr)
        return 1

    # Prefer requested symbols, then first N from cache
    to_run = [s for s in symbols if s in symbol_keys]
    for s in symbol_keys:
        if s not in to_run and len(to_run) < args.limit:
            to_run.append(s)

    import uw_enrichment_v2 as uw_enrich
    import uw_composite_v2 as uw_v2

    enricher = uw_enrich.UWEnricher()
    market_regime = "mixed"
    now = int(time.time())

    print("=== Composite score breakdown (post-fix: 180min freshness half-life, conviction default 0.5) ===\n")
    for symbol in to_run[: args.limit]:
        raw = cache.get(symbol, {})
        if not raw:
            continue
        last_update = raw.get("_last_update", raw.get("last_update", 0))
        age_min = (now - last_update) / 60.0 if last_update else 999
        conviction = raw.get("conviction")
        try:
            enriched = uw_enrich.enrich_signal(symbol, cache, market_regime)
        except Exception as e:
            print(f"{symbol}: enrich error {e}")
            continue
        freshness = enriched.get("freshness", 0.0)
        try:
            composite = uw_v2.compute_composite_score_v2(symbol, enriched, market_regime)
        except Exception as e:
            print(f"{symbol}: composite error {e}")
            continue
        score = composite.get("score", 0.0)
        threshold = uw_v2.get_threshold(symbol, "base")
        passes = uw_v2.should_enter_v2(composite, symbol, "base", api=None)
        comps = composite.get("components", {})
        flow_c = comps.get("flow", 0)
        print(f"{symbol}: score={score:.3f} threshold={threshold} passes={passes} | conviction={conviction} age_min={age_min:.1f} freshness={freshness:.3f} flow_contrib={flow_c:.3f}")
        if not passes and score < threshold:
            print(f"  -> BLOCKED: score < threshold (gap {threshold - score:.2f})")
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
