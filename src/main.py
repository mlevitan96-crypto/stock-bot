#!/usr/bin/env python3
"""
Dry-run entrypoint for owner validation.

Command (owner contract):
  python3 src/main.py --dry-run

Contract:
- Must NOT place orders.
- Must NOT modify trading/scoring/exit logic (read-only checks only).
- Must validate v2-only + paper-only invariants and basic integration reachability.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Tuple


def _fail(msg: str) -> Tuple[bool, str]:
    return False, msg


def _ok(msg: str = "OK") -> Tuple[bool, str]:
    return True, msg


def _is_paper_endpoint(url: str) -> bool:
    try:
        u = str(url or "")
        return ("paper-api.alpaca.markets" in u) and ("api.alpaca.markets" in u or True)
    except Exception:
        return False


def _run_checks() -> List[Tuple[str, bool, str]]:
    out: List[Tuple[str, bool, str]] = []

    # 1) Paper-only invariant
    base_url = os.getenv("ALPACA_BASE_URL", "") or ""
    ok, detail = _ok(base_url) if _is_paper_endpoint(base_url) else _fail(f"ALPACA_BASE_URL not paper: {base_url}")
    out.append(("alpaca_paper_endpoint", ok, detail))

    # 2) Alpaca reachable (no orders)
    try:
        import alpaca_trade_api as tradeapi  # type: ignore

        key = os.getenv("ALPACA_KEY", "") or ""
        sec = os.getenv("ALPACA_SECRET", "") or ""
        if not key or not sec or not base_url:
            out.append(("alpaca_get_account", *_fail("Missing ALPACA_KEY/ALPACA_SECRET/ALPACA_BASE_URL")))
        else:
            api = tradeapi.REST(key, sec, base_url, api_version="v2")
            acct = api.get_account()
            out.append(("alpaca_get_account", *_ok(f"status={getattr(acct,'status',None)} buying_power={getattr(acct,'buying_power',None)}")))
    except Exception as e:
        out.append(("alpaca_get_account", *_fail(f"{type(e).__name__}: {e}")))

    # 3) UW spec allow-list + UW reachable
    try:
        from src.uw.uw_spec_loader import get_valid_uw_paths

        n = len(get_valid_uw_paths() or set())
        ok, detail = _ok(str(n)) if n >= 50 else _fail(f"too_few_paths={n}")
        out.append(("uw_spec_loader", ok, detail))
    except Exception as e:
        out.append(("uw_spec_loader", *_fail(f"{type(e).__name__}: {e}")))

    try:
        from src.uw.uw_client import uw_http_get

        status, data, _hdr = uw_http_get("/api/alerts", params={"limit": 1}, timeout_s=8.0)
        if status == 200:
            out.append(("uw_intel_reachable", *_ok(f"status={status} keys={list((data or {}).keys())}")))
        else:
            out.append(("uw_intel_reachable", *_fail(f"status={status} keys={list((data or {}).keys())}")))
    except Exception as e:
        out.append(("uw_intel_reachable", *_fail(f"{type(e).__name__}: {e}")))

    # 4) v2 scoring runs (no live UW calls; uses provided enriched payload)
    try:
        from uw_composite_v2 import compute_composite_score_v2

        enriched: Dict[str, Any] = {
            "sentiment": "NEUTRAL",
            "conviction": 0.5,
            "dark_pool": {"sentiment": "NEUTRAL", "total_premium": 0.0},
            "insider": {"sentiment": "NEUTRAL", "conviction_modifier": 0.0},
            "freshness": 1.0,
        }
        r = compute_composite_score_v2("SPY", enriched, regime="NEUTRAL")
        score = r.get("score") if isinstance(r, dict) else None
        ok, detail = _ok(f"score={score}") if isinstance(score, (int, float)) else _fail(f"bad_result_type={type(r).__name__}")
        out.append(("v2_scoring_runs", ok, detail))
    except Exception as e:
        out.append(("v2_scoring_runs", *_fail(f"{type(e).__name__}: {e}")))

    # 5) v2 exit intelligence runs (pure computation)
    try:
        from src.exit.exit_score_v2 import compute_exit_score_v2
        from src.exit.profit_targets_v2 import compute_profit_target
        from src.exit.stops_v2 import compute_stop_price

        pos = {"symbol": "SPY", "side": "long", "entry_price": 100.0, "qty": 1.0, "current_price": 101.0}
        exit_score = compute_exit_score_v2(symbol="SPY", position=pos, entry_context={}, intel_snapshot={})
        pt = compute_profit_target(symbol="SPY", position=pos, intel_snapshot={})
        st = compute_stop_price(symbol="SPY", position=pos, intel_snapshot={})
        out.append(("v2_exit_intel_runs", *_ok(f"exit_score={exit_score} profit_target={pt} stop={st}")))
    except Exception as e:
        out.append(("v2_exit_intel_runs", *_fail(f"{type(e).__name__}: {e}")))

    # 6) Shadow modules must not exist (import should fail)
    try:
        import importlib

        importlib.import_module("src.trading.shadow_executor")
        out.append(("no_shadow_modules", *_fail("shadow_executor importable (should be removed)")))
    except Exception:
        out.append(("no_shadow_modules", *_ok("shadow modules not importable")))

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Run owner-level dry-run checks (no orders)")
    args = ap.parse_args()

    if not args.dry_run:
        print("Refusing: must pass --dry-run", flush=True)
        return 2

    checks = _run_checks()
    ok_all = all(bool(c[1]) for c in checks)
    print("V2 ENGINE DRY RUN (paper-only)")
    for name, ok, detail in checks:
        print(f"- {'PASS' if ok else 'FAIL'} {name} - {detail}")
    print("OVERALL:", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 2


if __name__ == "__main__":
    raise SystemExit(main())

