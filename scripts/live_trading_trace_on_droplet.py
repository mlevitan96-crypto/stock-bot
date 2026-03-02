#!/usr/bin/env python3
"""
Run ON THE DROPLET. Traces why there are no open positions:
- Last run.jsonl entries (clusters, orders)
- Last blocked_trades (reason, score, min_required)
- TRADING_MODE / PAPER_TRADING
- Cache freshness (_last_update age)
- One composite pass: would we get clusters with current cache?
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Load .env so UW_MISSING_INPUT_MODE etc. reflect what the live/paper process would use
try:
    from dotenv import load_dotenv
    load_dotenv(REPO / ".env", override=False)
except Exception:
    pass
RUN_JSONL = REPO / "logs" / "run.jsonl"
BLOCKED_JSONL = REPO / "state" / "blocked_trades.jsonl"
CACHE_PATH = REPO / "data" / "uw_flow_cache.json"


def main() -> int:
    print("=" * 80)
    print("LIVE TRADING TRACE — why no open positions?")
    print("=" * 80)

    # 1) TRADING_MODE / PAPER
    mode = os.environ.get("TRADING_MODE", "PAPER")
    paper = os.environ.get("PAPER_TRADING", "true")
    print(f"\n--- Env ---")
    print(f"  TRADING_MODE: {mode}")
    print(f"  PAPER_TRADING: {paper}")
    uw_mode = os.environ.get("UW_MISSING_INPUT_MODE", "reject")
    print(f"  UW_MISSING_INPUT_MODE: {uw_mode}  (use passthrough so composite score is preserved for expectancy gate)")
    print(f"  (Live orders only when TRADING_MODE is LIVE and PAPER_TRADING is false)")

    # 2) Last run.jsonl
    print(f"\n--- Last 5 run.jsonl entries ---")
    if not RUN_JSONL.exists():
        print("  (no run.jsonl)")
    else:
        lines = []
        with open(RUN_JSONL, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(line)
        for line in lines[-5:]:
            try:
                rec = json.loads(line)
                c = rec.get("clusters", rec.get("metrics", {}).get("clusters", "?"))
                o = rec.get("orders", rec.get("metrics", {}).get("orders", "?"))
                ts = rec.get("ts", rec.get("_ts", ""))
                print(f"  ts={ts}  clusters={c}  orders={o}")
            except Exception:
                print(f"  {line[:80]}...")

    # 3) Last blocked_trades
    print(f"\n--- Last 3 blocked_trades ---")
    if not BLOCKED_JSONL.exists():
        print("  (no blocked_trades.jsonl)")
    else:
        lines = []
        with open(BLOCKED_JSONL, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.strip():
                    lines.append(line.strip())
        for line in lines[-3:]:
            try:
                rec = json.loads(line)
                print(f"  {rec.get('symbol')}  reason={rec.get('reason')}  score={rec.get('score')}  min_required={rec.get('min_required')}")
            except Exception:
                print(f"  {line[:80]}...")

    # 4) Cache _last_update age
    print(f"\n--- Cache freshness (_last_update age) ---")
    if not CACHE_PATH.exists():
        print("  (no cache file)")
    else:
        now = int(time.time())
        cache = json.load(open(CACHE_PATH, "r", encoding="utf-8", errors="replace"))
        tickers = [k for k in cache.keys() if not k.startswith("_") and isinstance(cache.get(k), dict)]
        stale = 0
        for t in tickers[:5]:
            lu = (cache.get(t) or {}).get("_last_update", 0)
            age = now - lu if lu else 999999
            stale += 1 if age > 3600 else 0
            print(f"  {t}: age_sec={age} ({age//60} min)")
        if tickers:
            total_stale = sum(1 for t in tickers if (now - (cache.get(t) or {}).get("_last_update", 0)) > 3600)
            print(f"  Stale tickers: {total_stale}/{len(tickers)} (stale = _last_update > 1h)")

    # 5) One composite pass
    print(f"\n--- Composite pass (would we get clusters?) ---")
    sys.path.insert(0, str(REPO))
    try:
        import uw_enrichment_v2 as uw_enrich
        import uw_composite_v2 as uw_v2
    except ImportError as e:
        print(f"  Import error: {e}")
        return 0
    if not CACHE_PATH.exists():
        print("  (no cache)")
        return 0
    with open(CACHE_PATH, "r", encoding="utf-8", errors="replace") as f:
        cache = json.load(f)
    symbols = [k for k in cache.keys() if not k.startswith("_") and isinstance(cache.get(k), dict)][:15]
    threshold = float(os.environ.get("ENTRY_THRESHOLD_BASE", "2.7"))
    would_pass = 0
    for ticker in symbols:
        try:
            enriched = uw_enrich.enrich_signal(ticker, cache, "mixed")
            if not enriched:
                continue
            composite = uw_v2.compute_composite_score_v2(ticker, enriched, "mixed")
            if not composite:
                continue
            score = float(composite.get("score", 0.0))
            if score >= threshold:
                would_pass += 1
        except Exception:
            continue
    print(f"  Symbols with score >= {threshold}: {would_pass}/{len(symbols)}")
    if would_pass == 0:
        print("  -> So 0 clusters this cycle unless cache is touched (stale _last_update -> freshness=0 -> score=0).")
    else:
        print("  -> Should produce clusters this cycle if run_once runs with this cache.")

    print("\n" + "=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
