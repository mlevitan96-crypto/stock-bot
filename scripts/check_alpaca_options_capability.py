#!/usr/bin/env python3
"""
Read-only diagnostic: verify Alpaca REST auth and options REST endpoints (paper or live per .env).

- GET /v2/account (sanitized summary)
- GET /v2/options/contracts for SPY (proves options data path used by the Wheel)
- Optional: GET /v2/stocks/quotes/latest?symbols=<one OCC> if a contract id is returned

Repo root:
  PYTHONPATH=. python3 scripts/check_alpaca_options_capability.py
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta
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


def _keys() -> tuple[str, str, str]:
    key = (
        os.getenv("ALPACA_API_KEY")
        or os.getenv("ALPACA_KEY")
        or os.getenv("APCA_API_KEY_ID")
        or ""
    ).strip()
    secret = (
        os.getenv("ALPACA_SECRET_KEY")
        or os.getenv("ALPACA_API_SECRET_KEY")
        or os.getenv("ALPACA_SECRET")
        or os.getenv("ALPACA_API_SECRET")
        or ""
    ).strip()
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets").strip().rstrip("/")
    return key, secret, base


def main() -> int:
    try:
        import requests
    except ImportError:
        print("ERROR: requests required", file=sys.stderr)
        return 2

    key, secret, base = _keys()
    if not key or not secret:
        print("ERROR: Missing ALPACA_KEY/ALPACA_SECRET (or APCA_* equivalents) in environment.", file=sys.stderr)
        return 2

    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}

    print("=== Alpaca options capability (read-only) ===")
    print("base_url", base)

    r = requests.get(f"{base}/v2/account", headers=headers, timeout=20)
    print("GET /v2/account", "HTTP", r.status_code)
    if r.status_code != 200:
        print("body_snippet", (r.text or "")[:400])
        return 1
    acct = r.json()
    aid = str(acct.get("id") or "")
    print(
        "account_id_suffix",
        aid[-8:] if len(aid) >= 8 else aid,
        "status",
        acct.get("status"),
        "trading_blocked",
        acct.get("trading_blocked"),
    )
    print("equity", acct.get("equity"), "cash", acct.get("cash"), "multiplier", acct.get("multiplier"))

    today = date.today()
    exp_gte = (today + timedelta(days=5)).isoformat()
    exp_lte = (today + timedelta(days=45)).isoformat()
    params = {
        "underlying_symbols": "SPY",
        "type": "put",
        "expiration_date_gte": exp_gte,
        "expiration_date_lte": exp_lte,
    }
    r2 = requests.get(f"{base}/v2/options/contracts", headers=headers, params=params, timeout=25)
    print("GET /v2/options/contracts (SPY puts)", "HTTP", r2.status_code)
    body = {}
    try:
        body = r2.json() if r2.text else {}
    except Exception:
        body = {}
    if r2.status_code != 200:
        print("options_error_snippet", (r2.text or "")[:500])
        return 1
    contracts = body.get("option_contracts")
    if not isinstance(contracts, list):
        contracts = body if isinstance(body, list) else []
    n = len(contracts)
    print("option_contracts_count", n)
    if n:
        sample = contracts[0]
        sym = sample.get("symbol") or sample.get("id") or ""
        print("sample_contract_symbol", sym[:32] if sym else None)

    # Same client path as wheel: alpaca_trade_api submit_order exists on REST
    try:
        import alpaca_trade_api as tradeapi  # type: ignore

        api = tradeapi.REST(key, secret, base, api_version="v2")
        has_submit = hasattr(api, "submit_order")
        print("tradeapi.REST has submit_order:", has_submit)
        if n and has_submit:
            sym0 = (contracts[0].get("symbol") or contracts[0].get("id") or "").strip()
            if sym0:
                try:
                    from strategies.wheel_strategy import fetch_alpaca_latest_quote, normalize_alpaca_quote

                    rq = fetch_alpaca_latest_quote(api, sym0)
                    nq = normalize_alpaca_quote(rq) or {}
                    print(
                        "wheel fetch quote (OCC_sample) bid/ask",
                        nq.get("bid"),
                        nq.get("ask"),
                    )
                except Exception as e:
                    print("wheel_quote_sample_error", str(e)[:200])
    except Exception as e:
        print("tradeapi_import", str(e)[:200])

    print("=== OK: options REST reachable; Wheel uses this path + api.submit_order ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
