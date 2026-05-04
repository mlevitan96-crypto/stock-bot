#!/usr/bin/env python3
"""
Temporary diagnostic: compare Alpaca methods for OCC option NBBO.

Tries, in order:
1) tradeapi.REST.get_latest_quote(OCC)  [often empty for options — wrong API surface]
2) tradeapi.REST.get_quote(OCC) if present
3) Market Data REST GET /v1beta1/options/quotes/latest (opra, then indicative)

Repo root:
  PYTHONPATH=. python scripts/diagnostic_options_pricing.py
  PYTHONPATH=. python scripts/diagnostic_options_pricing.py --occ SPY260515P00500000
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

for path in (REPO / ".env", Path.home() / ".alpaca_env"):
    if not path.is_file():
        continue
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(path, override=False)
    except Exception:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def _pick_occ_from_contracts() -> str:
    import requests

    key = (os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY") or "").strip()
    secret = (os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_SECRET") or "").strip()
    base = (os.getenv("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets").rstrip("/")
    if not key or not secret:
        return ""
    from datetime import date, timedelta

    today = date.today()
    exp_gte = (today + timedelta(days=5)).isoformat()
    exp_lte = (today + timedelta(days=45)).isoformat()
    r = requests.get(
        f"{base}/v2/options/contracts",
        headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret},
        params={"underlying_symbols": "SPY", "type": "put", "expiration_date_gte": exp_gte, "expiration_date_lte": exp_lte},
        timeout=25,
    )
    if r.status_code != 200:
        print("contracts HTTP", r.status_code, (r.text or "")[:200])
        return ""
    body = r.json() if r.text else {}
    rows = body.get("option_contracts") or (body if isinstance(body, list) else [])
    if not isinstance(rows, list) or not rows:
        return ""
    c0 = rows[0]
    return str(c0.get("symbol") or c0.get("id") or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--occ", default="", help="Explicit OCC symbol; else pick from SPY puts via contracts API")
    args = ap.parse_args()

    key = (os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY") or "").strip()
    secret = (os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_SECRET") or "").strip()
    base = (os.getenv("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets").rstrip("/")
    data_base = (os.getenv("ALPACA_DATA_BASE_URL") or "https://data.alpaca.markets").rstrip("/")

    occ = (args.occ or "").strip() or _pick_occ_from_contracts()
    if not occ:
        print("ERROR: no OCC symbol (set --occ or fix contracts API)", file=sys.stderr)
        return 2
    print("=== diagnostic_options_pricing ===")
    print("OCC:", occ)
    print("ALPACA_BASE_URL:", base)
    print("ALPACA_DATA_BASE_URL:", data_base)

    # 1) Trading REST get_latest_quote
    try:
        import alpaca_trade_api as tradeapi  # type: ignore

        api = tradeapi.REST(key, secret, base, api_version="v2")
        fn = getattr(api, "get_latest_quote", None)
        if callable(fn):
            q = fn(occ)
            print("\n[1] get_latest_quote(OCC):", repr(q))
        else:
            print("\n[1] get_latest_quote: NOT AVAILABLE on REST client")
    except Exception as e:
        print("\n[1] get_latest_quote ERROR:", e)

    # 2) Legacy get_quote
    try:
        import alpaca_trade_api as tradeapi  # type: ignore

        api = tradeapi.REST(key, secret, base, api_version="v2")
        gq = getattr(api, "get_quote", None)
        if callable(gq):
            print("[2] get_quote(OCC):", repr(gq(occ)))
        else:
            print("[2] get_quote: NOT AVAILABLE")
    except Exception as e:
        print("[2] get_quote ERROR:", e)

    # 3) Market Data option latest quotes
    try:
        import requests

        url = f"{data_base}/v1beta1/options/quotes/latest"
        headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
        for feed in ("opra", "indicative"):
            r = requests.get(url, params={"symbols": occ, "feed": feed}, headers=headers, timeout=25)
            print(f"\n[3] Data API quotes/latest feed={feed} HTTP {r.status_code}")
            if r.status_code == 200 and r.text:
                j = r.json()
                q = (j.get("quotes") or {}).get(occ)
                print("    quote:", json.dumps(q, default=str)[:500] if q else "(no quote key)")
                if isinstance(q, dict) and (q.get("bp") is not None or q.get("ap") is not None):
                    print("\n>>> SUCCESS: use Market Data GET /v1beta1/options/quotes/latest with feed=", feed)
                    return 0
            else:
                print("    body snippet:", (r.text or "")[:200])
    except Exception as e:
        print("[3] Data API ERROR:", e)

    # 4) Repo helper (post-fix path)
    try:
        from strategies.wheel_strategy import fetch_alpaca_latest_quote

        import alpaca_trade_api as tradeapi  # type: ignore

        api = tradeapi.REST(key, secret, base, api_version="v2")
        hq = fetch_alpaca_latest_quote(api, occ)
        print("\n[4] fetch_alpaca_latest_quote(api, OCC):", repr(hq))
    except Exception as e:
        print("\n[4] fetch_alpaca_latest_quote ERROR:", e)

    print("\n>>> No method returned a usable bid/ask in this run.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
