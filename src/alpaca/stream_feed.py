"""
Resolve Alpaca market-data WebSocket feed and host from Trading API base URL + account tier.

- **Host** is derived from ``ALPACA_BASE_URL`` (paper-api → sandbox stream host, api.alpaca.markets → live).
  Override with ``ALPACA_STREAM_DATA_HOST_SANDBOX``, ``ALPACA_STREAM_DATA_HOST_LIVE``, or
  ``ALPACA_STREAM_DATA_HOST`` when the base URL is non-standard.
- **Feed** path segment (Alpaca wire names) comes from ``GET /v2/account`` tier when present,
  else ``ALPACA_STREAM_FEED`` or ``ALPACA_STREAM_FEED_TRY_ORDER`` (comma-separated).

``AlpacaStreamManager`` fails over to the alternate feed on WebSocket auth errors 402/403/409 when
the first feed in the pair fails (subscription / auth).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

# Alpaca Market Data WebSocket v2 path segments (broker API contract).
FEED_SIP = "sip"
FEED_IEX = "iex"


def strip_alpaca_credentials(api_key: Optional[str], api_secret: Optional[str]) -> Tuple[str, str]:
    return (api_key or "").strip(), (api_secret or "").strip()


def normalize_feed_segment(name: Optional[str]) -> Optional[str]:
    n = (name or "").strip().lower()
    if n in (FEED_SIP, FEED_IEX):
        return n
    return None


def alternate_market_data_feed(feed: str) -> Optional[str]:
    f = normalize_feed_segment(feed)
    if f == FEED_SIP:
        return FEED_IEX
    if f == FEED_IEX:
        return FEED_SIP
    return None


def alpaca_trading_environment(trading_base_url: str) -> str:
    """
    Classify trading REST base URL as paper vs live (for stream host selection).
    Returns one of: paper, live, unknown.
    """
    tu = (trading_base_url or "").strip().lower()
    if not tu:
        return "unknown"
    try:
        host = (urlparse(tu).hostname or "").lower()
    except Exception:
        host = ""
    if not host:
        return "unknown"
    if host == "paper-api.alpaca.markets" or host.startswith("paper-api."):
        return "paper"
    if host == "api.alpaca.markets":
        return "live"
    return "unknown"


def market_data_stream_host(
    trading_base_url: str,
    *,
    paper_fallback: bool = False,
) -> Tuple[str, str]:
    """
    Returns (websocket_hostname, environment_label).

    Host defaults are Alpaca's documented endpoints; override via env without code changes:
    ``ALPACA_STREAM_DATA_HOST_SANDBOX``, ``ALPACA_STREAM_DATA_HOST_LIVE``, ``ALPACA_STREAM_DATA_HOST``.
    """
    env_label = alpaca_trading_environment(trading_base_url)
    sandbox_host = (os.environ.get("ALPACA_STREAM_DATA_HOST_SANDBOX") or "stream.data.sandbox.alpaca.markets").strip()
    live_host = (os.environ.get("ALPACA_STREAM_DATA_HOST_LIVE") or "stream.data.alpaca.markets").strip()
    explicit = (os.environ.get("ALPACA_STREAM_DATA_HOST") or "").strip()

    if env_label == "paper":
        return sandbox_host, "paper"
    if env_label == "live":
        return live_host, "live"
    if explicit:
        return explicit, "custom_host_env"
    if paper_fallback:
        return sandbox_host, "paper_fallback"
    return live_host, "live_fallback"


def stream_data_ws_url(
    *,
    feed: str,
    trading_base_url: Optional[str] = None,
    paper: bool = False,
) -> str:
    """
    Build ``wss://<host>/v2/<feed>``.

    If ``trading_base_url`` is non-empty, host is inferred from it (preferred).
    Otherwise ``paper`` selects sandbox vs live host (legacy).
    """
    seg = normalize_feed_segment(feed) or FEED_IEX
    tb = (trading_base_url or "").strip()
    if tb:
        host, _ = market_data_stream_host(tb, paper_fallback=paper)
    else:
        sandbox_host = (os.environ.get("ALPACA_STREAM_DATA_HOST_SANDBOX") or "stream.data.sandbox.alpaca.markets").strip()
        live_host = (os.environ.get("ALPACA_STREAM_DATA_HOST_LIVE") or "stream.data.alpaca.markets").strip()
        host = sandbox_host if paper else live_host
    return f"wss://{host}/v2/{seg}"


def swap_stream_url_feed(url: str, new_feed: str) -> str:
    """Same host and /v2/ prefix; replace final path segment (for failover when URL was explicit)."""
    seg = normalize_feed_segment(new_feed) or new_feed.strip().lower()
    u = (url or "").strip().rstrip("/")
    if "/v2/" in u:
        return u.rsplit("/", 1)[0] + f"/{seg}"
    return f"{u}/v2/{seg}"


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
    Returns None if unknown (caller uses try-order).
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
        return FEED_SIP
    if t in ("basic", "free", "iex", "starter", "standard_lite", "lite"):
        return FEED_IEX
    if "premium" in t or "professional" in t or "sip" in t:
        return FEED_SIP
    if "basic" in t or "iex" in t or "free" in t:
        return FEED_IEX
    return None


def _feeds_from_try_order_string(order_str: str) -> Tuple[str, str]:
    parts = [normalize_feed_segment(p) for p in order_str.split(",")]
    seen: list[str] = []
    for p in parts:
        if p and p not in seen:
            seen.append(p)
    if len(seen) >= 2:
        return seen[0], seen[1]
    if len(seen) == 1:
        alt = alternate_market_data_feed(seen[0])
        if alt:
            return seen[0], alt
    return FEED_SIP, FEED_IEX


def resolve_stream_feed(
    api_key: str,
    api_secret: str,
    *,
    trading_base_url: str,
    env_feed_override: Optional[str] = None,
) -> Tuple[str, Optional[str], Dict[str, Any]]:
    """
    Returns (primary_feed, secondary_feed, meta).

    Precedence:
    1. ``env_feed_override`` or env ``ALPACA_STREAM_FEED`` if set to a single known feed → alternate is the other feed
    2. Trading API ``data_tier`` (or alias) when it maps to a feed → alternate is the other feed
    3. Env ``ALPACA_STREAM_FEED_TRY_ORDER`` (comma-separated, default ``sip,iex``)
    """
    meta: Dict[str, Any] = {"source": "try_order"}
    meta["trading_environment"] = alpaca_trading_environment(trading_base_url)

    ovr = (env_feed_override or os.environ.get("ALPACA_STREAM_FEED") or "").strip().lower()
    single = normalize_feed_segment(ovr)
    if single:
        alt = alternate_market_data_feed(single)
        meta.update({"source": "env", "ALPACA_STREAM_FEED": single, "data_tier": None})
        return single, alt, meta

    acct, err = fetch_alpaca_account(api_key, api_secret, trading_base_url)
    meta["account_fetch_error"] = err
    if acct is not None:
        meta["account_id"] = acct.get("id")
        tier = account_data_tier_label(acct)
        meta["data_tier"] = tier
        pf = preferred_feed_from_data_tier(tier)
        if pf:
            alt = alternate_market_data_feed(pf)
            meta["source"] = "api_data_tier"
            return pf, alt, meta
        meta["data_tier_note"] = (
            "data_tier missing or unrecognized in /v2/account — using ALPACA_STREAM_FEED_TRY_ORDER"
        )
    else:
        meta["data_tier"] = None
        meta["data_tier_note"] = "account fetch failed — using ALPACA_STREAM_FEED_TRY_ORDER"

    try_order = (os.environ.get("ALPACA_STREAM_FEED_TRY_ORDER") or f"{FEED_SIP},{FEED_IEX}").strip()
    meta["ALPACA_STREAM_FEED_TRY_ORDER"] = try_order
    a, b = _feeds_from_try_order_string(try_order)
    return a, b, meta


def feed_name_from_stream_url(url: str) -> str:
    u = (url or "").rstrip("/").lower()
    if u.endswith(f"/{FEED_SIP}"):
        return FEED_SIP
    if u.endswith(f"/{FEED_IEX}"):
        return FEED_IEX
    return "unknown"


def auth_error_allows_feed_failover(auth_raw: str, *, can_try_alternate: bool) -> bool:
    """
    True if WebSocket auth response indicates auth/subscription rejection and an alternate feed may help.
    Alpaca: 402 auth failed, 403 forbidden, 409 insufficient subscription.
    """
    if not can_try_alternate:
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
        if code_i in (402, 403, 409):
            return True
        if "insufficient subscription" in msg or "not available in your subscription" in msg:
            return True
        if code_i in (402, 403) and "auth" in msg:
            return True
    return False


def auth_error_triggers_sip_to_iex_failover(auth_raw: str, *, current_feed: str) -> bool:
    """Backward-compatible: SIP-only failover check (tests)."""
    return auth_error_allows_feed_failover(
        auth_raw,
        can_try_alternate=(normalize_feed_segment(current_feed) == FEED_SIP),
    )
