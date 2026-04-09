#!/usr/bin/env python3
"""
Temporary diagnostic: Trading API GET /v2/account — report market-data tier / feed hints.

Usage (repo root):
  python3 scripts/diag/check_alpaca_tier.py
  python3 scripts/diag/check_alpaca_tier.py --json

Reads the same env vars as the bot: ALPACA_KEY / ALPACA_SECRET (or ALPACA_API_KEY aliases),
ALPACA_BASE_URL (paper-api vs live).

Note: Alpaca's published OpenAPI schema for Account does not always list ``data_tier``; this
script prints it when the API returns it, and prints all keys containing tier/subscription/sip/data.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from dotenv import load_dotenv

    load_dotenv(REPO / ".env")
except Exception:
    pass


def _pick_credentials() -> tuple[str, str]:
    key = (
        os.environ.get("ALPACA_KEY")
        or os.environ.get("ALPACA_API_KEY")
        or os.environ.get("APCA_API_KEY_ID")
        or ""
    )
    secret = (
        os.environ.get("ALPACA_SECRET")
        or os.environ.get("ALPACA_API_SECRET")
        or os.environ.get("APCA_API_SECRET_KEY")
        or ""
    )
    return key.strip(), secret.strip()


def _whitespace_audit(names: tuple[str, ...]) -> None:
    print("--- credential whitespace audit (same strip() as REST/WS clients) ---")
    for name in names:
        raw = os.environ.get(name)
        if raw is None:
            print(f"  {name}: <unset>")
            continue
        if raw != raw.strip():
            print(f"  WARNING {name}: leading/trailing whitespace (len raw={len(raw)!r})")
        if "\n" in raw or "\r" in raw:
            print(f"  WARNING {name}: contains CR/LF")
        print(f"  {name}: len={len(raw)} first_char={raw[:1]!r} last_char={raw[-1:]!r}")


def _interesting_keys(obj: dict, prefix: str = "") -> None:
    pat = re.compile(r"tier|subscription|sip|data|market", re.I)
    for k, v in sorted(obj.items()):
        full = f"{prefix}{k}"
        if pat.search(full):
            disp = v
            if isinstance(disp, (dict, list)):
                disp = json.dumps(disp, default=str)[:500]
            print(f"  {full}: {disp}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Print Alpaca account market-data tier from GET /v2/account")
    ap.add_argument("--json", action="store_true", help="Print full account JSON (pretty)")
    ap.add_argument("--no-whitespace-audit", action="store_true")
    args = ap.parse_args()

    from src.alpaca.stream_feed import (
        account_data_tier_label,
        fetch_alpaca_account,
        preferred_feed_from_data_tier,
        resolve_stream_feed,
    )

    key, secret = _pick_credentials()
    base = (os.environ.get("ALPACA_BASE_URL") or os.environ.get("APCA_API_BASE_URL") or "").strip()
    if not base:
        base = "https://paper-api.alpaca.markets"

    if not args.no_whitespace_audit:
        _whitespace_audit(
            (
                "ALPACA_KEY",
                "ALPACA_SECRET",
                "ALPACA_API_KEY",
                "ALPACA_API_SECRET",
                "APCA_API_KEY_ID",
                "APCA_API_SECRET_KEY",
            )
        )
        print()

    print(f"Trading API base URL: {base}")
    if not key or not secret:
        print("ERROR: Missing ALPACA_KEY/ALPACA_SECRET (after strip).")
        return 2

    acct, err = fetch_alpaca_account(key, secret, base)
    if err:
        print(f"GET /v2/account failed: {err}")
        return 1
    assert acct is not None

    if args.json:
        print(json.dumps(acct, indent=2, default=str))
        return 0

    tier = account_data_tier_label(acct)
    print("--- data_tier (canonical field when present) ---")
    raw_dt = acct.get("data_tier")
    print(f"  account['data_tier'] = {raw_dt!r}")
    print(f"  resolved label (aliases scanned): {tier!r}")

    pf = preferred_feed_from_data_tier(tier)
    print("--- mapped WebSocket feed (inferred) ---")
    if pf:
        print(f"  preferred_feed_from_data_tier -> {pf!r} (basic~iex / premium~sip heuristic)")
    else:
        print("  preferred_feed_from_data_tier -> None (unknown tier string; bot defaults sip+iex failover)")

    feed, meta = resolve_stream_feed(key, secret, trading_base_url=base)
    print("--- resolve_stream_feed (env ALPACA_STREAM_FEED overrides tier) ---")
    print(f"  chosen feed: {feed!r}")
    print(f"  meta: {json.dumps(meta, default=str)}")

    print("--- account keys matching tier|subscription|sip|data|market ---")
    _interesting_keys(acct)
    for nk in ("user_configurations", "admin_configurations"):
        nested = acct.get(nk)
        if isinstance(nested, dict):
            _interesting_keys(nested, prefix=f"{nk}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
