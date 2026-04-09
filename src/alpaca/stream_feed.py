"""
Resolve Alpaca market-data WebSocket feed (sip vs iex) from Trading API account + env.

GET /v2/account is used as the operator-facing source of truth. Field names vary; we read
``data_tier`` when present and scan a few aliases. If absent, the stream manager defaults to
``sip`` and fails over to ``iex`` on auth errors 402/409 (see ``auth_error_triggers_sip_to_iex_failover``).

Credentials are stripped the same way as the WebSocket client (``key.strip()``, ``secret.strip()``).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def strip_alpaca_credentials(api_key: Optional[str], api_secret: Optional[str]) -> Tuple[str, str]:
    return (api_key or "").strip(), (api_secret or "").strip()


def fetch_alpaca_account(
    api_key: str,
    api_secret: str,
    trading_base_url: str,
    *,
    timeout_sec: float = 30.0,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """GET /v2/account (Trading API). Returns (json_dict, error_string)."""
    key, secret = strip_alpaca_credentials(api_key, api_secret)
    if not key or not secret:
        return None, "missing API key or secret (after strip)"
    base = (trading_base_url or "").strip().rstrip("/")
    if not base:
        return None, "missing trading_base_url"
    url = f"{base}/v2/account"
    req = urllib.request.Request(
        url,
        headers={
            "APCA-API-KEY-ID": key,
            "APCA-API-SECRET-KEY": secret,
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body), None
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")[:800]
        except Exception:
            detail = str(e)
        return None, f"HTTP {e.code}: {detail}"
    except Exception as e:
        return None, str(e)


def account_data_tier_label(account: Optional[Dict[str, Any]]) -> Optional[str]:
    """Best-effort ``data_tier`` (or Alpaca alias) from account JSON."""
    if not account:
        return None
    for k in ("data_tier", "market_data_tier", "market_data_subscription", "subscription_tier"):
        v = account.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    for nest_key in ("user_configurations", "admin_configurations"):
        nested = account.get(nest_key)
        if isinstance(nested, dict):
            for k in ("data_tier", "market_data_tier", "market_data_subscription"):
                v = nested.get(k)
                if v is not None and str(v).strip():
                    return str(v).strip()
    return None


def preferred_feed_from_data_tier(tier: Optional[str]) -> Optional[str]:
    """
    Map API tier string to ``sip`` or ``iex`` when unambiguous.
    Returns None if unknown (caller may default to sip + failover).
    """
    if not tier:
        return None
    t = tier.lower().replace(" ", "_").replace("-", "_")
    if t in (
        "premium",
        "professional",
        "pro",
        "unlimited",
        "sip",
        "algo_trader_plus",
        "algotraderplus",
        "paid",
        "enterprise",
    ):
        return "sip"
    if t in ("basic", "free", "iex", "starter", "standard_lite", "lite"):
        return "iex"
    if "premium" in t or "professional" in t or "sip" in t:
        return "sip"
    if "basic" in t or "iex" in t or "free" in t:
        return "iex"
    return None


def resolve_stream_feed(
    api_key: str,
    api_secret: str,
    *,
    trading_base_url: str,
    env_feed_override: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Returns (feed, meta) where feed is ``sip`` or ``iex``.

    Precedence:
    1. ``env_feed_override`` or env ``ALPACA_STREAM_FEED`` if set to sip|iex
    2. Trading API account tier mapping when ``data_tier`` (or alias) is recognized
    3. Default ``sip`` (legacy) — ``AlpacaStreamManager`` fails over to ``iex`` on 402/409
    """
    meta: Dict[str, Any] = {"source": "default_sip_with_iex_failover"}
    ovr = (env_feed_override or os.environ.get("ALPACA_STREAM_FEED") or "").strip().lower()
    if ovr in ("sip", "iex"):
        meta.update({"source": "env", "ALPACA_STREAM_FEED": ovr, "data_tier": None})
        return ovr, meta

    acct, err = fetch_alpaca_account(api_key, api_secret, trading_base_url)
    meta["account_fetch_error"] = err
    if acct is not None:
        meta["account_id"] = acct.get("id")
        tier = account_data_tier_label(acct)
        meta["data_tier"] = tier
        pf = preferred_feed_from_data_tier(tier)
        if pf:
            meta["source"] = "api_data_tier"
            return pf, meta
        meta["data_tier_note"] = (
            "data_tier field missing or unrecognized in /v2/account — using sip with iex failover on auth error"
        )
    else:
        meta["data_tier"] = None
        meta["data_tier_note"] = "account fetch failed — using sip with iex failover on auth error"

    return "sip", meta


def stream_data_ws_url(*, paper: bool, feed: str) -> str:
    feed = (feed or "iex").strip().lower()
    if feed not in ("sip", "iex"):
        feed = "iex"
    host = "stream.data.sandbox.alpaca.markets" if paper else "stream.data.alpaca.markets"
    return f"wss://{host}/v2/{feed}"


def feed_name_from_stream_url(url: str) -> str:
    u = (url or "").rstrip("/").lower()
    if u.endswith("/sip"):
        return "sip"
    if u.endswith("/iex"):
        return "iex"
    return "unknown"


def auth_error_triggers_sip_to_iex_failover(auth_raw: str, *, current_feed: str) -> bool:
    """
    True if WebSocket auth response indicates SIP/subscription rejection and we should retry on iex.
    Alpaca codes: 402 auth failed, 409 insufficient subscription (wrong feed for plan).
    """
    if (current_feed or "").lower() != "sip":
        return False
    try:
        data = json.loads(auth_raw)
    except json.JSONDecodeError:
        return False
    items = data if isinstance(data, list) else [data]
    for o in items:
        if not isinstance(o, dict):
            continue
        if o.get("T") != "error":
            continue
        code = o.get("code")
        try:
            code_i = int(code) if code is not None else None
        except (TypeError, ValueError):
            code_i = None
        msg = str(o.get("msg", "") or "").lower()
        if code_i in (402, 409):
            return True
        if "insufficient subscription" in msg or "not available in your subscription" in msg:
            return True
        if code_i == 402 and "auth" in msg:
            return True
    return False
