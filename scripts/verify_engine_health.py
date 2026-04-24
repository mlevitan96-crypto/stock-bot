#!/usr/bin/env python3
"""
End-to-end dry run: Alpaca account/positions + composite scoring (no market-hours gate).

Run from repo root:
  python3 scripts/verify_engine_health.py
  python3 scripts/verify_engine_health.py --symbol SPY
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# Load .env before main / Alpaca
try:
    from dotenv import load_dotenv

    load_dotenv(REPO / ".env")
except Exception:
    pass


def _alpaca_rest():
    import alpaca_trade_api as tradeapi  # type: ignore

    key = os.getenv("ALPACA_KEY") or os.getenv("APCA_API_KEY_ID") or os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET") or os.getenv("APCA_API_SECRET_KEY") or os.getenv("ALPACA_API_SECRET")
    base = (
        os.getenv("ALPACA_BASE_URL")
        or os.getenv("APCA_API_BASE_URL")
        or "https://paper-api.alpaca.markets"
    )
    if not key or not secret:
        raise RuntimeError(
            "Missing Alpaca credentials (set ALPACA_KEY/ALPACA_SECRET or APCA_API_KEY_ID/APCA_API_SECRET_KEY)"
        )
    return tradeapi.REST(key, secret, base_url=base.rstrip("/"))


def _pick_symbol(uw_cache: Dict[str, Any], preferred: List[str]) -> str:
    keys = {str(k).upper(): k for k in uw_cache.keys() if k}
    for p in preferred:
        u = p.upper()
        if u in keys:
            return str(keys[u])
    if uw_cache:
        return str(next(iter(uw_cache.keys())))
    return preferred[0]


def _regime() -> str:
    try:
        from config.registry import StateFiles
        import json as _json

        p = StateFiles.REGIME_DETECTOR
        if p.exists():
            d = _json.loads(p.read_text(encoding="utf-8", errors="replace"))
            if isinstance(d, dict):
                r = d.get("current_regime") or d.get("regime")
                if isinstance(r, str) and r.strip():
                    return r.strip()
    except Exception:
        pass
    return "mixed"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Alpaca + UW composite v2 health (dry run).")
    parser.add_argument("--symbol", default=None, help="Override ticker (default: NVDA, else SPY, else cache)")
    args = parser.parse_args()

    print("=" * 72)
    print("verify_engine_health.py — Back-to-Basics scoring pipeline check")
    print("=" * 72)

    # --- 1) Alpaca risk / account ---
    api = _alpaca_rest()
    acct = api.get_account()
    buying_power = float(getattr(acct, "buying_power", 0) or 0)
    equity = float(getattr(acct, "equity", 0) or 0)
    positions = api.list_positions()
    n_pos = len(positions)

    print("\n[1] Account / positions")
    print(f"    buying_power: {buying_power:,.2f}")
    print(f"    equity:       {equity:,.2f}")
    print(f"    open_positions: {n_pos}")

    import main as _main  # noqa: WPS433 — matches droplet diagnostic pattern

    Config = _main.Config
    max_conc = int(getattr(Config, "MAX_CONCURRENT_POSITIONS", 16))
    min_exec = float(getattr(Config, "MIN_EXEC_SCORE", 3.2))
    print(f"    MAX_CONCURRENT_POSITIONS (Config): {max_conc}")
    if n_pos >= max_conc:
        print(f"    WARNING: at or over capacity ({n_pos} >= {max_conc}).")
    else:
        print(f"    OK: under position cap ({n_pos} < {max_conc}).")

    # --- 2) Intelligence + composite (forced; no market-hours check) ---
    import uw_composite_v2 as uw_v2
    import uw_enrichment_v2 as uw_enrich

    uw_cache = _main.read_uw_cache() if callable(getattr(_main, "read_uw_cache", None)) else {}
    if not isinstance(uw_cache, dict):
        uw_cache = {}

    symbol = (args.symbol or "").strip().upper() or _pick_symbol(uw_cache, ["NVDA", "SPY"])
    regime = _regime()

    print("\n[2] Forced composite evaluation")
    print(f"    symbol: {symbol}")
    print(f"    regime: {regime}")
    print(f"    uw_cache keys (sample): {len(uw_cache)} symbols")

    enriched = uw_cache.get(symbol, {}) if isinstance(uw_cache.get(symbol), dict) else {}
    try:
        enriched_live = uw_enrich.enrich_signal(symbol, uw_cache, regime) or enriched
    except Exception as e:
        print(f"    enrich_signal warning: {e!r}; using raw cache slice")
        enriched_live = enriched

    # Avoid appending a diagnostic line to logs/uw_attribution.jsonl
    try:
        import src.uw.uw_attribution as _uwa

        _real_emit = _uwa.emit_uw_attribution

        def _noop_emit(**_kw: Any) -> None:
            return None

        _uwa.emit_uw_attribution = _noop_emit  # type: ignore[assignment]
        try:
            composite: Dict[str, Any] = uw_v2.compute_composite_score_v2(symbol, enriched_live, regime) or {}
        finally:
            _uwa.emit_uw_attribution = _real_emit  # type: ignore[assignment]
    except Exception:
        composite = uw_v2.compute_composite_score_v2(symbol, enriched_live, regime) or {}

    components = composite.get("components")
    if not isinstance(components, dict):
        components = {}

    score = composite.get("score")
    try:
        score_f = float(score) if score is not None else float("nan")
    except (TypeError, ValueError):
        score_f = float("nan")

    print("\n[3] Full `components` dict (JSON)")
    print(json.dumps(components, indent=2, default=str))

    # Map WEIGHTS_V3 names -> components keys (engine uses `flow` + `iv_skew`)
    core_map = {
        "options_flow": ("flow", "options_flow"),
        "dark_pool": ("dark_pool",),
        "greeks_gamma": ("greeks_gamma",),
        "ftd_pressure": ("ftd_pressure",),
        "iv_skew (weight iv_term_skew)": ("iv_skew", "iv_term_skew"),
        "oi_change": ("oi_change",),
        "toxicity_penalty": ("toxicity_penalty",),
    }
    print("\n[3b] Seven core signals (values from `components`)")
    for label, keys in core_map.items():
        val: Optional[Any] = None
        for k in keys:
            if k in components and components[k] is not None:
                val = components[k]
                break
        print(f"    {label}: {val!r}")

    try:
        from uw_composite_v2 import WEIGHTS_V3

        print("\n[3c] WEIGHTS_V3 (reference)")
        print(json.dumps(WEIGHTS_V3, indent=2, sort_keys=True))
    except Exception as e:
        print(f"\n[3c] could not load WEIGHTS_V3: {e!r}")

    print("\n[4] Gate check (MIN_EXEC_SCORE)")
    print(f"    composite score: {score_f}")
    print(f"    MIN_EXEC_SCORE:  {min_exec}")
    if score_f != score_f:  # NaN
        print("    RESULT: could not parse score — FAIL")
        return 2
    if score_f >= min_exec:
        print(f"    RESULT: PASS (score >= {min_exec})")
    else:
        print(f"    RESULT: below entry gate (score < {min_exec}) — expected for many symbols; pipeline OK if no exception")

    print("\n" + "=" * 72)
    print("verify_engine_health.py — done")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
