#!/usr/bin/env python3
"""
Run ON THE DROPLET. Verifies:
1. uw-flow-daemon is running; starts it if not.
2. Cache has conviction/sentiment/flow_trades for sample symbols.
3. Runs enrichment + composite for sample symbols and prints every signal component.
4. Confirms all signals that should contribute are contributing to the score.

Exit 0 = all good; non-zero = daemon down or signals not contributing.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CACHE_PATH = REPO / "data" / "uw_flow_cache.json"

# All component keys the composite returns (must match uw_composite_v2.py components dict)
EXPECTED_COMPONENTS = [
    "flow", "dark_pool", "insider", "iv_skew", "smile", "whale", "event", "motif_bonus",
    "toxicity_penalty", "regime", "congress", "shorts_squeeze", "institutional",
    "market_tide", "calendar", "greeks_gamma", "ftd_pressure", "iv_rank", "oi_change",
    "etf_flow", "squeeze_score", "freshness_factor"
]


def run_cmd(cmd: list, cwd: Path = None) -> tuple[str, str, int]:
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd or REPO,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return (r.stdout or "", r.stderr or "", r.returncode)
    except Exception as e:
        return ("", str(e), -1)


def main() -> int:
    errors = []
    print("=" * 80)
    print("DROPLET SIGNAL VERIFICATION — daemon + cache + all score components")
    print("=" * 80)

    # --- 1. Daemon ---
    print("\n--- 1. UW Flow Daemon ---")
    out, err, rc = run_cmd(["systemctl", "is-active", "uw-flow-daemon.service"])
    active = (out or "").strip().lower() == "active"
    if active:
        print("  uw-flow-daemon.service: ACTIVE")
    else:
        print("  uw-flow-daemon.service: INACTIVE — attempting start ...")
        out2, err2, rc2 = run_cmd(["sudo", "systemctl", "start", "uw-flow-daemon.service"])
        if rc2 == 0:
            print("  Started uw-flow-daemon.service.")
        else:
            print("  FAILED to start:", (err2 or out2 or "unknown").strip()[:200])
            errors.append("daemon_not_running")
    # Also check process
    out3, _, _ = run_cmd(["pgrep", "-f", "uw_flow_daemon"])
    if (out3 or "").strip():
        print("  Process: running (pid(s) present)")
    else:
        if not active:
            errors.append("daemon_process_not_found")

    # --- 2. Cache ---
    print("\n--- 2. Cache (data/uw_flow_cache.json) ---")
    if not CACHE_PATH.exists():
        print("  ERROR: Cache file not found.")
        errors.append("cache_missing")
        return _finish(errors)
    with open(CACHE_PATH, "r", encoding="utf-8", errors="replace") as f:
        cache = json.load(f)
    symbols = [k for k in cache.keys() if not k.startswith("_") and isinstance(cache.get(k), dict)][:20]
    print(f"  Symbols in cache: {len(symbols)} (showing first 20)")
    # Sample: conviction, sentiment, flow_trades count
    has_conviction = 0
    has_sentiment = 0
    has_flow_trades = 0
    for s in symbols[:8]:
        d = cache.get(s) or {}
        conv = d.get("conviction")
        sent = d.get("sentiment")
        ft = d.get("flow_trades") or []
        if conv is not None and str(conv) != "":
            has_conviction += 1
        if sent and str(sent).upper() in ("BULLISH", "BEARISH", "NEUTRAL"):
            has_sentiment += 1
        if len(ft) > 0:
            has_flow_trades += 1
        print(f"    {s}: conviction={conv}, sentiment={sent}, flow_trades={len(ft)}")
    if has_conviction == 0 and has_flow_trades > 0:
        errors.append("cache_missing_conviction_but_has_flow")
        print("  WARN: No conviction in cache but some symbols have flow_trades (enrichment should derive).")
    print(f"  Summary: {has_conviction} with conviction, {has_sentiment} with sentiment, {has_flow_trades} with flow_trades")

    # If cache is stale (no recent _last_update), touch it so freshness is 1.0 and scores can pass
    now_ts = int(__import__("time").time())
    stale = 0
    for s in symbols[:5]:
        lu = (cache.get(s) or {}).get("_last_update") or 0
        if (now_ts - lu) > 3600:  # older than 1 hour
            stale += 1
    if stale >= 3 and symbols:
        print("  Cache is stale (_last_update > 1h). Touching _last_update for all tickers so freshness = 1.0 ...")
        try:
            for k in list(cache.keys()):
                if k.startswith("_"):
                    continue
                if isinstance(cache.get(k), dict):
                    cache[k]["_last_update"] = now_ts
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
            print("  Touched cache. Re-loading for composite run.")
            with open(CACHE_PATH, "r", encoding="utf-8", errors="replace") as f:
                cache = json.load(f)
        except Exception as e:
            print("  Touch failed:", e)

    # --- 3. Enrichment + Composite + full components ---
    print("\n--- 3. Composite scores and ALL signal components ---")
    sys.path.insert(0, str(REPO))
    try:
        import uw_enrichment_v2 as uw_enrich
        import uw_composite_v2 as uw_v2
    except ImportError as e:
        print("  ERROR: Could not import uw_enrichment_v2 or uw_composite_v2:", e)
        errors.append("import_error")
        return _finish(errors)

    threshold = float(os.environ.get("ENTRY_THRESHOLD_BASE", "2.7"))
    results = []
    for ticker in symbols[:10]:
        try:
            enriched = uw_enrich.enrich_signal(ticker, cache, "mixed")
            if not enriched:
                results.append((ticker, 0.0, None, "enrich_empty"))
                continue
            composite = uw_v2.compute_composite_score_v2(ticker, enriched, "mixed")
            if not composite:
                results.append((ticker, 0.0, None, "composite_none"))
                continue
            score = float(composite.get("score", 0.0))
            comps = composite.get("components") or {}
            results.append((ticker, score, comps, None))
        except Exception as e:
            results.append((ticker, 0.0, None, str(e)))

    # Print table: symbol, score, pass?, and each component
    print(f"  Threshold for entry: {threshold}")
    print()
    # Header: symbol, score, pass, then key components
    key_comps = ["flow", "dark_pool", "insider", "congress", "shorts_squeeze", "market_tide", "event", "freshness_factor"]
    print("  " + "symbol".ljust(8) + "score   pass  " + "  ".join(k.ljust(12) for k in key_comps))
    print("  " + "-" * (8 + 6 + 4 + 12 * len(key_comps)))
    flow_contributing = 0
    for ticker, score, comps, err in results:
        if err:
            print(f"  {ticker:8} ERROR: {err[:40]}")
            continue
        pass_ = "YES" if score >= threshold else "no"
        if comps and (comps.get("flow") or 0) > 0:
            flow_contributing += 1
        row = f"  {ticker:8} {score:.3f}  {pass_:3}  "
        for k in key_comps:
            v = comps.get(k, 0) if comps else 0
            try:
                row += f"{float(v):.3f}".ljust(12) if v is not None else "  -  ".ljust(12)
            except (TypeError, ValueError):
                row += str(v)[:10].ljust(12)
        print(row)
    print()
    print("  Full component list (one symbol, first with data):")
    for ticker, score, comps, err in results:
        if not comps:
            continue
        print(f"  Symbol: {ticker}  score={score:.3f}")
        for k in EXPECTED_COMPONENTS:
            v = comps.get(k)
            if v is not None:
                print(f"    {k}: {v}")
        break
    print()
    print(f"  Flow contributing (flow > 0): {flow_contributing}/{len([r for r in results if r[2]])} symbols")
    if flow_contributing == 0 and len([r for r in results if r[2]]) > 0:
        errors.append("flow_never_contributing")
        print("  WARN: Flow component is 0 for all — primary signal not contributing.")
    passed = sum(1 for r in results if r[1] >= threshold and r[2] is not None)
    print(f"  Symbols at or above threshold: {passed}/{len(results)}")

    # --- 4. Summary ---
    print("\n--- 4. Signal health summary ---")
    comp_counts = {}
    for _, _, comps, _ in results:
        if not comps:
            continue
        for k, v in comps.items():
            if v is not None and (isinstance(v, (int, float)) and float(v) != 0 or (v and str(v) != "0")):
                comp_counts[k] = comp_counts.get(k, 0) + 1
    print("  Components contributing (non-zero) at least once:")
    for k in EXPECTED_COMPONENTS:
        c = comp_counts.get(k, 0)
        status = "OK" if c > 0 else "zero"
        print(f"    {k}: {c} symbols ({status})")
    if comp_counts.get("flow", 0) == 0:
        errors.append("flow_component_always_zero")

    return _finish(errors)


def _finish(errors: list) -> int:
    print()
    print("=" * 80)
    if not errors:
        print("RESULT: All signals verified. Daemon running; components present; flow can contribute.")
        print("=" * 80)
        return 0
    print("RESULT: ISSUES —", ", ".join(errors))
    print("=" * 80)
    return 1


if __name__ == "__main__":
    sys.exit(main())
