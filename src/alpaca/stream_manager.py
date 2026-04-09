"""
Alpaca market-data WebSocket (v2/sip or v2/iex) + thread-safe bar cache.

Spec: https://docs.alpaca.markets/docs/real-time-stock-pricing-data
- URL: built from ``ALPACA_BASE_URL`` (paper vs live) + feed segment; optional ``ALPACA_DATA_STREAM_URL``
  override; host overridable via ``ALPACA_STREAM_DATA_HOST_*`` env vars.
- Auth: {"action":"auth","key":...,"secret":...}
- Subscribe minute aggregates via JSON key "bars" (messages T=="b"); trades via "trades" (T=="t").

Feed selection: ``src.alpaca.stream_feed`` resolves primary/secondary feeds from GET /v2/account
(``data_tier`` when present), env ``ALPACA_STREAM_FEED``, or ``ALPACA_STREAM_FEED_TRY_ORDER``.
On WebSocket auth errors 402/403/409, fail over from primary to alternate feed before giving up.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, List, Optional, Set

import pandas as pd

try:
    import websockets
except ImportError:  # pragma: no cover
    websockets = None  # type: ignore

from src.alpaca.stream_feed import (
    FEED_IEX,
    FEED_SIP,
    alpaca_trading_environment,
    auth_error_allows_feed_failover,
    alternate_market_data_feed,
    feed_name_from_stream_url,
    market_data_stream_host,
    normalize_feed_segment,
    resolve_stream_feed,
    stream_data_ws_url,
    strip_alpaca_credentials,
    swap_stream_url_feed,
)

log = logging.getLogger(__name__)

def _key_id_prefix(key: str) -> str:
    k = (key or "").strip()
    if len(k) >= 8:
        return f"{k[:8]}…"
    if len(k) >= 4:
        return f"{k[:4]}…"
    return "(unset_or_short)"


class _FailoverToAlternateFeed(Exception):
    """Internal: reconnect immediately on alternate feed after primary auth failure."""

_SUBSCRIBE_CHUNK = 40
_MAX_BACKOFF_SEC = 120.0
_INITIAL_BACKOFF_SEC = 1.0

_GLOBAL_MANAGER: Optional["AlpacaStreamManager"] = None
_singleton_lock = threading.Lock()
_symbol_providers: List[Callable[[], List[str]]] = []


def set_stream_manager(m: Optional["AlpacaStreamManager"]) -> None:
    global _GLOBAL_MANAGER
    with _singleton_lock:
        _GLOBAL_MANAGER = m


def get_stream_manager() -> Optional["AlpacaStreamManager"]:
    with _singleton_lock:
        return _GLOBAL_MANAGER


def register_stream_symbol_provider(fn: Callable[[], List[str]]) -> None:
    """Register a callable that returns symbols to subscribe (merged across all engines). Idempotent per function object."""
    with _singleton_lock:
        if fn not in _symbol_providers:
            _symbol_providers.append(fn)


def _merged_symbol_provider() -> List[str]:
    with _singleton_lock:
        providers = list(_symbol_providers)
    syms: Set[str] = set()
    for fn in providers:
        try:
            for s in fn() or []:
                u = str(s).upper().strip()
                if u and u.isalnum():
                    syms.add(u)
        except Exception:
            continue
    if not syms:
        syms.add("SPY")
    try:
        max_s = int(os.environ.get("ALPACA_STREAM_MAX_SYMBOLS", "200"))
    except Exception:
        max_s = 200
    max_s = max(1, min(max_s, 500))
    return sorted(syms)[:max_s]


def ensure_alpaca_stream_manager(
    api_key: str,
    api_secret: str,
    *,
    paper: bool = False,
    url: Optional[str] = None,
    trading_base_url: Optional[str] = None,
    bar_maxlen: int = 400,
) -> Optional["AlpacaStreamManager"]:
    """
    Return the process-wide AlpacaStreamManager, creating and starting it once.
    Multiple StrategyEngine instances must call register_stream_symbol_provider first;
    symbol lists are merged on each subscribe refresh.
    """
    global _GLOBAL_MANAGER
    with _singleton_lock:
        if _GLOBAL_MANAGER is not None:
            return _GLOBAL_MANAGER
        try:
            mgr = AlpacaStreamManager(
                api_key,
                api_secret,
                _merged_symbol_provider,
                paper=paper,
                url=url,
                trading_base_url=trading_base_url,
                bar_maxlen=bar_maxlen,
            )
        except Exception as ex:
            log.warning("AlpacaStreamManager: cannot construct (%s)", ex)
            return None
        _GLOBAL_MANAGER = mgr
    mgr.start()
    return mgr


def _reset_stream_manager_for_tests() -> None:
    """Clear singleton state (unit tests only)."""
    global _GLOBAL_MANAGER
    with _singleton_lock:
        _GLOBAL_MANAGER = None
        _symbol_providers.clear()


@dataclass
class _BarRow:
    """One completed minute bar (SIP)."""

    ts: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float
    trade_count: int
    received_monotonic: float


class PriceCache:
    """
    Thread-safe store: latest OHLCV minute bars per symbol (ring buffer per symbol).
    Also tracks last trade (T) price when trade stream is enabled.
    """

    def __init__(self, maxlen_per_symbol: int = 400) -> None:
        self._lock = threading.RLock()
        self._maxlen = max(32, int(maxlen_per_symbol))
        self._bars: Dict[str, Deque[_BarRow]] = {}
        self._last_bar_rx_mono: Dict[str, float] = {}
        self._last_trade: Dict[str, tuple[float, float]] = {}  # mono, price

    def record_minute_bar(
        self,
        symbol: str,
        *,
        o: float,
        h: float,
        l: float,
        c: float,
        v: float,
        vw: float,
        n: int,
        t_iso: str,
    ) -> None:
        sym = str(symbol).upper().strip()
        if not sym:
            return
        try:
            ts = pd.Timestamp(t_iso)
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            else:
                ts = ts.tz_convert("UTC")
        except Exception:
            return
        row = _BarRow(
            ts=ts,
            open=float(o),
            high=float(h),
            low=float(l),
            close=float(c),
            volume=float(v),
            vwap=float(vw),
            trade_count=int(n),
            received_monotonic=time.monotonic(),
        )
        with self._lock:
            if sym not in self._bars:
                self._bars[sym] = deque(maxlen=self._maxlen)
            dq = self._bars[sym]
            if dq and dq[-1].ts == ts:
                dq[-1] = row
            else:
                dq.append(row)
            self._last_bar_rx_mono[sym] = time.monotonic()

    def record_trade(self, symbol: str, price: float) -> None:
        sym = str(symbol).upper().strip()
        if not sym:
            return
        with self._lock:
            self._last_trade[sym] = (time.monotonic(), float(price))

    def get_fresh_bars_df(
        self,
        symbol: str,
        limit: int,
        *,
        max_age_sec: float = 60.0,
    ) -> Optional[pd.DataFrame]:
        """
        Return last `limit` 1Min bars as a DataFrame (oldest first) if:
        - we have at least `limit` bars, and
        - the most recent bar was received within max_age_sec (wall via monotonic delta).
        """
        sym = str(symbol).upper().strip()
        lim = max(1, int(limit))
        with self._lock:
            dq = self._bars.get(sym)
            if not dq or len(dq) < lim:
                return None
            last_rx = self._last_bar_rx_mono.get(sym)
            if last_rx is None:
                return None
            if (time.monotonic() - last_rx) > float(max_age_sec):
                return None
            rows = list(dq)[-lim:]
        idx = pd.DatetimeIndex([r.ts for r in rows], tz="UTC")
        df = pd.DataFrame(
            {
                "open": [r.open for r in rows],
                "high": [r.high for r in rows],
                "low": [r.low for r in rows],
                "close": [r.close for r in rows],
                "volume": [r.volume for r in rows],
            },
            index=idx,
        )
        return df


class AlpacaStreamManager:
    """
    Background asyncio WebSocket client: market data v2 (sip or iex), auth + subscribe trades + minute bars.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        symbol_provider: Callable[[], List[str]],
        *,
        url: Optional[str] = None,
        paper: bool = False,
        trading_base_url: Optional[str] = None,
        bar_maxlen: int = 400,
    ) -> None:
        if websockets is None:
            raise RuntimeError("websockets package required; pip install websockets")
        self.stream_id = uuid.uuid4().hex[:12]
        self._key, self._secret = strip_alpaca_credentials(api_key, api_secret)
        self._symbol_provider = symbol_provider
        tb = (trading_base_url or os.environ.get("ALPACA_BASE_URL") or "").strip()
        if not tb:
            tb = "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets"
        self._trading_base_url = tb
        env_from_url = alpaca_trading_environment(tb)
        if env_from_url == "paper":
            self._paper = True
        elif env_from_url == "live":
            self._paper = False
        else:
            self._paper = bool(paper)
        if env_from_url in ("paper", "live") and bool(paper) != self._paper:
            log.warning(
                "AlpacaStreamManager: paper=%s disagrees with ALPACA_BASE_URL environment=%s; using URL-derived mode.",
                paper,
                env_from_url,
            )
        self._stream_host, self._environment_label = market_data_stream_host(
            self._trading_base_url,
            paper_fallback=self._paper,
        )
        self._failover_applied = False
        self._logged_iex_auth_dead: bool = False
        self._stream_resolve_meta: Dict[str, Any] = {}
        self._primary_feed: str = FEED_SIP
        self._secondary_feed: Optional[str] = FEED_IEX
        self._explicit_ws_url = False
        explicit_url = (url or os.environ.get("ALPACA_DATA_STREAM_URL") or "").strip()
        if explicit_url:
            self._explicit_ws_url = True
            self._url = explicit_url
            self._feed_name = feed_name_from_stream_url(explicit_url)
            if self._feed_name == "unknown":
                ulow = explicit_url.lower()
                self._feed_name = FEED_SIP if f"/{FEED_SIP}" in ulow else FEED_IEX
            self._primary_feed = normalize_feed_segment(self._feed_name) or self._feed_name
            self._secondary_feed = alternate_market_data_feed(self._primary_feed)
            self._stream_resolve_meta = {
                "source": "ALPACA_DATA_STREAM_URL",
                "trading_environment": env_from_url,
                "stream_data_host": self._stream_host,
                "stream_host_resolution": self._environment_label,
            }
        else:
            primary, secondary, meta = resolve_stream_feed(
                self._key, self._secret, trading_base_url=self._trading_base_url
            )
            self._stream_resolve_meta = dict(meta)
            self._stream_resolve_meta["stream_data_host"] = self._stream_host
            self._stream_resolve_meta["stream_host_resolution"] = self._environment_label
            self._primary_feed = primary
            self._secondary_feed = secondary
            self._feed_name = primary
            self._url = stream_data_ws_url(
                trading_base_url=self._trading_base_url,
                feed=primary,
                paper=self._paper,
            )
        self.price_cache = PriceCache(maxlen_per_symbol=bar_maxlen)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_auth_ok = threading.Event()
        self._last_error: Optional[str] = None

    @property
    def stream_url(self) -> str:
        return self._url

    @property
    def stream_feed(self) -> str:
        return self._feed_name

    @property
    def last_auth_ok(self) -> bool:
        return self._last_auth_ok.is_set()

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def start(self) -> None:
        if not self._key or not self._secret:
            log.warning("AlpacaStreamManager: missing API key/secret; not starting")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._thread_main, name="alpaca-md-ws", daemon=True)
        self._thread.start()
        self._emit_stream_started()

    def _emit_stream_started(self) -> None:
        """Once per physical stream start (singleton); includes stream_id for log correlation."""
        try:
            max_sym = int(os.environ.get("ALPACA_STREAM_MAX_SYMBOLS", "200"))
        except Exception:
            max_sym = 200
        max_sym = max(1, min(max_sym, 500))
        try:
            from utils.system_events import log_system_event

            log_system_event(
                "alpaca_stream",
                "stream_started",
                "INFO",
                stream_id=self.stream_id,
                url=self.stream_url,
                feed=self._feed_name,
                paper=self._paper,
                trading_environment=self._environment_label,
                max_symbols=max_sym,
            )
        except Exception:
            pass
        try:
            from datetime import datetime, timezone
            from pathlib import Path

            p = Path("logs/alpaca_stream.jsonl")
            p.parent.mkdir(parents=True, exist_ok=True)
            rec: Dict[str, Any] = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "msg": "stream_started",
                "stream_id": self.stream_id,
                "url": self.stream_url,
                "feed": self._feed_name,
                "paper": self._paper,
                "trading_environment": self._environment_label,
                "max_symbols": max_sym,
            }
            try:
                from strategies.context import get_strategy_id

                sid = get_strategy_id()
                if sid:
                    rec["strategy_id"] = sid
            except ImportError:
                pass
            with p.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        except Exception:
            pass

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5.0)

    def _thread_main(self) -> None:
        try:
            asyncio.run(self._run_loop())
        except Exception as ex:  # pragma: no cover
            log.exception("AlpacaStreamManager asyncio thread crashed: %s", ex)
            self._last_error = str(ex)

    def _normalize_symbols(self, raw: List[str]) -> List[str]:
        out: Set[str] = set()
        for s in raw or []:
            u = str(s).upper().strip()
            if u and u.isalnum():
                out.add(u)
        if not out:
            out.add("SPY")
        return sorted(out)

    async def _run_loop(self) -> None:
        backoff = _INITIAL_BACKOFF_SEC
        while not self._stop.is_set():
            try:
                async with websockets.connect(
                    self._url,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5,
                    max_size=2**23,
                ) as ws:
                    backoff = _INITIAL_BACKOFF_SEC
                    await self._consume_connection(ws)
            except asyncio.CancelledError:  # pragma: no cover
                break
            except _FailoverToAlternateFeed:
                backoff = _INITIAL_BACKOFF_SEC
                continue
            except Exception as ex:
                self._last_auth_ok.clear()
                self._last_error = str(ex)
                log.warning(
                    "Alpaca %s WebSocket disconnected: %s (reconnect in %.1fs)",
                    self._feed_name.upper(),
                    ex,
                    backoff,
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2.0, _MAX_BACKOFF_SEC)

    async def _consume_connection(self, ws: Any) -> None:
        # First message: connected
        raw0 = await ws.recv()
        self._dispatch_messages(raw0)

        await ws.send(
            json.dumps({"action": "auth", "key": self._key, "secret": self._secret})
        )
        raw1 = await ws.recv()
        if not self._check_auth_success(raw1):
            can_failover = (
                not self._failover_applied
                and self._secondary_feed is not None
                and self._feed_name == self._primary_feed
            )
            if auth_error_allows_feed_failover(raw1, can_try_alternate=can_failover):
                log.warning(
                    "Alpaca market-data WebSocket auth failed on primary feed=%s "
                    "(trading_environment=%s url=%s key_id_prefix=%s raw=%r). "
                    "Failing over to alternate feed=%s.",
                    self._primary_feed,
                    self._environment_label,
                    self._url,
                    _key_id_prefix(self._key),
                    raw1[:400],
                    self._secondary_feed,
                )
                self._failover_applied = True
                self._feed_name = self._secondary_feed or self._feed_name
                if self._explicit_ws_url and self._secondary_feed:
                    self._url = swap_stream_url_feed(self._url, self._secondary_feed)
                else:
                    self._url = stream_data_ws_url(
                        trading_base_url=self._trading_base_url,
                        feed=self._feed_name,
                        paper=self._paper,
                    )
                raise _FailoverToAlternateFeed()
            log.warning(
                "Alpaca market-data WebSocket auth rejected (trading_environment=%s feed=%s url=%s key_id_prefix=%s raw=%r).",
                self._environment_label,
                self._feed_name,
                self._url,
                _key_id_prefix(self._key),
                raw1[:400],
            )
            if self._failover_applied and not self._logged_iex_auth_dead:
                self._logged_iex_auth_dead = True
                log.critical(
                    "Alpaca market-data WebSocket auth failed on alternate feed=%s after primary failover "
                    "(trading_environment=%s url=%s key_id_prefix=%s). "
                    "Verify ALPACA_KEY/ALPACA_SECRET, ALPACA_BASE_URL vs stream host, and market-data streaming entitlement.",
                    self._feed_name,
                    self._environment_label,
                    self._url,
                    _key_id_prefix(self._key),
                )
            raise RuntimeError(f"{self._feed_name.upper()} auth failed: {raw1[:500]!r}")

        self._last_auth_ok.set()
        self._last_error = None

        while not self._stop.is_set():
            syms = self._normalize_symbols(self._symbol_provider())
            for i in range(0, len(syms), _SUBSCRIBE_CHUNK):
                chunk = syms[i : i + _SUBSCRIBE_CHUNK]
                sub = {
                    "action": "subscribe",
                    "trades": chunk,
                    "bars": chunk,
                }
                await ws.send(json.dumps(sub))
                ack = await asyncio.wait_for(ws.recv(), timeout=30.0)
                self._dispatch_messages(ack)

            # Multiplex: read until refresh interval
            refresh_at = time.monotonic() + 120.0
            while time.monotonic() < refresh_at and not self._stop.is_set():
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    self._dispatch_messages(msg)
                except asyncio.TimeoutError:
                    continue

    def _check_auth_success(self, raw: str) -> bool:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return False
        items = data if isinstance(data, list) else [data]
        for o in items:
            if not isinstance(o, dict):
                continue
            if o.get("T") == "success" and "authenticated" in str(o.get("msg", "")).lower():
                return True
            if o.get("T") == "error":
                self._last_error = str(o.get("msg") or o)
                return False
        return False

    def _dispatch_messages(self, raw: str) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return
        items = data if isinstance(data, list) else [data]
        for o in items:
            if not isinstance(o, dict):
                continue
            t = o.get("T")
            if t == "b":
                try:
                    self.price_cache.record_minute_bar(
                        str(o.get("S") or ""),
                        o=float(o.get("o", 0)),
                        h=float(o.get("h", 0)),
                        l=float(o.get("l", 0)),
                        c=float(o.get("c", 0)),
                        v=float(o.get("v", 0)),
                        vw=float(o.get("vw", 0) or 0),
                        n=int(o.get("n", 0) or 0),
                        t_iso=str(o.get("t") or ""),
                    )
                except Exception:
                    pass
            elif t == "u":
                # updatedBars — same schema as minute bar
                try:
                    self.price_cache.record_minute_bar(
                        str(o.get("S") or ""),
                        o=float(o.get("o", 0)),
                        h=float(o.get("h", 0)),
                        l=float(o.get("l", 0)),
                        c=float(o.get("c", 0)),
                        v=float(o.get("v", 0)),
                        vw=float(o.get("vw", 0) or 0),
                        n=int(o.get("n", 0) or 0),
                        t_iso=str(o.get("t") or ""),
                    )
                except Exception:
                    pass
            elif t == "t":
                try:
                    self.price_cache.record_trade(str(o.get("S") or ""), float(o.get("p", 0)))
                except Exception:
                    pass
