#!/usr/bin/env python3
"""
Unusual Whales WebSocket consumer (Sniper flow-alerts).

Protocol (from UW OpenAPI / socket docs):
  URI: ``wss://api.unusualwhales.com/socket`` (token may be query **or** RFC6455 header)
  Join: ``{"channel":"flow-alerts","msg_type":"join"}``
  Frames: JSON array ``[channel_name, payload]``

**Auth (401 mitigation):** Some keys reject ``?token=`` on the WebSocket upgrade. Default
``UW_WS_AUTH_MODE=bearer`` sends **only** ``Authorization: Bearer <UW_API_KEY>`` and a clean URL.
Set ``UW_WS_AUTH_MODE=query`` for legacy URL token, or ``both`` to send both.

Requires: ``websockets`` (repo pins ``<11``; supports ``additional_headers`` on recent 10.x / 11+).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)

_DEFAULT_WS_BASE = "wss://api.unusualwhales.com/socket"


def uw_ws_connect_config(api_token: str) -> Tuple[str, Optional[List[Tuple[str, str]]]]:
    """
    Returns ``(uri, additional_headers)`` for ``websockets.connect``.

    ``additional_headers`` is a list of (name, value) pairs for the HTTP upgrade request.
    """
    mode = os.getenv("UW_WS_AUTH_MODE", "bearer").strip().lower()
    base = (os.getenv("UW_WS_BASE", _DEFAULT_WS_BASE) or _DEFAULT_WS_BASE).strip()
    if "token=" in base.lower():
        base = base.split("?")[0].rstrip("?&")
    tok = str(api_token or "").strip()
    from urllib.parse import quote

    qt = quote(tok, safe="")
    sep = "&" if "?" in base else "?"
    if mode in ("query", "url", "legacy"):
        return f"{base}{sep}token={qt}", None
    if mode in ("both", "dual"):
        return f"{base}{sep}token={qt}", [("Authorization", f"Bearer {tok}")]
    # bearer-only (default)
    return base, [("Authorization", f"Bearer {tok}")]


def extract_flow_symbol(payload: Any) -> Optional[str]:
    """Best-effort underlying / issue symbol from a flow-alerts payload."""
    if not isinstance(payload, dict):
        return None
    for k in (
        "ticker",
        "symbol",
        "underlying",
        "underlying_symbol",
        "underlyingSymbol",
        "issue_symbol",
        "issue",
    ):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip().upper().split()[0]
    return None


async def _flow_alerts_recv_loop(
    ws: Any,
    sniper: Set[str],
    on_alert: Callable[[str, Dict[str, Any]], None],
    stop: asyncio.Event,
    reconnect_min: float,
) -> None:
    await ws.send(json.dumps({"channel": "flow-alerts", "msg_type": "join"}))
    while not stop.is_set():
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=120.0)
        except asyncio.TimeoutError:
            continue
        try:
            msg = json.loads(raw)
        except Exception:
            continue
        if not isinstance(msg, list) or len(msg) < 2:
            continue
        ch, data = msg[0], msg[1]
        if ch != "flow-alerts":
            continue
        if isinstance(data, dict) and str(data.get("status", "")).lower() == "ok":
            print("[UW-WS] flow-alerts join ok (server ack)", flush=True)
            continue
        sym = extract_flow_symbol(data)
        if sym and sym in sniper and isinstance(data, dict):
            try:
                on_alert(sym, data)
            except Exception as ex:
                log.warning("uw_flow_ws on_alert failed: %s", ex)


async def _consume_flow_alerts(
    api_token: str,
    sniper: Set[str],
    on_alert: Callable[[str, Dict[str, Any]], None],
    stop: asyncio.Event,
    *,
    reconnect_min: float = 2.0,
    reconnect_max: float = 120.0,
) -> None:
    import websockets

    backoff = reconnect_min
    while not stop.is_set():
        uri, hdr_list = uw_ws_connect_config(api_token)
        hdr_dict = dict(hdr_list) if hdr_list else None
        kw = dict(ping_interval=20, ping_timeout=60, close_timeout=10, max_size=8_000_000)
        try:
            if hdr_dict:
                try:
                    async with websockets.connect(uri, additional_headers=hdr_dict, **kw) as ws:
                        await _flow_alerts_recv_loop(ws, sniper, on_alert, stop, reconnect_min)
                except TypeError:
                    async with websockets.connect(uri, extra_headers=hdr_dict, **kw) as ws:
                        await _flow_alerts_recv_loop(ws, sniper, on_alert, stop, reconnect_min)
            else:
                async with websockets.connect(uri, **kw) as ws:
                    await _flow_alerts_recv_loop(ws, sniper, on_alert, stop, reconnect_min)
            backoff = reconnect_min
        except asyncio.CancelledError:
            break
        except Exception as ex:
            log.warning("uw_flow_ws connection error: %s (reconnect in %.1fs)", ex, backoff)
            await asyncio.sleep(min(backoff, reconnect_max))
            backoff = min(backoff * 2, reconnect_max)


def run_ws_loop_in_thread(
    api_token: str,
    sniper: Set[str],
    on_alert: Callable[[str, Dict[str, Any]], None],
    stop_event: threading.Event,
) -> threading.Thread:
    """Start asyncio WS loop on a daemon thread. Stop via ``stop_event``."""

    def _runner() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        a_stop = asyncio.Event()

        def _bridge_stop() -> None:
            while not stop_event.is_set():
                time.sleep(0.25)
            loop.call_soon_threadsafe(a_stop.set)

        watcher = threading.Thread(target=_bridge_stop, daemon=True)
        watcher.start()
        try:
            loop.run_until_complete(_consume_flow_alerts(api_token, sniper, on_alert, a_stop))
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for t in pending:
                    t.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            loop.close()

    t = threading.Thread(target=_runner, name="uw-flow-ws", daemon=True)
    t.start()
    return t


def _build_uri(api_token: str) -> str:
    """Always query-token URL (tests / legacy); live connect uses ``uw_ws_connect_config``."""
    from urllib.parse import quote

    base = (os.getenv("UW_WS_BASE", _DEFAULT_WS_BASE) or _DEFAULT_WS_BASE).strip()
    if "token=" in base.lower():
        base = base.split("?")[0].rstrip("?&")
    tok = quote(str(api_token or "").strip(), safe="")
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}token={tok}"
