#!/usr/bin/env python3
"""
Paper/live account: cancel all open orders, then close all positions via Alpaca REST.

**Governance:** Prefer `systemctl stop stock-bot` (or equivalent) *before* running so the
trading loop does not re-open positions or race this script. See
`scripts/repair/alpaca_controlled_liquidation.py` for polling + evidence.

Usage (repo root):
  python3 scripts/liquidate_all.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, List

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from dotenv import load_dotenv

    load_dotenv(REPO / ".env")
except Exception:
    pass


def _rest():
    import alpaca_trade_api as tradeapi  # type: ignore

    key = os.getenv("ALPACA_KEY") or os.getenv("APCA_API_KEY_ID") or os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET") or os.getenv("APCA_API_SECRET_KEY") or os.getenv("ALPACA_API_SECRET")
    base = (
        os.getenv("ALPACA_BASE_URL")
        or os.getenv("APCA_API_BASE_URL")
        or "https://paper-api.alpaca.markets"
    )
    if not key or not secret:
        print(
            "ERROR: Missing Alpaca credentials "
            "(ALPACA_KEY/ALPACA_SECRET or APCA_API_KEY_ID/APCA_API_SECRET_KEY).",
            file=sys.stderr,
        )
        sys.exit(2)
    return tradeapi.REST(key, secret, base_url=base.rstrip("/"))


def _summarize_close_batch(result: Any) -> None:
    """Print one line per close request from close_all_positions() return value."""
    if result is None:
        print("    (no structured return; broker may still have accepted closes)", flush=True)
        return
    if not isinstance(result, (list, tuple)):
        print(f"    raw: {type(result).__name__}", flush=True)
        return
    n = len(result)
    ok = 0
    for i, item in enumerate(result):
        sym = getattr(item, "symbol", None)
        status = getattr(item, "status", None)
        body = getattr(item, "body", None)
        if sym is None and isinstance(body, dict):
            sym = body.get("symbol")
        if status is None and isinstance(body, dict):
            status = body.get("status")
        order_st = None
        if isinstance(body, dict):
            order_st = body.get("status")
        line = f"    [{i + 1}/{n}] symbol={sym!r} http_status={status!r} order_status={order_st!r}"
        print(line, flush=True)
        if status == 200 or (isinstance(status, int) and 200 <= status < 300):
            ok += 1
    print(f"    Summary: {ok}/{n} entries with HTTP 2xx", flush=True)


def _close_positions_fallback(api: Any, positions: List[Any]) -> List[dict]:
    out: List[dict] = []
    for p in positions:
        sym = getattr(p, "symbol", "") or ""
        if not sym:
            continue
        try:
            try:
                api.close_position(sym, cancel_orders=True)
            except TypeError:
                api.close_position(sym)
            out.append({"symbol": sym, "ok": True, "error": None})
        except Exception as e:
            out.append({"symbol": sym, "ok": False, "error": str(e)[:500]})
        time.sleep(0.25)
    return out


def main() -> int:
    print("liquidate_all.py — Alpaca cancel-all + close-all", flush=True)
    print(
        "NOTE: Stop stock-bot before production liquidation to avoid races.\n",
        file=sys.stderr,
        flush=True,
    )

    api = _rest()
    base_url = getattr(api, "_base_url", getattr(api, "base_url", ""))
    print(f"Using base URL: {base_url}", flush=True)

    # 1) Cancel orders
    print("\n[1] cancel_all_orders()", flush=True)
    try:
        api.cancel_all_orders()
        print("    OK — cancel_all_orders() completed (broker accepted request).", flush=True)
    except Exception as e:
        print(f"    ERROR: {e!r}", flush=True)
        return 1

    # 2) Close all positions
    print("\n[2] close_all_positions()", flush=True)
    before = api.list_positions() or []
    print(f"    Positions before close: {len(before)}", flush=True)

    result: Any = None
    try:
        cap = getattr(api, "close_all_positions", None)
        if callable(cap):
            try:
                result = cap(cancel_orders=False)
            except TypeError:
                result = cap()
            print("    OK — close_all_positions() returned.", flush=True)
        else:
            raise AttributeError("close_all_positions not available on REST client")
    except Exception as e:
        print(f"    close_all_positions unavailable or failed ({e!r}); falling back to per-symbol close.", flush=True)
        result = _close_positions_fallback(api, before)

    # 3) Confirm what we got back
    print("\n[3] Broker response / per-close confirmation", flush=True)
    _summarize_close_batch(result)

    wait_sec = 15.0
    print(f"\n[4] Waiting {wait_sec:.0f}s for fills (paper/live may stay open when market is closed)…", flush=True)
    time.sleep(wait_sec)
    after = api.list_positions() or []
    print(f"    Open positions now: {len(after)}", flush=True)
    if after:
        for p in after[:40]:
            print(f"    still open: {getattr(p, 'symbol', p)} qty={getattr(p, 'qty', '?')}", flush=True)
        if len(after) > 40:
            print(f"    … and {len(after) - 40} more", flush=True)
        print(
            "\nWARNING: Not flat yet — common when the market is closed (day orders sit accepted); "
            "re-run after the open or use scripts/repair/alpaca_controlled_liquidation.py for polling + second wave.",
            flush=True,
        )

    print(
        "\nDONE — cancel_all_orders() and close_all_positions() completed without exception "
        "(liquidation commands sent to broker).",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
