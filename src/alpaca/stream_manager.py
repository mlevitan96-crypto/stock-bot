"""
Alpaca consolidated SIP WebSocket (v2/sip) + thread-safe bar cache.

Spec: https://docs.alpaca.markets/docs/real-time-stock-pricing-data
- URL: wss://stream.data.alpaca.markets/v2/sip (production)
- Auth: {"action":"auth","key":...,"secret":...}
- Subscribe minute aggregates via JSON key "bars" (messages T=="b"); trades via "trades" (T=="t").

AM (aggregate minute) in legacy naming maps to the "bars" channel / bar schema (T=="b").
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, List, Optional, Set

import pandas as pd

try:
    import websockets
except ImportError:  # pragma: no cover
    websockets = None  # type: ignore

log = logging.getLogger(__name__)

_DEFAULT_PROD_URL = "wss://stream.data.alpaca.markets/v2/sip"
_DEFAULT_SANDBOX_URL = "wss://stream.data.sandbox.alpaca.markets/v2/sip"
_SUBSCRIBE_CHUNK = 40
_MAX_BACKOFF_SEC = 120.0
_INITIAL_BACKOFF_SEC = 1.0

_GLOBAL_MANAGER: Optional["AlpacaStreamManager"] = None


def set_stream_manager(m: Optional["AlpacaStreamManager"]) -> None:
    global _GLOBAL_MANAGER
    _GLOBAL_MANAGER = m


def get_stream_manager() -> Optional["AlpacaStreamManager"]:
    return _GLOBAL_MANAGER


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
    Background asyncio WebSocket client: SIP v2, auth + subscribe trades + minute bars.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        symbol_provider: Callable[[], List[str]],
        *,
        url: Optional[str] = None,
        paper: bool = False,
        bar_maxlen: int = 400,
    ) -> None:
        if websockets is None:
            raise RuntimeError("websockets package required; pip install websockets")
        self._key = (api_key or "").strip()
        self._secret = (api_secret or "").strip()
        self._symbol_provider = symbol_provider
        self._url = (url or "").strip() or (_DEFAULT_SANDBOX_URL if paper else _DEFAULT_PROD_URL)
        self.price_cache = PriceCache(maxlen_per_symbol=bar_maxlen)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_auth_ok = threading.Event()
        self._last_error: Optional[str] = None

    @property
    def stream_url(self) -> str:
        return self._url

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
        self._thread = threading.Thread(target=self._thread_main, name="alpaca-sip-ws", daemon=True)
        self._thread.start()

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
            except Exception as ex:
                self._last_auth_ok.clear()
                self._last_error = str(ex)
                log.warning("Alpaca SIP WebSocket disconnected: %s (reconnect in %.1fs)", ex, backoff)
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
            raise RuntimeError(f"SIP auth failed: {raw1[:500]!r}")

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
